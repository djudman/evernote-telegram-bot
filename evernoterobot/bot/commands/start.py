import json

from telegram.bot import TelegramBotCommand
from bot.model import StartSession, User, ModelNotFound


class StartCommand(TelegramBotCommand):

    name = 'start'

    async def execute(self, user, message):
        welcome_text = '''Welcome! It's bot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with bot.'''
        signin_button = {
            'text': 'Waiting for Evernote...',
            'url': self.bot.url,
        }
        inline_keyboard = {'inline_keyboard': [[signin_button]]}
        chat_id = message['chat']['id']
        msg = await self.bot.api.sendMessage(chat_id, welcome_text,
                                             json.dumps(inline_keyboard))
        # TODO: async
        user_id = message['from']['id']
        oauth_data = self.bot.evernote.get_oauth_data(user_id)

        try:
            StartSession.get({'user_id': user_id})
        except ModelNotFound:
            await StartSession.create(user_id=user_id, oauth_data=oauth_data)

        try:
            User.get({'user_id': user_id})
        except ModelNotFound:
            await User.create(user_id=user_id, telegram_chat_id=chat_id)

        signin_button['text'] = 'Sign in to Evernote'
        signin_button['url'] = oauth_data["oauth_url"]
        await self.bot.api.editMessageReplyMarkup(
            chat_id, msg['message_id'], json.dumps(inline_keyboard))
