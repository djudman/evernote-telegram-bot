import logging
from typing import Optional, Callable

from utelegram.api import BotApi
from utelegram.models import Update, Message


class TelegramBotError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class TelegramBot:

    __update_types__ = {
        '*', 'message', 'edited_message', 'channel_post', 'edited_channel_post',
        'inline_query', 'chosen_inline_result', 'callback_query',
        'shipping_query', 'pre_checkout_query', 'poll'
    }

    def __init__(self, token: str, bot_url: str = None, config: dict = None, storage=None):
        self.config = config or {}
        self.api = BotApi(token)
        self.url = bot_url
        self.storage = storage
        self.__commands__ = {}
        self.__handlers__ = {}
        self.logger = logging.getLogger("utelegram")

    def set_command_handler(self, name: str, callable_handler: Callable):
        if name in self.__commands__:
            raise TelegramBotError(f'Command with name `{name}` already registered.')
        self.__commands__[name] = callable_handler

    def set_update_handler(self, update_type: str, handler: Callable):
        if update_type not in self.__update_types__:
            raise TelegramBotError(f'Invalid update type `{update_type}`')
        self.__handlers__[update_type] = handler

    def process_update(self, update_data: dict):
        self.logger.debug(update_data)
        update = Update(**update_data)
        try:
            on_update = self.__handlers__.get('*')
            if on_update and on_update(update) == False:
                return
            if update.message and self.__execute_command(update.message):
                return
            for update_type in self.__update_types__:
                if update_type == '*':  # Already handled
                    continue
                value = getattr(update, update_type)
                if value is None:
                    continue
                handler = self.__handlers__.get(update_type)
                if handler is None:
                    continue
                handler(self, value)
                break
            else:
                raise TelegramBotError('No handlers found')
        except TelegramBotError as e:
            message = update.message or update.edited_message or \
                update.channel_post or update.edited_channel_post
            if message and message.chat:
                chat_id = message.chat.id
                text = '\u274c Error. {0}'.format(e)
                self.send_message(chat_id, text)
            raise e
        except Exception as e:
            raise TelegramBotError(e)

    def __execute_command(self, message: Message):
            command_name = self.__parse_command(message)
            if not command_name:
                return
            on_command = self.__commands__.get(command_name)
            if not on_command:
                raise TelegramBotError(f'Command `{command_name}` not found')
            on_command(self, message)
            return True

    def __parse_command(self, message: Message) -> Optional[str]:
        if not message.entities or len(message.entities) > 1:
            return
        entity = next(iter(message.entities))  # list is not iterator
        if entity.type != 'bot_command':
            return
        text = message.text
        if text.startswith('/') and entity.offset == 0:
            return text[1:entity.length]  # skip ahead '/'

    def send_message(self, chat_id, text):
        return self.api.sendMessage(chat_id, text)
