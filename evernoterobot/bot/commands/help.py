from telegram.bot import TelegramBotCommand


class HelpCommand(TelegramBotCommand):

    __name__ = 'help'

    async def execute(self, message):
        return '''This is bot for evernote.
Contacts:
    email: djudman@gmail.com
'''
