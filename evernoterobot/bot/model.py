import datetime

from motor.motor_asyncio import AsyncIOMotorClient

from settings import MONGODB_URI


class ModelNotFound(Exception):

    def __init__(self, condition=None):
        message = ''
        if condition:
            message = "Condition: %s" % str(condition)
        super(ModelNotFound, self).__init__(message)


class MetaModel(type):

    def __call__(cls, *args, **kwargs):
        instance = super(MetaModel, cls).__call__(*args, **kwargs)
        if not hasattr(cls, '_db_client'):
            cls._db_client = AsyncIOMotorClient(MONGODB_URI)
            cls._db = cls._db_client.get_default_database()
        # if not hasattr(cls, '_cache'):
        #     cls._cache = Cache(host=MEMCACHED['host'], port=MEMCACHED['port'])
        return instance


class Model(metaclass=MetaModel):

    collection = None

    def __init__(self, **kwargs):
        for arg_name, arg_value in kwargs.items():
            setattr(self, arg_name, arg_value)

    @classmethod
    def __reconnect(cls):
        cls._db_client = AsyncIOMotorClient(MONGODB_URI)
        cls._db = cls._db_client.get_default_database()

    @classmethod
    async def find_one(cls, condition) -> dict:
        entry = await cls._db[cls.collection].find_one(condition)
        if not entry:
            raise ModelNotFound(condition)
        return entry

    @classmethod
    async def get(cls, condition: dict) -> object:
        data = await cls.find_one(condition)
        return cls(**data)

    @classmethod
    async def get_sorted(cls, num_entries=100, *, condition=None):
        entries = []
        cursor = cls._db[cls.collection].find(condition or {}).sort('created').limit(num_entries)
        while await cursor.fetch_next:
            data = cursor.next_object()
            entries.append(cls(**data))
        return entries

    @classmethod
    async def create(cls, **kwargs):
        if not kwargs.get('created'):
            kwargs['created'] = datetime.datetime.now()
        model = cls(**kwargs)
        return await model.save()

    async def save(self) -> object:
        assert self.collection,\
               "You must set 'collection' class attribute in your subclass"
        data = {}
        for name, v in self.__dict__.items():
            if not name.startswith('_') or name == '_id':
                data[name] = getattr(self, name)
        self._id = await self._db[self.collection].save(data)
        return self

    async def delete(self):
        await self._db[self.collection].remove({'_id': self._id})


class StartSession(Model):
    collection = 'start_sessions'


class TelegramUpdate(Model):
    collection = 'telegram_updates'


class DownloadTask(Model):
    collection = 'download_tasks'

    def __init__(self, **kwargs):
        super(DownloadTask, self).__init__(**kwargs)
        assert self.file_id
        assert self.completed is not None


class User(Model):

    collection = 'users'

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not hasattr(self, 'created'):
            self.created = datetime.datetime.now()
        self.state = kwargs.get('state')

Model()  # This is hack for initialization _db field
