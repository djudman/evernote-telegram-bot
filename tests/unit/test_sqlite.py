import os
import unittest

from evernotebot.storage import Sqlite


class TestSqliteStorage(unittest.TestCase):
    def setUp(self):
        dirpath = '/tmp'
        db_name = 'test_db'
        self._filepath = os.path.join(dirpath, db_name)
        self.client = Sqlite('/tmp', collection='test_table', db_name=db_name)

    def tearDown(self) -> None:
        self.client.close()
        os.unlink(self._filepath)

    def test_create(self):
        object_id = self.client.create({'id': 11, 'x': 'test'})
        self.assertEqual(object_id, 11)
        object_id = self.client.create({'a': 'test'}, auto_generate_id=True)
        self.assertEqual(object_id, 12)
        with self.assertRaises(Exception) as e:
            self.client.create({'id': -3, 'z': 'test'})
            self.assertEqual(str(e), 'Invalid id `-3`. Id must be >= 0')
        object_id = self.client.create({'id': 10, 'z': 'test'})
        self.assertEqual(object_id, 10)
        object_id = self.client.create({'a': 'test'}, auto_generate_id=True)
        self.assertEqual(object_id, 13)

    def test_get(self):
        self.client.create({'id': 11, 'x': 'test'})
        data = self.client.get(11)
        self.assertEqual(data['x'], 'test')

    def test_get_all(self):
        data = list(self.client.get_all())
        self.assertFalse(data)
        self.client.create({'id': 11, 'x': 'test'})
        self.client.create({'x': 'test2'}, auto_generate_id=True)
        data = list(self.client.get_all())
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['id'], 11)
        self.assertEqual(data[1]['id'], 12)

    def test_save(self):
        self.client.create({'id': 11, 'x': 'test'})
        self.client.save({'id': 11, 'x': 'test-test', 'y': '+'})
        data = self.client.get(11)
        self.assertEqual(data['x'], 'test-test')
        self.assertEqual(data['y'], '+')
        with self.assertRaises(Exception) as e:
            self.client.save({'id': 12, 'y': '+'})
            self.assertEqual(str(e), 'Object `12` not found')

    def test_delete(self):
        self.client.create({'id': 11, 'x': 'test'})
        data = list(self.client.get_all())
        self.assertEqual(len(data), 1)
        self.client.delete(11)
        data = list(self.client.get_all())
        self.assertEqual(len(data), 0)
        with self.assertRaises(Exception) as e:
            self.client.delete(11)
            self.assertEqual(str(e), 'Object `11` not found')
        self.client.delete(11, check_deleted_count=False)
