import json
import logging
from importlib import import_module
from requests_oauthlib.oauth1_session import TokenRequestDenied

from bot.commands import help_command
from bot.commands import start_command
from bot.commands import switch_mode
from bot.commands import switch_mode_command
from bot.commands import switch_notebook
from bot.commands import switch_notebook_command
from bot.handlers.text import handle_text
from bot.handlers.photo import handle_photo
from bot.handlers.audio import handle_audio
from bot.handlers.location import handle_location
from bot.models import User
from data.storage.storage import StorageMixin
from telegram.bot_api import BotApi
from util.evernote.client import EvernoteClient


class EvernoteBot(StorageMixin):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        telegram_token = config['telegram']['token']
        self.api = BotApi(telegram_token)
        self.url = config['telegram']['bot_url']
        self.evernote = EvernoteClient(sandbox=config.get('debug', True))

    def get_user(self, telegram_message):
        user_id = telegram_message.from_user.id
        return self.get_storage(User).get(user_id)

    def handle_telegram_update(self, telegram_update):
        try:
            command_name = telegram_update.get_command()
            if command_name:
                self.execute_command(command_name, telegram_update)
                return
            message = telegram_update.message or telegram_update.edited_message
            if message:
                self.handle_message(message)
            post = telegram_update.channel_post or telegram_update.edited_channel_post
            if post:
                self.handle_post(post)
        except Exception as e:
            chat_id = telegram_update.message.chat.id
            error_message = '\u274c Error. {0}'.format(e)
            self.api.sendMessage(chat_id, error_message)
            logging.getLogger().error(e, exc_info=1)

    def execute_command(self, name, telegram_update):
        message = telegram_update.message
        if name == 'help':
            return help_command(self, message.chat.id)
        elif name == 'start':
            return start_command(self, message)
        elif name == 'switch_mode':
            return switch_mode_command(self, message)
        elif name == 'notebook':
            return switch_notebook_command(self, message)
        else:
            raise Exception('Unknown command "{}"'.format(name))

    def handle_message(self, message):
        user = self.get_user(message)
        if not user:
            raise Exception('Unregistered user {0}. {1}'.format(user.id, self.get_storage(User).get_all({})))
        status_message = self.api.sendMessage(message.chat.id, 'Accepted')
        if message.text:
            handle_text(self, message)
        if message.photo:
            handle_photo(self, message)
        if message.audio:
            handle_audio(self, message)
        if message.location:
            handle_location(self, message)
        self.api.editMessageText(message.chat.id, status_message['message_id'], 'Saved')

    def handle_post(self, post):
        # TODO:
        pass

    def handle_state(self, state_label, message):
        user = self.get_user(message)
        if state_label == 'switch_mode':
            switch_mode(self, message)
        elif state_label == 'switch_notebook':
            switch_notebook(self, message)
        else:
            logging.getLogger().warning('Invalid state: {}'.format(state_label))
        user.state = None
        user.save()
        self.api.sendMessage(user.telegram.chat_id, 'Done.', json.dumps({'hide_keyboard': True}))

    def oauth_callback(self, callback_key, oauth_verifier, access_type):
        user = self.get_storage(User).get({'evernote.oauth.callback_key': callback_key})
        if not user:
            raise Exception('User not found. callback_key = {}'.format(callback_key))
        if not oauth_verifier:
            text = 'We are sorry, but you have declined authorization.'
            self.api.sendMessage(user.telegram.chat_id, text)
            return
        chat_id = user.telegram.chat_id
        evernote_config = self.config['evernote']['access'][access_type]
        try:
            oauth = user.evernote.oauth
            user.evernote.access_token = self.evernote.get_access_token(
                evernote_config['key'],
                evernote_config['secret'],
                oauth.token,
                oauth.secret,
                oauth_verifier
            )
            user.save()
        except TokenRequestDenied as e:
            logging.getLogger().error(e, exc_info=1)
            text = 'We are sorry, but we have some problems with Evernote connection. Please try again later.'
            self.api.sendMessage(chat_id, text)
            return
        except Exception as e:
            logging.getLogger().error(e, exc_info=1)
            self.api.sendMessage(chat_id, 'Unknown error. Please, try again later.')
            return
        text = 'Evernote account is connected.\nFrom now you can just send a message and a note will be created.'
        self.api.sendMessage(chat_id, text)
        default_notebook = self.evernote.get_default_notebook(user.evernote.access_token)
        user.evernote.notebook.from_dict(default_notebook)
        user.save()
        mode = user.bot_mode.replace('_', ' ').capitalize()
        text = 'Current notebook: {0}\nCurrent mode: {1}'.format(user.evernote.notebook.name, mode)
        self.api.sendMessage(chat_id, text)

    def save_note(self, user, text=None, title=None, html=None, files=None):
        if user.bot_mode == 'one_note':
            self.evernote.update_note(
                user.evernote.access_token,
                user.evernote.shared_note_id,
                text=text,
                html=html,
                title=title,
                files=files
            )
        else:
            self.evernote.create_note(
                user.evernote.access_token,
                user.evernote.notebook.guid,
                text=text,
                html=html,
                title=title,
                files=files
            )
