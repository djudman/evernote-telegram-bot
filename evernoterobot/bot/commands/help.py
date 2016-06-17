from telegram.bot import TelegramBotCommand


class HelpCommand(TelegramBotCommand):

    name = 'help'

    async def execute(self, message):
        text = '''This is bot for evernote.
Contacts:
    email: djudman@gmail.com
'''
        chat_id = message['chat']['id']
        await self.bot.api.sendMessage(chat_id, text)
