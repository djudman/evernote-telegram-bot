from data.storage.fields import StringField
from data.storage.model import Model
from data.storage.model import storage
from data.storage.storage import StorageMixin
from unittest import TestCase


class TestModel(Model):
    title = StringField()


@storage(provider='memory')
class TestMemoryModel(Model):
    title = StringField()


@storage(provider='mongo', db='test', collection='test')
class TestMongoModel(Model):
    title = StringField()


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
