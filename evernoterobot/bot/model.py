import datetime

from pymongo import MongoClient

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
            cls._db_client = MongoClient(MONGODB_URI)
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
    def find_one(cls, query) -> dict:
        entry = cls._db[cls.collection].find_one(query)
        if not entry:
            raise ModelNotFound(query)
        return entry

    @classmethod
    def get(cls, query: dict):
        data = cls.find_one(query)
        return cls(**data)

    @classmethod
    def get_sorted(cls, num_entries=100, *, condition=None):
        cursor = cls._db[cls.collection].find(condition or {}).sort('created').limit(num_entries)
        return [cls(**entry) for entry in cursor]

    @classmethod
    def find_and_modify(cls, query=None, update=None):
        return cls._db[cls.collection].find_and_modify(
            query=query or {},
            update=update or {},
            sort={ 'created': 1 },
        )

    @classmethod
    def create(cls, **kwargs):
        if not kwargs.get('created'):
            kwargs['created'] = datetime.datetime.now()
        model = cls(**kwargs)
        return model.save()

    def save(self) -> object:
        assert self.collection,\
               "You must set 'collection' class attribute in your subclass"
        data = {}
        for name, v in self.__dict__.items():
            if not name.startswith('_') or name == '_id':
                data[name] = getattr(self, name)
        self._id = self._db[self.collection].save(data)
        return self

    def delete(self):
        self._db[self.collection].remove({'_id': self._id})


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
