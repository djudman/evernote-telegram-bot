import json

import asyncio

import settings
from bot.model import StartSession, User, ModelNotFound
from ext.telegram.bot import TelegramBotCommand
from ext.telegram.models import Message
from ext.botan_async import track

class StartCommand(TelegramBotCommand):

    name = 'start'

    async def execute(self, message: Message):
        chat_id = message.chat.id
        user_id = message.user.id
        asyncio.ensure_future(track(user_id, message.raw))
        config = settings.EVERNOTE['basic_access']

        welcome_text = '''Welcome! It's bot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with bot.'''
        signin_button = {
            'text': 'Waiting for Evernote...',
            'url': self.bot.url,
        }
        inline_keyboard = {'inline_keyboard': [[signin_button]]}
        welcome_message_future = asyncio.ensure_future(self.bot.api.sendMessage(chat_id, welcome_text, json.dumps(inline_keyboard)))
        oauth_data = await self.bot.evernote_api.get_oauth_data(
            user_id, config['key'], config['secret'], config['oauth_callback'])

        session_data = {
            'user': {
                'username': message.user.username,
                'first_name': message.user.first_name,
                'last_name': message.user.last_name,
            },
            'chat_id': chat_id,
        }
        StartSession.create(id=user_id, user_id=user_id, data=session_data, oauth_data=oauth_data)

        signin_button['text'] = 'Sign in to Evernote'
        signin_button['url'] = oauth_data["oauth_url"]
        await asyncio.wait([welcome_message_future])
        msg = welcome_message_future.result()
        asyncio.ensure_future(self.bot.api.editMessageReplyMarkup(chat_id, msg['message_id'], json.dumps(inline_keyboard)))
