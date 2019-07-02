import unittest
from unittest import mock

from evernotebot.bot.core import EvernoteBot
from evernotebot.bot.models import BotUser

from config import bot_config
from mocks import EvernoteSdkMock


class TestCore(unittest.TestCase):
    def setUp(self):
        self.default_user_data = {
            "id": 2,
            "created": 123,
            "last_request_ts": 123,
            "bot_mode": "multiple_notes",
            "telegram": {
                "first_name": "Bob",
                "last_name": None,
                "username": None,
                "chat_id": 1,
            },
            "evernote": {
                "access": {"token": "access_token", "permission": "basic"},
                "notebook": {"name": "xxx", "guid": "xxx"}
            },
        }

    @mock.patch('evernotebot.util.evernote.client.EvernoteSdk',
                new_callable=EvernoteSdkMock)
    def test_get_evernote_api_object(self, sdk):
        bot = EvernoteBot(bot_config)
        api = bot.evernote()
        self.assertIsNotNone(api)
        self.assertTrue("default" in bot._evernote_apis_cache)
        bot_user = BotUser(**self.default_user_data)
        api = bot.evernote(bot_user)
        self.assertIsNotNone(api)
        self.assertEqual(len(bot._evernote_apis_cache), 2)
        self.assertTrue(bot_user.id in bot._evernote_apis_cache)
        for i in range(110):
            self.default_user_data["id"] = i
            bot_user = BotUser(**self.default_user_data)
            api = bot.evernote(bot_user)
            self.assertIsNotNone(api)
        self.assertEqual(len(bot._evernote_apis_cache), 100)
        self.assertFalse("default" in bot._evernote_apis_cache)
        self.assertFalse(1 in bot._evernote_apis_cache)
