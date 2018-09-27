import unittest

from data.storage.fields import StringField
from data.storage.fields import StructField
from data.storage.model import Model
from data.storage.model import storage
from data.storage.storage import StorageMixin
from test import TestCase


class TestModel(Model):
    title = StringField()


@storage(provider='memory')
class TestMemoryModel(Model):
    title = StringField()


@storage(provider='mongo', db='test', collection='test')
class TestMongoModel(Model):
    title = StringField()


@storage(provider='mongo', db='test', collection='test')
class TestUnsetModel(Model):
    name = StringField()
    data = StructField(
        info=StructField(
            nickname=StringField()
        ),
        name=StringField(),
        surname=StringField()
    )

class TestApp(StorageMixin):
    pass


class TestStorage(TestCase):

    def check_storage(self, config, model_class):
        app = TestApp(config=config)
        storage = app.get_storage(model_class)
        model = storage.create_model({'title': 'Hello'})
        self.assertEqual(len(storage.get_all({})), 0)
        model.save()
        results = storage.get_all({})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, 'Hello')
        id1 = results[0].id
        model2 = storage.create_model({'title': 'Model 2'})
        model2.save()
        self.assertEqual(len(storage.get_all({})), 2)
        model1 = storage.get(id1)
        self.assertEqual(model1.id, id1)
        model1.delete()
        self.assertEqual(len(storage.get_all({})), 1)

    def test_default_provider(self):
        config = {
            'storage': {
                'providers': {
                    'memory': {
                        'class': 'data.storage.providers.MemoryProvider',
                        'default': True,
                    }
                }
            },
        }
        self.check_storage(config, TestModel)

    def test_memory_storage(self):
        config = {
            'storage': {
                'providers': {
                    'memory': {
                        'class': 'data.storage.providers.MemoryProvider',
                    }
                }
            },
        }
        self.check_storage(config, TestMemoryModel)

    @unittest.skip('TODO: clear test database before each test')
    def test_mongo_storage(self):
        config = {
            'storage': {
                'providers': {
                    'mongo': {
                        'class': 'data.storage.providers.MongoProvider',
                        'connection_string': 'mongodb://127.0.0.1:27017/?serverSelectionTimeoutMS=100',
                    }
                }
            },
        }
        self.check_storage(config, TestMongoModel)

    def test_unset_none_fields(self):
        config = {
            'storage': {
                'providers': {
                    'mongo': {
                        'class': 'data.storage.providers.MongoProvider',
                        'connection_string': 'mongodb://127.0.0.1:27017/',
                    }
                }
            },
        }
        app = TestApp(config=config)
        storage = app.get_storage(TestUnsetModel)
        model = storage.create_model({'id': 123})
        model.name = 'test'
        model.data.info.nickname = 'iv'
        model.data.name = 'Ivan'
        model.data.surname = 'Ivanov'
        model.save()
        self.assertEqual(model.id, 123)
        model.data.name = None
        model.data.info = None
        model.save()
        documents = storage.provider.get_all({'id': model.id})
        self.assertEqual(len(documents), 1)
        d = documents[0]
        self.assertEqual(d['name'], 'test')
        self.assertEqual(d['id'], 123)
        self.assertTrue('info' not in d['data'])
        self.assertTrue('name' not in d['data'])
        storage.provider.delete({'id': model.id})
