import unittest
from datetime import datetime

from config import load_config
from telegram.bot_api import BotApi


class TestBotApi(unittest.TestCase):
    def setUp(self):
        config = load_config()
        token = config['telegram']['token']
        self.api = BotApi(token)
        self.chat_id = config['telegram']['chat_id']

    @unittest.skip('Sends message to telegram. Uncomment when it needs')
    def test_send_message(self):
        text = '{} - Hello from test'.format(datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
        response = self.api.sendMessage(self.chat_id, text)
        self.assertIsNotNone(response.get('message_id'))
        self.assertIsNotNone(response.get('from'))
        self.assertIsNotNone(response.get('chat'))
        self.assertIsNotNone(response.get('date'))
        self.assertEqual(response.get('text'), text)
