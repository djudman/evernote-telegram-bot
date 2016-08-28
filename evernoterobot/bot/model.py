import datetime
import importlib
import inspect
import uuid

from settings import STORAGE


class ModelNotFound(Exception):

    def __init__(self, query=None):
        message = ''
        if query:
            message = "Query: %s" % str(query)
        super(ModelNotFound, self).__init__(message)


# class MetaModel(type):

    # def __call__(cls, *args, **kwargs):
    #     instance = super(MetaModel, cls).__call__(*args, **kwargs)
    #     if not hasattr(cls, '__storage'):
    #         path = STORAGE['class'].split('.')
    #         classname = path[-1:][0]
    #         module_name = ".".join(path[:-1])
    #         module = importlib.import_module(module_name)
    #         for name, klass in inspect.getmembers(module):
    #             if name == classname:
        # cls.__storage = MongoClient(MONGODB_URI)
            # cls._db = cls._db_client.get_default_database()
        # if not hasattr(cls, '_cache'):
        #     cls._cache = Cache(host=MEMCACHED['host'], port=MEMCACHED['port'])
        # return instance


class Model:

    def __init__(self, **kwargs):
        self.id = None
        if not hasattr(self, 'save_fields'):
            self.save_fields = []
        for arg_name, arg_value in kwargs.items():
            setattr(self, arg_name, arg_value)

    @classmethod
    def __get_storage(cls):
        if hasattr(cls, 'storage'):
            return cls.storage
        path = STORAGE['class'].split('.')
        classname = str(path[-1:][0])
        module_name = ".".join(path[:-1])
        module = importlib.import_module(module_name)
        for name, klass in inspect.getmembers(module):
            if name == classname:
                cls.storage = klass(STORAGE, collection=classname.lower())
                return cls.storage
        raise Exception('Class {0} not found'.format(STORAGE['class']))

    @classmethod
    def create(cls, **kwargs):
        model = cls(**kwargs)
        model._created = datetime.datetime.now()
        if not hasattr(model, 'id'):
            model.id = str(uuid.uuid4())
        model.save()
        return model

    @classmethod
    def get(cls, query: dict):
        document = cls.__get_storage().get(query)
        if not document:
            raise ModelNotFound(query)
        return cls(**document)

    @classmethod
    def find(cls, query: dict=None, sort=None):
        query = query or {}
        sort = sort or []
        return [cls(**doc) for doc in cls.__get_storage().find(query, sort)]

    def save(self):
        self.__get_storage().save(self)

    def update(self, query: dict, new_values: dict):
        query['id'] = self.id
        document = self.__get_storage().update(query, new_values)
        if not document:
            raise ModelNotFound()
        return self.__class__(**document)

    def delete(self):
        self.__get_storage().delete(self)

    def save_data(self) -> dict:
        data = {}
        if 'id' not in self.save_fields:
            self.save_fields.append('id')
        for field in self.save_fields:
            if not hasattr(self, field):
                continue
            val = getattr(self, field)
            if isinstance(val, Model):
                data[field] = val.save_data()
            else:
                data[field] = val
        return data

            # @classmethod
    # def get_sorted(cls, num_entries=100, *, condition=None):
    #     cursor = cls._db[cls.collection].find(condition or {}).sort('created').limit(num_entries)
    #     return [cls(**entry) for entry in cursor]

    # @classmethod
    # def find_and_modify(cls, query=None, update=None):
    #     return cls._db[cls.collection].find_and_modify(
    #         query=query or {},
    #         update=update or {},
    #         sort={ 'created': 1 },
    #     )

    # @classmethod
    # def create(cls, **kwargs):
    #     if not kwargs.get('created'):
    #         kwargs['created'] = datetime.datetime.now()
    #     model = cls(**kwargs)
    #     return model.save()

    # def save(self) -> object:
    #     assert self.collection,\
    #            "You must set 'collection' class attribute in your subclass"
    #     data = {}
    #     for name, v in self.__dict__.items():
    #         if not name.startswith('_') or name == '_id':
    #             data[name] = getattr(self, name)
    #     self._id = self._db[self.collection].save(data)
    #     return self

    # def delete(self):
    #     self._db[self.collection].remove({'_id': self._id})


class StartSession(Model):

    save_fields = [
        'user_id',
        'oauth_data',
    ]

    def __init__(self, user_id, oauth_data: dict, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = user_id
        self.oauth_data = oauth_data


class TelegramUpdate(Model):

    save_fields = [
        'user_id',
        'request_type',
        'status_message_id',
        'created',
        'data'
    ]

    def __init__(self, user_id, request_type, status_message_id, data: dict, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = user_id
        self.request_type = request_type
        self.status_message_id = status_message_id
        self.data = data
        self.created = kwargs.get('created', datetime.datetime.now())


class DownloadTask(Model):

    save_fields = [
        'file_id',
        'file_size',
        'completed',
        'user_id',
    ]

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.file_id = kwargs['file_id']
        self.file_size = kwargs['file_size']
        self.user_id = kwargs.get('user_id')
        self.completed = kwargs.get('completed', False)


class User(Model):

    save_fields = [
        'id',
        'telegram_chat_id',
        'state',
        'mode',
        'evernote_access_token',
        'current_notebook',
        'places',
    ]

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.telegram_chat_id = kwargs['telegram_chat_id']
        self.state = kwargs.get('state')
        self.mode = kwargs.get('mode')
        self.places = kwargs.get('places')
        self.evernote_access_token = kwargs.get('evernote_access_token')
        self.current_notebook = kwargs.get('current_notebook')
