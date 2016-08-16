import json

from bot.model import StartSession, User, ModelNotFound
from ext.telegram.bot import TelegramBotCommand


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
        msg = await self.bot.api.sendMessage(chat_id, welcome_text, json.dumps(inline_keyboard))
        # TODO: async
        user_id = message['from']['id']
        oauth_data = self.bot.evernote.get_oauth_data(user_id)

        try:
            session = await StartSession.get({'user_id': user_id})
            self.bot.logger.warn("Start session for user %s already exists" % user_id)
            session.oauth_data = oauth_data
            await session.save()
        except ModelNotFound:
            await StartSession.create(user_id=user_id, oauth_data=oauth_data)

        try:
            await User.get({'user_id': user_id})
            self.bot.logger.warn("User %s already exists" % user_id)
        except ModelNotFound:
            await User.create(user_id=user_id, telegram_chat_id=chat_id,
                              mode='one_note',
                              username=message['from'].get('username'),
                              first_name=message['from'].get('first_name'),
                              last_name=message['from'].get('last_name'))

        signin_button['text'] = 'Sign in to Evernote'
        signin_button['url'] = oauth_data["oauth_url"]
        await self.bot.api.editMessageReplyMarkup(chat_id, msg['message_id'], json.dumps(inline_keyboard))
