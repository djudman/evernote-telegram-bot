import json
import logging
import random
import string
from os.path import basename
from os.path import join
from time import time
from urllib.parse import urlparse

from uhttp.client import make_request

from utelegram import TelegramBot, TelegramBotError
from utelegram.models import Message

from evernotebot.bot.commands import start_command, \
    switch_mode_command, switch_notebook_command, help_command
from evernotebot.bot.models import BotUser, EvernoteOauthData, EvernoteNotebook
from evernotebot.bot.shortcuts import get_evernote_oauth_data, get_cached_object
from evernotebot.bot.storage import Mongo
from evernotebot.util.evernote.client import EvernoteApi


class EvernoteBotException(Exception):
    pass


class EvernoteBot(TelegramBot):
    def __init__(self, config, storage=None):
        telegram_config = config["telegram"]
        token = telegram_config["token"]
        bot_url = telegram_config["bot_url"]
        super().__init__(token, bot_url=bot_url, config=config)
        self._evernote_clients_cache = {}
        self.storage = storage
        if self.storage is None:
            self.storage = self._get_default_storage(config)
        self.register_handlers()

    def _get_default_storage(self, config):
        storage_config = config["storage"]
        connection_string = storage_config["connection_string"]
        db_name = storage_config["db"]
        return Mongo(connection_string, db_name=db_name, collection_name="users")

    def evernote(self, bot_user: BotUser=None) -> EvernoteApi:
        access_token = bot_user.evernote.access_token if bot_user else None
        sandbox = self.config.get("debug", True)
        return get_cached_object(
            self._evernote_clients_cache,
            bot_user.id,
            constructor=lambda: EvernoteApi(access_token, sandbox)
        )

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
        user_data = self.storage.get(user_id)
        bot_user = BotUser(**user_data)
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
            "switch_mode": self.switch_mode,  # self.switch_mode()
            "switch_notebook": self.switch_notebook,  # self.switch_notebook()
        }
        state_handler = handlers_map.get(state)
        if not state_handler:
            raise EvernoteBotException(f"Invalid state: {state}")
        state_handler(bot_user, message.text)
        bot_user.state = None
        self.storage.save(bot_user.asdict())

    def handle_message(self, message: Message):
        message_attrs = ("text", "photo", "voice", "audio", "video",
                         "document", "location")
        for attr_name in message_attrs:
            value = getattr(message, attr_name, None)
            if value is None:
                continue
            handler = getattr(self, f"on_{attr_name}", None)
            if handler is None:
                continue
            status_message = self.api.sendMessage(
                message.chat.id, f"{attr_name.capitalize()} accepted")
            handler(message)
            self.api.editMessageText(message.chat.id,
                status_message["message_id"], "Saved")

    def switch_mode(self, bot_user: BotUser, selected_mode_str: str):
        def validate(mode_str):
            mode = mode_str
            if mode_str.startswith("> ") and mode_str.endswith(" <"):
                mode = mode_str[2:-2]
            title = mode
            mode = mode.lower().replace(" ", "_")
            if mode not in ("one_note", "multiple_notes"):
                raise TelegramBotError(f"Unknown mode '{title}'")
            return mode, title

        new_mode, new_mode_title = validate(selected_mode_str)
        chat_id = bot_user.telegram.chat_id
        if bot_user.bot_mode == new_mode:
            text = f"The Bot already in '{new_mode_title}' mode."
            self.api.sendMessage(chat_id, text, json.dumps({"hide_keyboard": True}))
            return
        if new_mode == "one_note":
            self.switch_mode_one_note(bot_user)
            return
        bot_user.evernote.shared_note_id = None
        bot_user.bot_mode = new_mode
        text = f"The Bot was switched to '{new_mode_title}' mode."
        self.api.sendMessage(chat_id, text, json.dumps({"hide_keyboard": True}))

    def switch_notebook(self, bot_user: BotUser, notebook_name: str):
        if notebook_name.startswith("> ") and notebook_name.endswith(" <"):
            notebook_name = notebook_name[2:-2]
        query = {"name": notebook_name}
        notebooks = self.evernote(bot_user).get_all_notebooks(query)
        if not notebooks:
            raise TelegramBotError(f"Notebook '{notebook_name}' not found")
        # TODO: self.create_note(notebook) if bot_user.bot_mode == 'one_note'
        notebook = notebooks[0]
        bot_user.evernote.notebook.name = notebook["name"]
        bot_user.evernote.notebook.guid = notebook["guid"]
        chat_id = bot_user.telegram.chat_id
        self.api.sendMessage(chat_id, f"Current notebook: {notebook['name']}",
                             json.dumps({"hide_keyboard": True}))

    def switch_mode_one_note(self, bot_user: BotUser):
        chat_id = bot_user.telegram.chat_id
        evernote_data = bot_user.evernote
        if evernote_data.access.permission == 'full':
            note = self.evernote(bot_user).create_note(
                evernote_data.notebook.guid,
                title='Telegram bot notes'
            )
            bot_user.bot_mode = 'one_note' # TODO: move up
            evernote_data.shared_note_id = note.guid
            note_url = self.evernote(bot_user).get_note_link(note.guid)
            text = f'Your notes will be saved to <a href="{note_url}">this note</a>'
            self.api.sendMessage(chat_id, text, json.dumps({'hide_keyboard': True}), parse_mode='Html')
        else:
            text = 'To enable "One note" mode you should allow to the bot both reading and updating your notes'
            self.api.sendMessage(chat_id, text, json.dumps({'hide_keyboard': True}))
            message_text = 'Please tap on button below to give access to bot.'
            button_text = 'Allow read and update notes'
            bot_user.evernote.oauth = get_evernote_oauth_data(self, bot_user.id,
                chat_id, message_text, button_text, access='full')

    def save_note(self, user: BotUser, text=None, title=None, **kwargs):
        if user.bot_mode == 'one_note':
            note_id = user.evernote.shared_note_id
            self.evernote(user).update_note(note_id, text, title, **kwargs)
        else:
            notebook_id = user.evernote.notebook.guid
            self.evernote(user).create_note(notebook_id, text, title, **kwargs)

    def _download_file_from_telegram(self, file_id):
        download_url = self.api.getFile(file_id)
        data = make_request(download_url)
        short_name = basename(urlparse(download_url).path)
        filename = join(self.config["tmp_root"], f"{file_id}_{short_name}")
        with open(filename, "wb") as f:
            f.write(data)
        return filename, short_name

    def _check_evernote_quota(self, bot_user: BotUser, file_size):
        quota = self.evernote(bot_user).get_quota_info()
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
        self._check_evernote_quota(user, file_size)
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
