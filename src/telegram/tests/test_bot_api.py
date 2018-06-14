import unittest
from config import TELEGRAM
from datetime import datetime
from telegram.bot_api import BotApi


class TestBotApi(unittest.TestCase):
    def setUp(self):
        token = TELEGRAM['token']
        self.api = BotApi(token)
        self.chat_id = TELEGRAM['chat_id']

    def test_send_message(self):
        text = '{} - Hello from test'.format(datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
        response = self.api.sendMessage(self.chat_id, text)
        self.assertIsNotNone(response.get('message_id'))
        self.assertIsNotNone(response.get('from'))
        self.assertIsNotNone(response.get('chat'))
        self.assertIsNotNone(response.get('date'))
        self.assertEqual(response.get('text'), text)
