import json
import unittest

from api.handlers import telegram_hook
from app import Application
from config import load_config
from util.http import Request


class TestTelegramHook(unittest.TestCase):
    def test_run(self):
        config = load_config()
        app = Application(config)
        request = Request({
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/{0}'.format(config['telegram']['token']),
        })
        request.app = app
        data = {
            'update_id': '123',
            'message': {
                'message_id': 111,
                'date': 123,
                'from': {
                    'id': 222,
                    'is_bot': False,
                    'first_name': 'Test',
                },
                'entities': [
                    {
                        'type': 'bot_command',
                        'offset': 0,
                        'length': 6,
                    },
                ],
                'chat': {
                    'id': config['telegram']['chat_id'],
                    'type': 'private',
                },
                'text': '/start',
            },
        }
        request.body = json.dumps(data).encode()
        telegram_hook(request)
