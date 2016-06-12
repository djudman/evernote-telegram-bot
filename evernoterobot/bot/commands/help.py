from telegram.bot import TelegramBotCommand


class HelpCommand(TelegramBotCommand):

    name = 'help'

    async def execute(self, message):
        return '''This is bot for evernote.
Contacts:
    email: djudman@gmail.com
'''
