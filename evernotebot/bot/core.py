import copy
import importlib
import json
import logging
import traceback
from time import time

from evernotebot.bot.commands import (
    start_command, switch_mode_command, switch_notebook_command, help_command
)
from evernotebot.bot.models import BotUser
from evernotebot.bot.shortcuts import (
    get_evernote_oauth_data, download_telegram_file, get_message_caption,
    get_telegram_link
)
from evernotebot.telegram import Message, TelegramBot, TelegramBotError
from evernotebot.util.evernote.client import EvernoteApi


class EvernoteBotException(TelegramBotError):
    pass


class EvernoteBot(TelegramBot):
    def __init__(self, config):
        super().__init__(config['telegram']['bot_name'], config['telegram']['token'])
        self.config = config
        self._handlers = {
            'message': self.on_message,
            'edited_message': self.on_message,
            'channel_post': None, # TODO:
            'edited_channel_post': None, # TODO:
        }
        self._commands = {
            'start': start_command,
            'switch_mode': switch_mode_command,
            'notebook': switch_notebook_command,
            'help': help_command,
        }
        self._evernote_api = {}
        storage_config = config['storage']
        self.users = self._init_storage(storage_config['users'])
        self.failed_updates = self._init_storage(storage_config['failed_updates'])

    def _init_storage(self, config: dict):
        module_name, classname = config['class'].rsplit('.', 1)
        module = importlib.import_module(module_name)
        config_copy = copy.deepcopy(config)
        del config_copy['class']
        StorageClass = getattr(module, classname)
        return StorageClass(**config_copy)

    def stop(self):
        self.users.close()
        self.failed_updates.close()

    def get_evernote_api(self, user_id: int = None):
        user_id = user_id or self.ctx.get('user_id')
        if not user_id:
            raise Exception('`user_id` is not set')
        if not self._evernote_api.get(user_id):
            user_data = self.users.get(user_id)
            user = BotUser(**user_data)
            token = user.evernote.access.token
            self._evernote_api[user_id] = EvernoteApi(token, sandbox=self.config['debug'])
        return self._evernote_api[user_id]

    def on_message(self, bot, message: dict):
        user_id = message['from']['id']
        user_data = self.users.get(user_id)
        if not user_data:
            raise EvernoteBotException(f"Unregistered user {user_id}. "
                                        "You've to send /start command to register")
        bot_user = BotUser(**user_data)
        if not bot_user.evernote or not bot_user.evernote.access.token:
            raise EvernoteBotException("You have to sign in to Evernote first. "
                                       "Send /start and press the button")
        self.ctx['user'] = bot_user
        if bot_user.state:
            self.handle_state(bot_user, message)
            return
        self.handle_message(message)

    def handle_state(self, bot_user: BotUser, message: dict):
        state = bot_user.state
        handlers_map = {
            'switch_mode': self.switch_mode,  # self.switch_mode()
            'switch_notebook': self.switch_notebook,  # self.switch_notebook()
        }
        state_handler = handlers_map[state]
        state_handler(bot_user, message['text'])
        bot_user.state = None
        self.users.save(bot_user.asdict())

    def handle_message(self, message: Message):
        message_attrs = ('text', 'photo', 'voice', 'audio', 'video', 'document', 'location')
        for attr_name in message_attrs:
            value = getattr(message, attr_name, None)
            if value is None:
                continue
            status_message = self.api.sendMessage(message.chat.id, f'{attr_name.capitalize()} accepted')
            handler = getattr(self, f'on_{attr_name}')
            handler(message)
            self.api.editMessageText(message.chat.id, status_message['message_id'], 'Saved')

    def _validate_mode(self, selected_mode_str):
        mode = selected_mode_str
        if selected_mode_str.startswith('> ') and selected_mode_str.endswith(' <'):
            mode = selected_mode_str[2:-2]
        title = mode
        mode = mode.lower().replace(' ', '_')
        if mode not in {'one_note', 'multiple_notes'}:
            raise EvernoteBotException(f'Unknown mode `{title}`')
        return mode, title

    def switch_mode(self, bot_user: BotUser, selected_mode_str: str):
        new_mode, new_mode_title = self._validate_mode(selected_mode_str)
        if bot_user.bot_mode == new_mode:
            text = f'The bot already in `{new_mode_title}` mode.'
            self.send_message(text)
            return
        if new_mode == 'one_note':
            self.switch_mode_one_note(bot_user)
        elif new_mode == 'multiple_notes':
            bot_user.evernote.shared_note_id = None
            bot_user.bot_mode = new_mode
            self.send_message(f'The bot has switched to `{new_mode_title}` mode.')
        raise EvernoteBotException(f'Unknown mode `{new_mode}`')

    def switch_notebook(self, bot_user: BotUser, notebook_name: str):
        if notebook_name.startswith('> ') and notebook_name.endswith(' <'):
            notebook_name = notebook_name[2:-2]
        evernote = self.get_evernote_api()
        notebooks = evernote.get_all_notebooks({'name': notebook_name})
        if not notebooks:
            raise EvernoteBotException(f'Notebook `{notebook_name}` not found')
        # TODO: self.create_note(notebook) if bot_user.bot_mode == 'one_note'
        notebook = notebooks[0]
        bot_user.evernote.notebook.name = notebook['name']
        bot_user.evernote.notebook.guid = notebook['guid']
        self.send_message(f'Current notebook: {notebook["name"]}')

    def switch_mode_one_note(self, bot_user: BotUser):
        chat_id = bot_user.telegram.chat_id
        evernote_data = bot_user.evernote
        if evernote_data.access.permission == 'full':
            note = self.get_evernote_api().create_note(
                evernote_data.notebook.guid,
                title='Telegram bot notes'
            )
            bot_user.bot_mode = 'one_note' # TODO: move up
            evernote_data.shared_note_id = note.guid
            note_url = self.get_evernote_api().get_note_link(note.guid)
            text = f'Your notes will be saved to <a href="{note_url}">this note</a>'
            self.api.sendMessage(chat_id, text, json.dumps({'hide_keyboard': True}), parse_mode='Html')
        else:
            self.send_message('To enable `One note` mode you have to allow '
                              'to the bot both reading and updating your notes')
            bot_user.evernote.oauth = get_evernote_oauth_data(
                self, bot_user,
                'Please, sign in and give the permissions to the bot.',
                access='full')

    def save_note(self, text: str = None, title: str = None, **kwargs):
        user = self.ctx['user']
        evernote = self.get_evernote_api(user.id)
        if user.bot_mode == 'one_note':
            note_id = user.evernote.shared_note_id
            evernote.update_note(note_id, text, title, **kwargs)
        else:
            notebook_id = user.evernote.notebook.guid
            evernote.create_note(notebook_id, text, title, **kwargs)

    def _check_evernote_quota(self, file_size: int):
        quota = self.get_evernote_api().get_quota_info()
        if quota['remaining'] < file_size:
            reset_date = quota['reset_date'].strftime('%Y-%m-%d %H:%M:%S')
            remain_bytes = quota['remaining']
            raise EvernoteBotException(f'Your evernote quota is out ({remain_bytes} bytes remains till {reset_date})')

    def save_file_to_evernote(self, file_id, file_size, message: dict):
        # telegram restriction. We can't download file > 20Mb
        max_size = 20 * 1024 * 1024
        if file_size > max_size:
            raise EvernoteBotException('File too big. Telegram does not allow to the bot to download files over 20Mb.')
        filename, short_name = download_telegram_file(self.api, file_id, self.config['tmp_root'])
        self._check_evernote_quota(file_size)
        title = get_message_caption(message) or (message['text'] and message['text'][:20]) or 'File'
        files = ({'path': filename, 'name': short_name},)
        text = ''
        telegram_link = get_telegram_link(message)
        if telegram_link:
            text = f'<div><p><a href="{telegram_link}">{telegram_link}</a></p><pre>{message["caption"]}</pre></div>'
        self.save_note('', title=title, files=files, html=text)

    def fail_update(self, data: dict):
        message = f'Telegram update failed. Data: `{data}`'
        logging.getLogger('evernotebot').error(message, exc_info=True)
        self.failed_updates.create({
            'created': time(),
            'data': data,
            'exception': traceback.format_exc(),
        }, auto_generate_id=True)
