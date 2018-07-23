from bot.commands import help_command
from bot.commands import start_command
from data.storage.storage import StorageMixin
from importlib import import_module
from telegram.bot_api import BotApi


class EvernoteBot(StorageMixin):
    def __init__(self, config):
        self.config = config
        telegram_token = config['telegram']['token']
        self.api = BotApi(telegram_token)

    def handle_telegram_update(self, telegram_update): # TODO: handle all errors and send error message to client
        command_name = telegram_update.get_command()
        if command_name:
            return self.execute_command(command_name, telegram_update)
        message = telegram_update.message or telegram_update.edited_message
        if message:
            self.handle_message(message)
        post = telegram_update.channel_post or telegram_update.edited_channel_post
        if post:
            self.handle_post(post)

    def execute_command(self, name, telegram_update):
        if name == 'help':
            return help_command(self, telegram_update.message.chat.id)
        elif name == 'start':
            return start_command(self, telegram_update.message)
        else:
            raise Exception('Unknown command "{}"'.format(name))

    def handle_message(self, message):
        telegram_user = message.from_user
        user = self.storage.get(User, telegram_user.id)
        if not user:
            raise Exception('Unregistered user {0}'.format(telegram_user.id))

    def handle_post(self, post):
        # TODO:
        pass

    def _register_user(self, telegram_message):
        telegram_user = telegram_message.from_user
        user_data = {
            'id': telegram_user.id,
            'bot_mode': 'multiple_notes',
            'telegram': {
                'first_name': telegram_user.first_name,
                'last_name': telegram_user.last_name,
                'username': telegram_user.username,
                'chat_id': telegram_message.chat.id,
            }
        }
        user = self.get_storage(User).create_model(user_data)
        user.save()
        return user
