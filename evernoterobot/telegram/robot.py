import logging
import asyncio
import json
from .api import BotApi
from libevernote.client import Evernote
from user import User
import session


class EvernoteRobot:

    def __init__(self, token, evernote_data):
        self.link = 'https://telegram.me/evernoterobot'
        self.api = BotApi(token)
        self.evernote_oauth_callback = evernote_data['oauth_callback']
        self.evernote = Evernote(evernote_data['key'], evernote_data['secret'])
        self.logger = logging.getLogger()
        # TODO: add cache

    async def handle_update(self, data):
        if 'message' in data:
            await self.handle_message(data['message'])
        elif 'inline_query' in data:
            # TODO: process inline query
            pass
        elif 'chosen_inline_result' in data:
            # TODO: process inline result
            pass
        elif 'callback_query' in data:
            # TODO: process callback query
            pass
        else:
            # TODO: unsupported update
            pass

    async def handle_message(self, message):
        self.chat_id = message['chat']['id']
        if message.get('from'):
            self.user = User(message.get('from'))

        commands = []
        for entity in message.get('entities', []):
            if entity['type'] == 'bot_command':
                offset = entity['offset']
                length = entity['length']
                cmd = message.get('text', '')[offset:length]
                if cmd.startswith('/'):
                    cmd = cmd.replace('/', '')
                commands.append(cmd)

        if commands:
            for cmd in commands:
                text = await self.execute_command(cmd)
                if isinstance(text, str):
                    await self.api.sendMessage(self.chat_id, text)
        else:
            text = message.get('text', '')
            await self.api.sendMessage(self.chat_id, text)

    async def execute_command(self, cmd):
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            if asyncio.iscoroutinefunction(func):
                text = await func()
            else:
                text = func()
        else:
            text = "Unsupported command '%s'" % cmd
            self.logger.warning(text)
        return text

    async def start(self):
        welcome_text = '''Hi! I'm robot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with me.'''
        signin_button = {
            'text': 'Preparing link for you...',
            'url': self.link,
        }
        inline_keyboard = [[signin_button]]
        message = await self.api.sendMessage(self.chat_id, welcome_text,
                                             json.dumps(inline_keyboard))
        # startsession = await session.get_start_session(self.user.id)
        # if not startsession:
        #     callback_key = self.get_callback_key(self.user.id)
        #     callback_url = "%(callback_url)s?key=%(key)s" % {
        #             'callback_url': self.evernote_oauth_callback,
        #             'key': callback_key,
        #         }
        #     request_token = self.evernote.get_request_token(callback_url)
        #     oauth_token = request_token['oauth_token']
        #     oauth_token_secret = request_token['oauth_token_secret']
        #     # TODO: put tokens to cache
        #     oauth_url = self.evernote.get_authorize_url(request_token)
        #     await session.save_start_session(self.user.id, oauth_url,
        #                                      callback_key)
        # else:
        #     oauth_url = startsession['oauth_url']

        signin_button['text'] = 'Sign in to Evernote'
        signin_button['url'] = 'oauth_url'
        await self.api.editMessageReplyMarkup(
            self.chat_id, message['message_id'], json.dumps(inline_keyboard))

    def get_callback_key(self, user_id):
        return "%s.%s" % (user_id, self.api.token)

    async def verify_callback_key(callback_key):
        return await session.get_start_session(sid=callback_key)

    def auth(self):
        # TODO:
        pass

    def logout(self):
        # TODO:
        pass

    def help(self):
        return '''
What is it?
- Bot for fast saving notes to Evernote
Contacts
- djudman@gmail.com'''
