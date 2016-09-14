import datetime
import importlib
import inspect
import uuid

import settings


class ModelNotFound(Exception):

    def __init__(self, query=None):
        message = ''
        if query:
            message = "Query: %s" % str(query)
        super(ModelNotFound, self).__init__(message)


class Model:

    storage = None

    def __init__(self, **kwargs):
        self.id = None
        if not hasattr(self, 'save_fields'):
            self.save_fields = []
        for arg_name, arg_value in kwargs.items():
            setattr(self, arg_name, arg_value)

    @classmethod
    def __get_storage(cls):
        collection = cls.__name__.lower()
        if cls.storage and cls.storage.collection == collection:
            return cls.storage
        storage_info = settings.STORAGE
        path = storage_info['class'].split('.')
        classname = str(path[-1:][0])
        module_name = ".".join(path[:-1])
        module = importlib.import_module(module_name)
        for name, klass in inspect.getmembers(module):
            if name == classname:
                cls.storage = klass(storage_info, collection=collection)
                return cls.storage
        raise Exception('Class {0} not found'.format(storage_info['class']))

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
    def find(cls, query: dict=None, sort=None, skip=None, limit=None):
        query = query or {}
        sort = sort or []
        return [cls(**doc) for doc in cls.__get_storage().find(query, sort, skip, limit)]

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


class StartSession(Model):

    save_fields = [
        'key',
        'data',
        'oauth_data',
        'created',
    ]

    def __init__(self, key, data: dict, oauth_data: dict, **kwargs):
        self.id = kwargs.get('id')
        self.key = key
        self.data = data
        self.oauth_data = oauth_data
        self.created = kwargs.get('created', datetime.datetime.now())


class TelegramUpdate(Model):

    save_fields = [
        'user_id',
        'request_type',
        'status_message_id',
        'created',
        'message',
    ]

    def __init__(self, user_id, request_type, status_message_id, message: dict, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = user_id
        self.request_type = request_type
        self.status_message_id = status_message_id
        self.message = message
        self.created = kwargs.get('created', datetime.datetime.now())

    def has_file(self):
        return self.request_type.lower() in ['photo', 'document', 'voice', 'video']


class FailedUpdate(TelegramUpdate):

    save_fields = [
        'user_id',
        'request_type',
        'status_message_id',
        'message',
        'failed_at',
        'error',
    ]

    def __init__(self, user_id, request_type, status_message_id, message, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = user_id
        self.request_type = request_type
        self.status_message_id = status_message_id
        self.message = message
        self.failed_at = kwargs.get('failed_at', datetime.datetime.now())
        self.error = kwargs.get('error')
        if 'error' not in self.save_fields:
            self.save_fields.append('error')


class DownloadTask(Model):

    save_fields = [
        'file_id',
        'file_size',
        'completed',
        'user_id',
        'mime_type',
        'file',
    ]

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.file_id = kwargs['file_id']
        self.file_size = kwargs.get('file_size')
        self.user_id = kwargs.get('user_id')
        self.completed = kwargs.get('completed', False)
        self.mime_type = kwargs.get('mime_type')
        self.file = kwargs.get('file')


class User(Model):

    save_fields = [
        'id',
        'telegram_chat_id',
        'state',
        'mode',
        'evernote_access_token',
        'current_notebook',
        'places',
        'name',
        'username',
        'settings',
        'last_request_time',
    ]

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.username = kwargs.get('username')
        self.last_request_time = kwargs.get('last_request_time', datetime.datetime.now())
        self.telegram_chat_id = kwargs['telegram_chat_id']
        self.state = kwargs.get('state')
        self.mode = kwargs.get('mode')
        self.places = kwargs.get('places')
        self.evernote_access_token = kwargs.get('evernote_access_token')
        self.current_notebook = kwargs.get('current_notebook')
        self.settings = kwargs.get('settings', {})
