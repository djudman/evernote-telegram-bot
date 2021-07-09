import json
import logging
from typing import Optional

from .api import BotApi


class TelegramBotError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def extract_message_from_update(update: dict) -> Optional[dict]:
    fields = ('message', 'edited_message', 'channel_post', 'edited_channel_post')
    for name in fields:
        if name in update:
            return update[name]


class TelegramBot:

    def __init__(self, name: str, token: str):
        self.api = BotApi(token)
        self.url = f'https://t.me/{name}'
        self._commands = {}
        self._handlers = {}
        self.ctx = None
        self.logger = logging.getLogger('telegram.bot')

    @property
    def current_update(self):
        if not self.ctx:
            raise TelegramBotError(f'Internal error (no ctx)')
        return self.ctx['update']

    def build_ctx(self, update: dict):
        ctx = {'update': update}
        message = extract_message_from_update(update)
        if message:
            ctx['message'] = message
            ctx['user_id'] = message['from']['id']
        return ctx

    def process_update(self, update: dict):
        self.logger.debug(update)
        self.ctx = self.build_ctx(update)
        message = self.ctx.get('message')
        try:
            if message and (command_name := self._parse_command(message)):
                self.exec_command(command_name)
            else:
                self.exec_handler()
        except TelegramBotError as e:
            self.send_message('\u274c Error. {0}'.format(e))
            raise e
        except Exception as e:
            raise TelegramBotError(e)
        finally:
            self.ctx = None

    def exec_command(self, name: str):
        handler = self._commands.get(name)
        if not handler:
            raise TelegramBotError(f'Command `{name}` not found')
        message = self.current_update['message']
        handler(self, message)

    def exec_handler(self):
        update = self.current_update
        for update_type, handler in self._handlers:
            if update_type not in update or not handler:
                continue
            handler(self, update[update_type])
            break
        else:
            self.logger.info(f'No handlers found for update: {update}')

    @staticmethod
    def _parse_command(message: dict) -> Optional[str]:
        entities = message.get('entities', [])
        if len(entities) != 1:
            return
        entity = entities[0]
        if entity['type'] != 'bot_command':
            return
        text = message['text']
        if text.startswith('/') and entity['offset'] == 0:
            name = text[1:entity['length']]  # skip ahead '/'
            return name

    def send_message(self, text: str, chat_id: int = None) -> Optional[dict]:
        if not chat_id and (update := self.current_update):
            fields = ('message', 'edited_message', 'channel_post', 'edited_channel_post')
            for name in fields:
                if (message := update.get(name)) and message.chat:
                    chat_id = message['chat']['id']
                    break
        if chat_id:
            markup = json.dumps({'hide_keyboard': True})
            return self.api.sendMessage(chat_id, text, markup)
        self.logger.error(f'Can\'t send message `{text}`: no chat_id')
