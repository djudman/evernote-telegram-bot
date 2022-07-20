from unittest import TestCase

from evernotebot import EvernoteBot
from evernotebot.config import load_config


class TestStartCommand(TestCase):
    def setUp(self) -> None:
        config = load_config()
        self.bot = EvernoteBot(config)

    def test_base(self):
        data = {
            'update_id': 1,
            'message': {
                'message_id': 123,
                'from': {
                    'id': 14433,
                    'is_bot': False,
                    'first_name': 'Test',
                    'last_name': 'test',
                    'username': 'test_user',
                    'language_code': 'ru',
                },
                'chat': {
                    'id': 111,
                },
                'text': '/start',
                'entities': [{
                    'offset': 0,
                    'length': 6,
                    'type': 'bot_command',
                }],
            },
        }
        self.bot.process_update(data)
