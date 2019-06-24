import json
import logging
from requests_oauthlib.oauth1_session import TokenRequestDenied

from evernotebot.bot.commands import help_command
from evernotebot.bot.commands import oauth
from evernotebot.bot.commands import start_command
from evernotebot.bot.commands import switch_mode_command
from evernotebot.bot.commands import switch_notebook_command

from evernotebot.bot.handlers.text import handle_text
from evernotebot.bot.handlers.photo import handle_photo
from evernotebot.bot.handlers.audio import handle_audio
from evernotebot.bot.handlers.video import handle_video
from evernotebot.bot.handlers.document import handle_document
from evernotebot.bot.handlers.location import handle_location

from evernotebot.bot.models import User
from evernotebot.bot.storage import Mongo
from evernotebot.util.evernote.client import EvernoteClient
from utelegram import TelegramBot, TelegramBotError
from utelegram.models import Message


class EvernoteBot(TelegramBot):
    def __init__(self, config):
        self.evernote = EvernoteClient(sandbox=config.get('debug', True))
        telegram_config = config['telegram']
        token = telegram_config['token']
        bot_url = telegram_config['bot_url']
        storage_config = config['storage']
        connection_string = storage_config['connection_string']
        db_name = storage_config['db']
        super().__init__(token, bot_url=bot_url, config=config)
        self._storage = Mongo(connection_string, db_name, 'users')
        self.set_update_handler('message', self.on_message)
        self.set_update_handler('edited_message', self.on_message)

    def on_message(self, bot, message: Message):
        user_id = message.from_user.id
        bot_user = self._storage.get(user_id)
        if not bot_user:
            raise Exception('Unregistered user {0}. You\'ve to send /start command to register'.format(user_id))
        if not bot_user.evernote.access.token:
            raise Exception('You have to sign in to Evernote first. Send /start and press the button')
        if bot_user.state:
            self.handle_state(bot_user, message)
        else:
            self.handle_message(message)

    def handle_state(self, bot_user: User, message: Message):
        state_label = bot_user.state
        if state_label not in ('switch_mode', 'switch_notebook'):
            raise Exception(f'Invalid state: {state_label}')
        if state_label == 'switch_mode':
            self.switch_mode(bot_user, message.text)
        elif state_label == 'switch_notebook':
            self.switch_notebook(bot_user, message.text)
        bot_user.state = None
        self._storage.save(bot_user.asdict())

    def handle_message(self, message: Message):
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

    def switch_mode(self, bot_user, new_mode):
        new_mode = new_mode.lower()
        if new_mode.startswith('> ') and new_mode.endswith(' <'):
            new_mode = new_mode[2:-2]
        new_mode = new_mode.replace(' ', '_')
        if new_mode not in ('one_note', 'multiple_notes'):
            raise TelegramBotError(f'Unknown mode "{new_mode}"')
        new_mode_title = new_mode.replace('_', ' ').capitalize()
        chat_id = bot_user.telegram.chat_id
        if bot_user.bot_mode == new_mode:
            text = f'The Bot already in "{new_mode_title}" mode.'
            self.api.sendMessage(chat_id, text, json.dumps({'hide_keyboard': True}))
        elif new_mode == 'one_note':
            self.switch_mode_one_note(bot_user)
        else:
            bot_user.evernote.shared_note_id = None
            bot_user.bot_mode = new_mode
            text = f'The Bot was switched to "{new_mode_title}" mode.'
            self.api.sendMessage(chat_id, text, json.dumps({'hide_keyboard': True}))

    def switch_notebook(self, bot_user, notebook_name: str):
        if notebook_name.startswith('> ') and notebook_name.endswith(' <'):
            notebook_name = notebook_name[2:-2]
        token = bot_user.evernote.access.token
        query = {'name': notebook_name}
        notebooks = self.evernote.get_all_notebooks(token, query)
        if not notebooks:
            raise TelegramBotError(f'Notebook "{notebook_name}" not found')
        # TODO: self.create_note(notebook) if bot_user.bot_mode == 'one_note'
        notebook = notebooks[0]
        bot_user.evernote.notebook.name = notebook['name']
        bot_user.evernote.notebook.guid = notebook['guid']
        chat_id = bot_user.telegram.chat_id
        self.api.sendMessage(chat_id, f'Current notebook: {notebook["name"]}', json.dumps({'hide_keyboard': True}))

    def switch_mode_one_note(self, bot_user):
        chat_id = bot_user.telegram.chat_id
        evernote_data = bot_user.evernote
        if evernote_data.access.permission == 'full':
            note = self.evernote.create_note(
                evernote_data.access.token,
                evernote_data.notebook.guid,
                title='Telegram bot notes'
            )
            bot_user.bot_mode = 'one_note' # TODO: move up
            evernote_data.shared_note_id = note.guid
            note_url = self.evernote.get_note_link(evernote_data.access.token, note.guid)
            text = f'Your notes will be saved to <a href="{note_url}">this note</a>'
            self.api.sendMessage(chat_id, text, json.dumps({'hide_keyboard': True}), parse_mode='Html')
        else:
            text = 'To enable "One note" mode you should allow to the bot both reading and updating your notes'
            self.api.sendMessage(chat_id, text, json.dumps({'hide_keyboard': True}))
            message_text = 'Please tap on button below to give access to bot.'
            button_text = 'Allow read and update notes'
            oauth(self, bot_user, message_text, button_text, access='full')

    def oauth_callback(self, callback_key, oauth_verifier, access_type):
        if not oauth_verifier:
            raise TelegramBotError('We are sorry, but you have declined authorization.')
        users = self._storage.get_all({'evernote.oauth.callback_key': callback_key})
        if not users:
            raise Exception(f'User not found. callback_key = {callback_key}')
        user = users[0]
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
            user.evernote.oauth = None
            self._storage.save(user.asdict())
        except TokenRequestDenied as e:
            # TODO: log original exception
            raise Exception('We are sorry, but we have some problems with Evernote connection. Please try again later.')
        except Exception as e:
            # TODO: log original exception
            raise Exception('Unknown error. Please, try again later.')
        if access_type == 'basic':
            text = 'Evernote account is connected.\nFrom now you can just send a message and a note will be created.'
            self.api.sendMessage(chat_id, text)
            default_notebook = self.evernote.get_default_notebook(user.evernote.access.token)
            user.evernote.notebook.name = default_notebook['name']
            user.evernote.notebook.guid = default_notebook['guid']
            self._storage.save(user.asdict())
            mode = user.bot_mode.replace('_', ' ').capitalize()
            self.api.sendMessage(chat_id, f'Current notebook: {user.evernote.notebook.name}\nCurrent mode: {mode}')
        else:
            self.switch_mode(user, 'one_note')
            self._storage.save(user.asdict())

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
