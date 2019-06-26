import json
import logging
import random
import string
from os.path import basename
from os.path import join
from urllib.parse import urlparse

from uhttp.client import make_request

from requests_oauthlib.oauth1_session import TokenRequestDenied
from utelegram import TelegramBot, TelegramBotError
from utelegram.models import Message

from evernotebot.bot.commands import start_command, \
    switch_mode_command, switch_notebook_command, help_command
from evernotebot.bot.models import BotUser, EvernoteOauthData
from evernotebot.bot.storage import Mongo
from evernotebot.util.evernote.client import EvernoteClient


class EvernoteBotException(Exception):
    pass


class EvernoteBot(TelegramBot):
    def __init__(self, config):
        self.evernote = EvernoteClient(sandbox=config.get("debug", True))
        telegram_config = config["telegram"]
        token = telegram_config["token"]
        bot_url = telegram_config["bot_url"]
        storage_config = config["storage"]
        connection_string = storage_config["connection_string"]
        db_name = storage_config["db"]
        super().__init__(token, bot_url=bot_url, config=config)
        self.storage = Mongo(connection_string, db_name=db_name, collection_name="users")
        self.register_handlers()

    def register_handlers(self):
        self.set_update_handler("message", self.on_message)
        self.set_update_handler("edited_message", self.on_message)
        commands = {
            "start": start_command,
            "switch_mode": switch_mode_command,
            "switch_notebook": switch_notebook_command,
            "help": help_command,
        }
        for name, handler in commands.items():
            self.set_command_handler(name, handler)

    def on_message(self, bot, message: Message):
        user_id = message.from_user.id
        bot_user = self.storage.get(user_id)
        if not bot_user:
            raise EvernoteBotException(f"Unregistered user {user_id}. "
                                        "You've to send /start command to register")
        if not bot_user.evernote or not bot_user.evernote.access.token:
            raise EvernoteBotException("You have to sign in to Evernote first. "
                                       "Send /start and press the button")
        if bot_user.state:
            self.handle_state(bot_user, message)
        else:
            self.handle_message(message)

    def handle_state(self, bot_user: BotUser, message: Message):
        state = bot_user.state
        handlers_map = {
            "switch_mode": self.switch_mode,
            "switch_notebook": self.switch_notebook,
        }
        state_handler = handlers_map.get(state)
        if not state_handler:
            raise EvernoteBotException(f"Invalid state: {state}")
        state_handler(bot_user, message.text)
        bot_user.state = None
        self.storage.save(bot_user.asdict())

    def handle_message(self, message: Message):
        message_attrs = ('text', 'photo', 'voice', 'audio', 'video', 'document', 'location')
        for attr_name in message_attrs:
            value = getattr(message, attr_name, None)
            if value is None:
                continue
            handler = getattr(self, f"on_{attr_name}", None)
            if handler is None:
                continue
            status_message = self.api.sendMessage(message.chat.id, f"{attr_name.capitalize()} accepted")
            handler(self, message)
            self.api.editMessageText(message.chat.id, status_message['message_id'], 'Saved')

    def switch_mode(self, bot_user: BotUser, new_mode: str):
        new_mode = new_mode.lower()
        if new_mode.startswith("> ") and new_mode.endswith(" <"):
            new_mode = new_mode[2:-2]
        new_mode = new_mode.replace(" ", "_")
        if new_mode not in ("one_note", "multiple_notes"):
            raise TelegramBotError(f"Unknown mode '{new_mode}'")
        new_mode_title = new_mode.replace("_", " ").capitalize()
        chat_id = bot_user.telegram.chat_id
        if bot_user.bot_mode == new_mode:
            text = f"The Bot already in '{new_mode_title}' mode."
            self.api.sendMessage(chat_id, text, json.dumps({"hide_keyboard": True}))
        elif new_mode == "one_note":
            self.switch_mode_one_note(bot_user)
        else:
            bot_user.evernote.shared_note_id = None
            bot_user.bot_mode = new_mode
            text = f"The Bot was switched to '{new_mode_title}' mode."
            self.api.sendMessage(chat_id, text, json.dumps({"hide_keyboard": True}))

    def switch_notebook(self, bot_user: BotUser, notebook_name: str):
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

    def switch_mode_one_note(self, bot_user: BotUser):
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
            bot_user.evernote.oauth = self.get_evernote_oauth_data(bot_user.id, chat_id, message_text, button_text, access='full')

    def save_note(self, user: BotUser, text=None, title=None, html=None, files=None):
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

    def get_evernote_oauth_data(self, user_id: int, chat_id: int, message_text: str, button_text: str, access='basic'):
        auth_button = {'text': 'Waiting for Evernote...', 'url': self.url}
        inline_keyboard = {'inline_keyboard': [[auth_button]]}
        status_message = self.api.sendMessage(chat_id, message_text, json.dumps(inline_keyboard))
        symbols = string.ascii_letters + string.digits
        session_key = ''.join([random.choice(symbols) for _ in range(32)])
        oauth_data = self.evernote.get_oauth_data(user_id, session_key, self.config['evernote'], access)
        auth_button['text'] = button_text
        auth_button['url'] = oauth_data['oauth_url']
        self.api.editMessageReplyMarkup(chat_id, status_message['message_id'], json.dumps(inline_keyboard))
        keys = ('callback_key', 'oauth_token', 'oauth_token_secret')
        return {
            "callback_key": oauth_data["callback_key"],
            "token": oauth_data["oauth_token"],
            "secret": oauth_data["oauth_token_secret"],
        }

    def evernote_oauth_callback(self, callback_key, oauth_verifier, access_type):
        if not oauth_verifier:
            raise TelegramBotError('We are sorry, but you have declined authorization.')
        users = self.storage.get_all({'evernote.oauth.callback_key': callback_key})
        if not users:
            raise EvernoteBotException(f'User not found. callback_key = {callback_key}')
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
            self.storage.save(user.asdict())
        except TokenRequestDenied as e:
            # TODO: log original exception
            raise TelegramBotError('We are sorry, but we have some problems with Evernote connection. Please try again later.')
        except Exception as e:
            # TODO: log original exception
            raise TelegramBotError('Unknown error. Please, try again later.')
        if access_type == 'basic':
            text = 'Evernote account is connected.\nFrom now you can just send a message and a note will be created.'
            self.api.sendMessage(chat_id, text)
            default_notebook = self.evernote.get_default_notebook(user.evernote.access.token)
            user.evernote.notebook.name = default_notebook['name']
            user.evernote.notebook.guid = default_notebook['guid']
            self.storage.save(user.asdict())
            mode = user.bot_mode.replace('_', ' ').capitalize()
            self.api.sendMessage(chat_id, f'Current notebook: {user.evernote.notebook.name}\nCurrent mode: {mode}')
        else:
            self.switch_mode(user, 'one_note')
            self.storage.save(user.asdict())

    def _download_file_from_telegram(self, file_id):
        download_url = self.api.getFile(file_id)
        data = make_request(download_url)
        short_name = basename(urlparse(download_url).path)
        filename = join(self.config["tmp_root"], f"{file_id}_{short_name}")
        with open(filename, "wb") as f:
            f.write(data)
        return filename, short_name

    def _check_evernote_quota(self, evernote_access_token, file_size):
        quota = self.evernote.get_quota_info(evernote_access_token)
        if quota["remaining"] < file_size:
            reset_date = quota["reset_date"].strftime("%Y-%m-%d %H:%M:%S")
            remain_bytes = quota['remaining']
            raise EvernoteBotException(f"Your evernote quota is out ({remain_bytes} bytes remains till {reset_date})")

    def _save_file_to_evernote(self, file_id, file_size, message: Message):
        max_size = 20 * 1024 * 1024 # telegram restriction. We can't download any file that has size more than 20Mb
        if file_size > max_size:
            raise EvernoteBotException('File too big. Telegram does not allow to the bot to download files over 20Mb.')
        filename, short_name = self._download_file_from_telegram(file_id)
        user_data = self.storage.get(message.from_user.id)
        user = BotUser(**user_data)
        self._check_evernote_quota(user.evernote.access.token, file_size)
        title = message.caption or message.text[:20] or 'File'
        files = ({'path': filename, 'name': short_name},)
        self.save_note(user, text=message.text, title=title, files=files)

    def on_text(self, message: Message):
        user_data = self.storage.get(message.from_user.id)
        user = BotUser(**user_data)
        text = message.text
        self.save_note(user, text, title=text[:20])

    def on_photo(self, message: Message):
        max_size = 20 * 1024 * 1024 # telegram restriction. We can't download any file that has size more than 20Mb
        file_id = None
        file_size = 0
        for photo in message.photo: # pick the biggest file
            if file_size < photo.file_size <= max_size:
                file_size = photo.file_size
                file_id = photo.file_id
        if not file_id:
            raise EvernoteBotException("File too big. Telegram does not allow to the bot to download files over 20Mb.")
        self._save_file_to_evernote(file_id, file_size, message)

    def on_audio(self, message: Message):
        file_id = message.voice.file_id
        file_size = message.voice.file_size
        self._save_file_to_evernote(file_id, file_size, message)

    def on_document(self, message: Message):
        file_size = message.document.file_size
        file_id = message.document.file_id
        self._save_file_to_evernote(file_id, file_size, message)

    def on_video(self, message: Message):
        file_size = message.video.file_size
        file_id = message.video.file_id
        self._save_file_to_evernote(file_id, file_size, message)

    def on_location(self, message: Message):
        latitude = message.location.latitude
        longitude = message.location.longitude
        maps_url = f"https://maps.google.com/maps?q={latitude},{longitude}"
        title = "Location"
        html = f"<a href='{maps_url}'>{maps_url}</a>"
        if message.venue:
            venue = message.venue
            title=venue.title or title
            address=venue.address
            html = f"{title}<br />{address}<br /><a href='{maps_url}'>{maps_url}</a>"
            foursquare_id = venue.foursquare_id
            if foursquare_id:
                url = f"https://foursquare.com/v/{foursquare_id}"
                html += f"<br /><a href='{url}'>{url}</a>"
        user_data = self.storage.get(message.from_user.id)
        user = BotUser(**user_data)
        self.save_note(user, title=title, html=html)
