from time import time

from evernotebot.bot.errors import EvernoteBotException
from evernotebot.bot.mixins.base import BaseMixin
from evernotebot.storage import Storage
from evernotebot.storage.models import User


def dict_merge(d1: dict, d2: dict):
    for k, v in d2.items():
        if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
            dict_merge(d1[k], d2[k])
        else:
            d1[k] = d2[k]


class UserMixin(BaseMixin):
    def __init__(self, config: dict):
        super(UserMixin, self).__init__(config)
        self.user: User = None
        self.current_user: User = None
        self._users = Storage('users', config['storage'])

    async def on_bot_stop(self):
        self._users.close()

    async def on_bot_update(self, update: dict):
        message = update.get('message') or update.get('channel_post')
        if not message:
            return
        from_user = message.get('from') or message.get('sender_chat')
        user = await self.storage.get(User, from_user['id'])
        if not user:
            user = User(
                id=from_user['id'],
                user_id=from_user['id'],
                chat_id=message['chat']['id'],
                first_name=from_user.get('first_name'),
                last_name=from_user.get('last_name'),
                username=from_user.get('username'),
                bot_mode='multiple_notes'
            )
        self.user = user

    async def on_message(self, message: dict):
        if self.user.created:
            return
        name = self.user.first_name or ''
        last_name = self.user.last_name or ''
        name = ' '.join([name, last_name, f'id = {self.user["user_id"]}'])
        text = f'Unregistered user {name}. You\'ve to send /start command to register'
        raise EvernoteBotException(text)

    async def save_user(self):
        if not self.user.created:
            self.user.created = time()
            self.user.bot_mode = self.config['default_mode']
            self.user.evernote_access = 'readonly'
        await self.storage.save([self.user])

    # def on_bot_update_finished(self):
        # self._users.close()

    def find_user(self, query: dict) -> dict:
        users = list(self._users.get_all(query))
        if not users:
            raise Exception(f'Cant find user with query `{query}`')
        user = users.pop()
        self.user = self._users.get(user['id'])
        return self.user
