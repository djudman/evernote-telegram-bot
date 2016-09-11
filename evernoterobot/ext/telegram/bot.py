import logging
from abc import abstractmethod

from ext.telegram.api import BotApi
from ext.telegram.models import TelegramUpdate, Message


class TelegramBotError(Exception):
    def __init__(self, message):
        super(TelegramBotError, self).__init__(message)


class TelegramBot:

    def __init__(self, token, bot_name, **kwargs):
        self.api = BotApi(token)
        self.name = bot_name
        self.url = 'https://telegram.me/%s' % bot_name
        self.logger = logging.getLogger()
        self.commands = {}
        if kwargs:
            map(lambda name, value: setattr(self, name, value), kwargs.items())

    def add_command(self, command_class, force=False):
        cmd_name = command_class.name
        if cmd_name in self.commands and not force:
            raise TelegramBotError('Command "%s" already exists' % cmd_name)
        self.commands[cmd_name] = command_class

    async def handle_update(self, data: dict):
        try:
            update = TelegramUpdate(data)
            await self.on_before_handle_update(update)

            if update.message:
                await self.handle_message(update.message)
            # TODO: process inline query
            # TODO: process inline result
            # TODO: process callback query
        except Exception as e:
            self.logger.error(e, exc_info=1)

    async def handle_message(self, message: Message):
        user = message.user

        await self.on_message_received(message)

        if hasattr(message, 'photos') and message.photos:
            await self.on_photo(message)
        if hasattr(message, 'video') and message.video:
            await self.on_video(message)
        if hasattr(message, 'document') and message.document:
            await self.on_document(message)
        if hasattr(message, 'voice') and message.voice:
            await self.on_voice(message)
        if hasattr(message, 'location') and message.location:
            await self.on_location(message)

        commands = [cmd.replace('/', '') for cmd in message.bot_commands or []]
        if commands:
            for cmd in commands:
                await self.execute_command(cmd, message)
        else:
            text = message.text
            if text:
                await self.on_text(message)

        await self.on_message_processed(message)

    async def execute_command(self, cmd_name: str, message: Message):
        CommandClass = self.commands.get(cmd_name)
        if not CommandClass:
            raise TelegramBotError('Command "%s" not found' % cmd_name)
        obj = CommandClass(self)
        await obj.execute(message)

    async def on_before_handle_update(self, update: TelegramUpdate):
        pass

    async def on_message_received(self, message: Message):
        pass

    async def on_message_processed(self, message: Message):
        pass

    async def on_photo(self, message: Message):
        pass

    async def on_video(self, message: Message):
        pass

    async def on_document(self, message: Message):
        pass

    async def on_voice(self, message: Message):
        pass

    async def on_location(self, message: Message):
        pass

    async def on_text(self, message: Message):
        pass


class TelegramBotCommand:

    name = 'command_name'

    def __init__(self, bot: TelegramBot):
        self.bot = bot
        assert self.__class__.name != 'command_name',\
            'You must define command name with "name" class attribute'

    @abstractmethod
    async def execute(self, message: Message):
        pass
