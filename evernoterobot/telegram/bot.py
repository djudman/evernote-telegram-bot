import logging
from abc import abstractmethod

from telegram.api import BotApi


class TelegramBotError(Exception):
    def __init__(self, message):
        super(TelegramBotError, self).__init__(message)


class TelegramBot:

    def __init__(self, token, bot_name):
        self.api = BotApi(token)
        self.name = bot_name
        self.url = 'https://telegram.me/%s' % bot_name
        self.logger = logging.getLogger()
        self.commands = {}

    def add_command(self, handler_class, force=False):
        cmd_name = handler_class.name
        if cmd_name in self.commands and not force:
            raise TelegramBotError('Command "%s" already exists' % cmd_name)
        self.commands[cmd_name] = handler_class

    async def handle_update(self, data: dict):
        if 'message' in data:
            await self.handle_message(data['message'])
        elif 'inline_query' in data:
            self.logger.info('Inline query: %s' % data)
            # TODO: process inline query
        elif 'chosen_inline_result' in data:
            self.logger.info('Chosen inline result: %s' % data)
            # TODO: process inline result
        elif 'callback_query' in data:
            self.logger.info('Callback query: %s' % data)
            # TODO: process callback query
        else:
            raise TelegramBotError('Unsupported update %s' % data)

    async def handle_message(self, message: dict):
        user_id = message['from']['id']
        chat_id = message['chat']['id']

        await self.on_message_received(user_id, chat_id, message)

        if 'photo' in message:
            await self.on_photo(user_id, chat_id, message)
        elif 'document' in message:
            await self.on_document(user_id, chat_id, message)
        elif 'voice' in message:
            await self.on_voice(user_id, chat_id, message)
        elif 'location' in message:
            await self.on_location(user_id, chat_id, message)
        else:
            commands = []
            for entity in message.get('entities', []):
                if entity['type'] == 'bot_command':
                    offset = entity['offset']
                    length = entity['length']
                    cmd = message.get('text', '')[offset:length]
                    if cmd.startswith('/'):
                        cmd = cmd.replace('/', '')
                    commands.append(cmd)

            if commands:
                for cmd in commands:
                    await self.execute_command(cmd, message)
            else:
                text = message.get('text')
                if text:
                    await self.on_text(user_id, chat_id, message, text)

        await self.on_message_processed(user_id, chat_id, message)

    async def execute_command(self, cmd_name: str, message):
        CommandClass = self.commands.get(cmd_name)
        if not CommandClass:
            raise TelegramBotError('Command "%s" not found' % cmd_name)
        obj = CommandClass(self)
        result = await obj.execute(message)
        await self.on_command_completed(cmd_name, result)

    async def on_command_completed(self, cmd_name, result):
        pass

    async def on_message_received(self, user_id, chat_id, message):
        pass

    async def on_message_processed(self, user_id, chat_id, message):
        pass

    async def on_photo(self, user_id, chat_id, message):
        pass

    async def on_document(self, user_id, chat_id, message):
        pass

    async def on_voice(self, user_id, chat_id, message):
        pass

    async def on_location(self, user_id, chat_id, message):
        pass

    async def on_text(self, user_id, chat_id, message, text):
        pass


class TelegramBotCommand:

    name = 'command_name'

    def __init__(self, bot: TelegramBot):
        self.bot = bot
        assert self.__class__.name != 'command_name',\
            'You must define command name with "name" class attribute'

    @abstractmethod
    async def execute(self, message):
        pass
