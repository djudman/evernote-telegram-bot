#!/usr/bin/env python3
import importlib.util
import os
import sys
import time
import unittest
from config import load_config
from telegram.models import TelegramUpdate


def build_test_data(update_id=None, message_id=None, date=None, from_id=None, chat_id=None, text=None):
    config = load_config()
    entities = []
    if text.startswith('/'):
        entities.append({
            'type': 'bot_command',
            'offset': 0,
            'length': len(text),
        })
    return {
        'update_id': update_id or '123',
        'message': {
            'message_id': message_id or 111,
            'date': date or int(time.time()),
            'from': {
                'id': from_id or 222,
                'is_bot': False,
                'first_name': 'Test',
            },
            'entities': entities,
            'chat': {
                'id': chat_id or config['telegram']['chat_id'],
                'type': 'private',
            },
            'text': text or '/start',
        },
    }


class TestCase(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.fixtures = {
            'start_command': build_test_data(text='/start'),
            'switch_mode_command': build_test_data(text='/switch_mode'),
            'switch_mode_text': build_test_data(text='One note'),
            'help_command': build_test_data(text='/help'),
            'simple_text': build_test_data(text='hello, world'),
        }

    def tearDown(self):
        pass


class MockMethod:
    def __init__(self, result=None):
        self.calls = []
        self.result = result

    def __call__(self, *args, **kwargs):
        call_data = {'args': args, 'kwargs': kwargs}
        self.calls.append(call_data)
        return self.result

    @property
    def call_count(self):
        return len(self.calls)


def import_module_by_path(path):
    spec = importlib.util.spec_from_file_location('test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_test_modules(pattern):
    test_modules = []
    if pattern.endswith('.py') and os.path.sep in pattern and os.path.exists(pattern):
        module = import_module_by_path(pattern)
        return [module]
    current_dir = os.path.dirname(os.path.realpath(__file__))
    for dirpath, _, filenames in os.walk(current_dir):
        for name in filenames:
            if name.startswith('test') and name.endswith('.py') and pattern in name.lower():
                path = os.path.join(dirpath, name)
                module = import_module_by_path(path)
                test_modules.append(module)
    return test_modules


if __name__ == '__main__':
    pattern = sys.argv[1].lower() if len(sys.argv) > 1 else ''
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for module in get_test_modules(pattern):
        suite.addTests(loader.loadTestsFromModule(module))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
