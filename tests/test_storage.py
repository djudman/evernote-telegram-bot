import os
from pathlib import Path
from unittest import TestCase

from evernotebot.storage import Storage


class TestStorage(TestCase):
    def setUp(self) -> None:
        self.config = {
            'provider': 'evernotebot.storage.providers.sqlite.Sqlite',
            'dirpath': '/tmp/',
            'db_name': 'test',
        }
        self.clear()

    def tearDown(self) -> None:
        self.clear()

    def clear(self):
        filepath = Path(self.config['dirpath'], self.config['db_name'])
        if filepath.exists():
            os.unlink(filepath.resolve())

    def test_base(self):
        storage = Storage('test', self.config)
        object_id = storage.create({'id': 2, 'x': 123})
        self.assertEqual(object_id, 2)
        data = list(storage.get_all())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], {'id': 2, 'x': 123})
        object_id = storage.create({'y': 123})
        self.assertIsNotNone(object_id)
        data = list(storage.get_all())
        self.assertEqual(len(data), 2)
        self.assertEqual(data[1], {'id': object_id, 'y': 123})
        storage.delete(object_id)
        data = list(storage.get_all())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], {'id': 2, 'x': 123})
        storage.save({'id': 2, 'x': 123, 'z': 'xxx'})
        object_data = storage.get(2)
        self.assertEqual(object_data, {'id': 2, 'x': 123, 'z': 'xxx'})
        storage.close()
        self.assertRaises(Exception, lambda: storage.get(2))
