import time

from motor.motor_asyncio import AsyncIOMotorClient

from settings import MONGODB_URI


class MetaModel(type):

    def __call__(cls, *args, **kwargs):
        instance = super(MetaModel, cls).__call__(*args, **kwargs)
        instance.db = AsyncIOMotorClient(MONGODB_URI)
        return instance


class Model(metaclass=MetaModel):

    collection = ''

    @classmethod
    async def find_one(cls, condition):
        db = cls.db.evernoterobot
        entry = await db[cls.collection].find_one(condition)
        return entry


class StartSession(Model):

    collection = 'start_sessions'

    def __init__(self, user_id, chat_id, oauth_data):
        self.created = time.time()
        self.user_id = user_id
        self.telegram_chat_id = chat_id
        self.oauth_token = oauth_data.oauth_token
        self.oauth_token_secret = oauth_data.oauth_token_secret
        self.oauth_url = oauth_data.oauth_url
        self.callback_key = oauth_data.callback_key

    async def save(self):
        data = {}
        for k, v in self.__dict__.items():
            data[k] = getattr(self, k)
        data['_id'] = data['user_id']
        db = self.db.evernoterobot
        await db.start_sessions.save(data)

    @classmethod
    async def find(cls, evernote_callback_key: str):
        db = cls.db.evernoterobot
        session = await db.start_sessions.find_one(
            {'callback_key': evernote_callback_key})
        if session:
            session['user_id'] = session['_id']
            del session['_id']
            return StartSession(session)


class User(Model):

    collection = 'users'

    def __init__(self, user_id, access_token, notebook_guid):
        self.user_id = user_id
        self.evernote_access_token = access_token
        self.notebook_guid = notebook_guid

    async def save(self):
        data = {}
        for k, v in self.__dict__.items():
            data[k] = getattr(self, k)
        data['_id'] = data['user_id']
        db = self.db.evernoterobot
        await db.users.save(data)
