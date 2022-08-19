import functools
import json
import random
import re
import string
from http.client import HTTPConnection
from urllib.parse import parse_qsl

import urllib3

from evernotebot.storage import Storage
from evernotebot.util.asgi import AsgiApplication
from tests.telegram.models import Chat, User


def validate_token(method):
    def wrapper(obj, token, *args, **kwargs):
        if not obj.users.get_all({'token': token}):
            return {'ok': False, 'error_code': -1, 'description': 'bot not found'}
        return method(obj, *args, **kwargs)
    return wrapper


class Api(AsgiApplication):
    def __init__(self, host: str, port: int):
        url_schema = (
            ('CREATE', r'^/user$', self.api_add_user),
            ('GET', r'^/user/(\d+)$', self.api_get_user),
            ('CREATE', r'^/user/(\d+)/chats$', self.api_create_chats),
            ('GET', r'^/user/(\d+)/chats$', self.api_get_chats),
            ('POST', r'^/chat/(\d+)/message$', self.api_chat_message),
            # ('GET', r'^/inbox$', self.api_inbox),
            # telegram bot api
            ('POST', r'^/bot([\w\d_-]+)/setWebhook$', self.bot_api_setWebhook),
            ('POST', r'^/bot([\w\d_-]+)/sendMessage$', self.bot_api_sendMessage),
            ('POST', r'^/bot([\w\d_-]+)/editMessageReplyMarkup', self.bot_api_editMessageReplyMarkup),
        )
        super().__init__(url_schema, bind=f'{host}:{port}')
        storage_config = {
            'provider': 'evernotebot.storage.providers.sqlite.Sqlite',
            'db_name': 'telegram_api',
            'dirpath': '/tmp/telegram-api/',
        }
        self.users = Storage('users', storage_config)
        self.bots = Storage('bots', storage_config)
        self.chats = Storage('chats', storage_config)

    def get_chat(self, chat_id: int) -> Chat:
        ids = self.chats.get(chat_id)['members']
        members = tuple(self.users.get(member_id) for member_id in ids)
        return Chat(chat_id, members)

    def api_add_user(self, request):
        data = request.json()
        user_id = data.get('user_id')
        if not user_id:
            while True:
                user_id = random.randint(1, 1000000)
                if not self.users.get(user_id):
                    break
        elif self.users.get(user_id):
            raise Exception(f'User `{user_id}` already exists')
        user_data = {
            'id': user_id,
            'user_id': user_id,
            'first_name': data.get('first_name', f'Client {user_id}'),
            'last_name': data.get('last_name', ''),
            'username': data.get('username', f'user_{user_id}'),
            'language_code': data.get('language_code', 'en')
        }
        if data.get('is_bot'):
            random_char = functools.partial(random.choice, string.ascii_letters)
            token = data.get('token') or ''.join([random_char() for _ in range(32)])
            user_data.update({
                'bot_name': data['bot_name'],
                'token': token,
                'is_bot': True
            })
        self.users.create(user_data)
        return user_data

    def api_get_user(self, user_id: int, request):
        user_id = int(user_id)
        return self.users.get(user_id)

    def get_user(self, user_id: int) -> User:
        return User(**self.users.get(user_id))

    def api_create_chats(self, user_id: int, request):
        user_id = int(user_id)
        for user_data in self.users.get_all():
            if user_id == user_data['id']:
                continue
            chat_id = random.randint(1, 1000000)
            self.chats.create({
                'id': chat_id,
                'chat_id': chat_id,
                'members': [user_id, int(user_data['id'])],
            })
        return {'chats': list(self.chats.get_all())}

    def api_get_chats(self, user_id, request):
        user_id = int(user_id)
        out = {}
        for chat in self.chats.get_all():
            members = chat['members'].copy()
            members.remove(user_id)
            uid = members.pop()
            out[chat['id']] = {
                'chat_id': chat['id'],
                'user': self.users.get(uid),
            }
        return {'chats': out}

    def next_message_id(self, chat_id: int) -> int:
        chat_data = self.chats.get(chat_id)
        message_id = chat_data.get('last_message_id')
        if message_id is None:
            message_id = 1
        else:
            message_id += 1
        chat_data['last_message_id'] = message_id
        self.chats.save(chat_data)
        return message_id

    def api_chat_message(self, chat_id, request):
        chat_id = int(chat_id)
        message_id = self.next_message_id(chat_id)
        out = {'message_id': message_id}
        data = request.json()
        from_user = self.get_user(data['from'])
        text = data['text']
        for user in self.get_chat(chat_id).members:
            if user.user_id == from_user.user_id:
                continue
            if user.is_bot:
                self.update_bot(user, from_user, chat_id, message_id, text)
            else:
                out['send_to'] = user.user_id
        return out

    def update_bot(self, bot: User, from_user: User, chat_id: int, message_id: int, text: str):
        if not bot.webhook_url:
            return
        update_data = {
            'update_id': message_id,
            'message': {
                'message_id': message_id,
                'from': {
                    'id': from_user.user_id,
                    'is_bot': False,
                    'first_name': from_user.first_name,
                    'last_name': from_user.last_name,
                    'username': from_user.username,
                    'language_code': from_user.language_code,
                },
                'chat': {
                    'id': chat_id,
                },
                'text': text,
            },
        }
        entities = self.parse_entities(text)
        if entities:
            update_data['message']['entities'] = entities
        url = urllib3.util.parse_url(bot.webhook_url)
        conn = HTTPConnection(url.host, url.port)  # HTTPConnection used because we run bot on 127.0.0.1
        try:
            body = json.dumps(update_data).encode()
            conn.request('POST', url.path, body)
            response = conn.getresponse()
            response_bytes = response.read()
            if response.status != 200:
                raise Exception(response_bytes.decode())
        finally:
            conn.close()

    def parse_entities(self, text: str):
        '''
        entity struct:
            'offset': 0,
            'length': 6,
            'type': 'bot_command',
        '''
        entities = []
        pattern = re.compile(r'(^|\s)(/[a-zA-Z]+)(\s|$)')
        matched = re.match(pattern, text)
        if matched:
            for cmd in matched.groups():
                if not cmd:
                    continue
                offset = text.index(cmd)
                entities.append({
                    'type': 'bot_command',
                    'offset': offset,
                    'length': len(cmd),
                })
        return entities

    def bot_api_setWebhook(self, token, request):
        urlencoded_data = request.read()
        params = parse_qsl(urlencoded_data)
        data = {name.decode(): value for name, value in params}
        webhook_url = data['url'].decode()
        user = next(self.users.get_all({'token': token}))
        user['webhook_url'] = webhook_url
        self.users.save(user)
        return {'ok': True, 'result': webhook_url}

    @validate_token
    def bot_api_sendMessage(self, request):
        return {'ok': True, 'result': {'message_id': 12}}

    @validate_token
    def bot_api_editMessageReplyMarkup(self, request):
        return {'ok': True, 'result': {}}


if __name__ == '__main__':
    app = Api('127.0.0.1', 11000)
    app.run()
