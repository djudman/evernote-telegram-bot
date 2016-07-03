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
        await self.on_before_handle_update(data)

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

    async def get_user(self, message):
        return message['from']['id']

    async def handle_message(self, message: dict):
        user = await self.get_user(message)

        await self.on_message_received(user, message)

        if 'photo' in message:
            await self.on_photo(user, message)
        elif 'document' in message:
            await self.on_document(user, message)
        elif 'voice' in message:
            await self.on_voice(user, message)
        elif 'location' in message:
            await self.on_location(user, message)
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
                    await self.execute_command(cmd, user, message)
            else:
                text = message.get('text')
                if text:
                    await self.on_text(user, message, text)

        await self.on_message_processed(user, message)

    async def execute_command(self, cmd_name: str, user, message):
        CommandClass = self.commands.get(cmd_name)
        if not CommandClass:
            raise TelegramBotError('Command "%s" not found' % cmd_name)
        obj = CommandClass(self)
        result = await obj.execute(user, message)
        await self.on_command_completed(cmd_name, user, result)

    async def on_before_handle_update(self, data):
        pass

    async def on_command_completed(self, cmd_name, user, result):
        pass

    async def on_message_received(self, user, message):
        pass

    async def on_message_processed(self, user, message):
        pass

    async def on_photo(self, user, message):
        pass

    async def on_document(self, user, message):
        pass

    async def on_voice(self, user, message):
        pass

    async def on_location(self, user, message):
        pass

    async def on_text(self, user, message, text):
        pass


class TelegramBotCommand:

    name = 'command_name'

    def __init__(self, bot: TelegramBot):
        self.bot = bot
        assert self.__class__.name != 'command_name',\
            'You must define command name with "name" class attribute'

    @abstractmethod
    async def execute(self, user, message):
        pass
