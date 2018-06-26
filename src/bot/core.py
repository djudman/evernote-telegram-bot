from bot.commands import help_command
from bot.commands import start_command
from config import STORAGE
from importlib import import_module
from telegram.bot_api import BotApi


class EvernoteBot:
    def __init__(self, telegram_token):
        self.telegram_api = BotApi(telegram_token)
        StorageClass = import_module(STORAGE['class'])
        self.storage = StorageClass(STORAGE)

    def handle_telegram_update(telegram_update): # TODO: handle all errors and send error message to client
        command_name = telegram_update.get_command()
        if command_name:
            return execute_command(command_name, telegram_update)
        message = telegram_update.message or telegram_update.edited_message
        if message:
            telegram_user = message.from_user
            user = self.storage.get(User, telegram_user.id)
            if not user:
                user = User()
                user.import_telegram_data(telegram_user, message.chat)
                user.save()
            handle_text_message(message)

    def execute_command(self, name):
        if name == 'help':
            return help_command()
