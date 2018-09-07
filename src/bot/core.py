import json
import logging
from importlib import import_module
from requests_oauthlib.oauth1_session import TokenRequestDenied

from bot.commands import help_command
from bot.commands import oauth
from bot.commands import start_command
from bot.commands import switch_mode_command
from bot.commands import switch_notebook_command
from bot.handlers.text import handle_text
from bot.handlers.photo import handle_photo
from bot.handlers.audio import handle_audio
from bot.handlers.video import handle_video
from bot.handlers.document import handle_document
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
            return help_command(self, message)
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
            user_id = message.from_user.id
            raise Exception('Unregistered user {0}. You\'ve to send /start command to register'.format(user_id))
        if user.state:
            self.handle_state(user.state, message)
            return
        if message.text:
            handle_text(self, message)
        if message.photo:
            handle_photo(self, message)
        if message.voice:
            handle_audio(self, message)
        if message.video:
            handle_video(self, message)
        if message.document:
            handle_document(self, message)
        if message.location:
            handle_location(self, message)

    def handle_post(self, post):
        # TODO:
        pass

    def handle_state(self, state_label, message):
        user = self.get_user(message)
        if state_label == 'switch_mode':
            mode = message.text.lower()
            if mode.startswith('> ') and mode.endswith(' <'):
                mode = mode[2:-2]
            mode = mode.replace(' ', '_')
            if mode not in ('one_note', 'multiple_notes'):
                logging.getLogger().warning('Invalid mode {}'.format(mode))
                self.api.sendMessage(user.telegram.chat_id, 'Unknown mode "{}"'.format(mode))
                return
            self.switch_mode(user, mode)
            user.save()
        elif state_label == 'switch_notebook':
            name = message.text
            if name.startswith('> ') and name.endswith(' <'):
                name = name[2:-2]
            self.switch_notebook(user, name)
            user.save()
        else:
            logging.getLogger().warning('Invalid state: {}'.format(state_label))

    def switch_mode(self, user, new_mode):
        user.state = ''
        if user.bot_mode == new_mode:
            text = 'The Bot already in "{0}" mode.'.format(new_mode.replace('_', ' ').capitalize())
            self.api.sendMessage(user.telegram.chat_id, text, json.dumps({'hide_keyboard': True}))
            return
        if new_mode == 'one_note':
            if user.evernote.access.permission == 'full':
                note = self.evernote.create_note(
                    user.evernote.access.token,
                    user.evernote.notebook.guid,
                    title='Telegram bot notes'
                )
                user.bot_mode = new_mode
                user.evernote.shared_note_id = note.guid
            else:
                text = 'To enable "One note" mode you should allow to bot to read and update your notes'
                self.api.sendMessage(user.telegram.chat_id, text, json.dumps({'hide_keyboard': True}))
                message_text = 'Please tap on button below to give access to bot.'
                button_text = 'Allow read and update notes'
                oauth(self, user, message_text, button_text, access='full')
                return
        user.bot_mode = new_mode
        text = 'The Bot was switched to "{0}" mode.'.format(new_mode.replace('_', ' ').capitalize())
        self.api.sendMessage(user.telegram.chat_id, text, json.dumps({'hide_keyboard': True}))

    def switch_notebook(self, user, notebook_name):
        token = user.evernote.access.token
        query = { 'name': notebook_name }
        notebooks = self.evernote.get_all_notebooks(token, query)
        if not notebooks:
            self.api.sendMessage(user.telegram.chat_id, 'Notebook "{}" not found'.format(notebook_name))
            return
        user.state = ''
        user.evernote.notebook.from_dict(notebooks[0])
        # TODO: self.create_note(notebook) if user.bot_mode == 'one_note'
        text = 'Current notebook: {0}'.format(notebook_name)
        self.api.sendMessage(user.telegram.chat_id, text, json.dumps({'hide_keyboard': True}))

    def save_note(self, user, text=None, title=None, html=None, files=None):
        if user.bot_mode == 'one_note':
            self.evernote.update_note(
                user.evernote.access.token,
                user.evernote.shared_note_id,
                text=text,
                html=html,
                title=title,
                files=files
            )
        else:
            self.evernote.create_note(
                user.evernote.access.token,
                user.evernote.notebook.guid,
                text=text,
                html=html,
                title=title,
                files=files
            )

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
            user.evernote.access.token = self.evernote.get_access_token(
                evernote_config['key'],
                evernote_config['secret'],
                oauth.token,
                oauth.secret,
                oauth_verifier
            )
            user.evernote.access.permission = access_type
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
        if access_type == 'basic':
            text = 'Evernote account is connected.\nFrom now you can just send a message and a note will be created.'
            self.api.sendMessage(chat_id, text)
            default_notebook = self.evernote.get_default_notebook(user.evernote.access.token)
            user.evernote.notebook.from_dict(default_notebook)
            user.save()
            mode = user.bot_mode.replace('_', ' ').capitalize()
            text = 'Current notebook: {0}\nCurrent mode: {1}'.format(user.evernote.notebook.name, mode)
            self.api.sendMessage(chat_id, text)
        else:
            self.switch_mode(user, 'one_note')
            user.save()
