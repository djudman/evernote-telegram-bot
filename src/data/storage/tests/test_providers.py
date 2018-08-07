import unittest
import random
from string import ascii_letters as letters
from data.storage.providers import MemoryProvider
from data.storage.providers import MongoProvider


class TestProviders(unittest.TestCase):
    def test_memory_provider(self):
        provider = MemoryProvider({})
        document1 = {'x': 1, 'version': 1}
        id1 = provider.insert(document1)
        self.assertEqual(provider.count(), 1)
        document2 = {'y': 1, 'version': 2}
        id2 = provider.insert(document2)
        self.assertEqual(provider.count(), 2)
        for document in provider.get_all({}):
            self.assertIsNotNone(document['id'])
        document3 = {'z': 1, 'version': 2}
        id3 = provider.insert(document3)
        document = provider.get({'version': 2})
        provider.update({'version': 2}, {'version': 1, 'x': 'x'})
        document = provider.get(id2)
        self.assertEqual(document['id'], id2)
        self.assertEqual(document['version'], 1)
        self.assertEqual(document['x'], 'x')
        self.assertEqual(document['y'], 1)
        document = provider.get(id3)
        self.assertEqual(document['id'], id3)
        self.assertEqual(document['version'], 1)
        self.assertEqual(document['x'], 'x')
        self.assertEqual(document['z'], 1)
        provider.delete({'id': id1})
        self.assertEqual(provider.count(), 2)
        id4 = provider.insert({'x': {'y': {'z': 123}}})
        document = provider.get({'x.y.z': 123})
        self.assertIsNotNone(document)
        provider.update({'x.y.z': 123}, {'x': 1})
        document = provider.get(id4)
        self.assertIsNotNone(document)

    def test_mongo_provider(self):
        random_name = "".join([random.choice(letters) for x in range(8)])
        config = {
            'connection_string': 'mongodb://127.0.0.1:27017/?serverSelectionTimeoutMS=100',
            'db': random_name,
            'collection': 'test',
        }
        provider = MongoProvider(config)
        document = {'x': 1, 'test': 1}
        id1 = provider.insert(document)
        self.assertIsNotNone(id1)
        document2 = {'x': 1, 'test': 2, 'id': 'zzz'}
        self.assertEqual(provider.insert(document2), 'zzz')
        self.assertEqual(provider.count({}), 2)
        provider.update({'x': 1}, {'z': 'z'})
        self.assertIsNotNone(provider.get(id1))
        for d in provider.get_all({}):
            self.assertEqual(d['z'], 'z')
        deleted_count = provider.delete({'id': id1})
        self.assertEqual(deleted_count, 1)
        self.assertEqual(provider.count({}), 1)
        provider.connection.exec_command(provider.db, 'dropDatabase')
