import json

from bot.model import StartSession, User, ModelNotFound
from ext.telegram.bot import TelegramBotCommand
from ext.telegram.models import Message
from ext.botan_async import track

class StartCommand(TelegramBotCommand):

    name = 'start'

    async def execute(self, message: Message):
        await track(message.user.id, message.raw)
        welcome_text = '''Welcome! It's bot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with bot.'''
        signin_button = {
            'text': 'Waiting for Evernote...',
            'url': self.bot.url,
        }
        inline_keyboard = {'inline_keyboard': [[signin_button]]}
        chat_id = message.chat.id
        msg = await self.bot.api.sendMessage(chat_id, welcome_text, json.dumps(inline_keyboard))
        # TODO: async
        user_id = message.user.id
        oauth_data = self.bot.evernote.get_oauth_data(user_id)

        StartSession.create(user_id=user_id, oauth_data=oauth_data)

        User.create(id=user_id,
                    telegram_chat_id=chat_id,
                    mode='multiple_notes',
                    places={},
                    username=message.user.username,
                    first_name=message.user.first_name,
                    last_name=message.user.last_name)

        signin_button['text'] = 'Sign in to Evernote'
        signin_button['url'] = oauth_data["oauth_url"]
        await self.bot.api.editMessageReplyMarkup(chat_id, msg['message_id'], json.dumps(inline_keyboard))
