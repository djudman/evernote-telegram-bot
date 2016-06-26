from telegram.bot import TelegramBotCommand


class HelpCommand(TelegramBotCommand):

    name = 'help'

    async def execute(self, user, message):
        text = '''This is bot for evernote.
Contacts:
    email: djudman@gmail.com
'''
        await self.bot.api.sendMessage(user.telegram_chat_id, text)
