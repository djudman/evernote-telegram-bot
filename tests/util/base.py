import unittest

from evernotebot.config import load_config


class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bot_config = load_config()
        for name in ('users', 'failed_updates'):
            bot_config['storage'][name] = {'class': 'tests.util.storage.MemoryStorage'}
        self.config = bot_config
