import json
import unittest

from api.handlers import telegram_hook
from app import Application
from config import load_config
from util.http import Request
from test import TestCase
from test import MockMethod


class TestTelegramHook(TestCase):
    def test_base(self):
        request = Request({})
        request.app = Application(self.config)
        request.app.bot.handle_telegram_update = MockMethod()
        data = self.fixtures['simple_text']
        request.body = json.dumps(data).encode()
        telegram_hook(request)
        method = request.app.bot.handle_telegram_update
        self.assertEqual(method.call_count, 1)
        arg = method.calls[0]['args'][0]
        self.assertEqual(arg.__class__.__name__, 'TelegramUpdate')
