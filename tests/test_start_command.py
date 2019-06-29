import unittest

from evernotebot.bot.core import EvernoteBot

from config import bot_config
from mocks import TelegramApiMock, EvernoteClientMock
from storage import MemoryStorage


class TestStartCommad(unittest.TestCase):
    def test_start(self):
        user_id = 5
        update_data = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 123,
                "text": '/start',
                "entities": [{
                    "type": "bot_command",
                    "offset": 0,
                    "length": len("/start"),
                }],
                "from_user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": 9, "type": ""},
            },
        }
        bot = EvernoteBot(bot_config, storage=MemoryStorage())
        bot.api = TelegramApiMock()
        bot.evernote = EvernoteClientMock()
        bot.process_update(update_data)
        user_data = bot.storage.get(user_id)
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data["id"], 5)
        self.assertEqual(user_data["evernote"]["oauth"]["token"], "token")
        self.assertEqual(bot.api.sendMessage.call_count, 1)
        self.assertEqual(bot.api.editMessageReplyMarkup.call_count, 1)
        self.assertEqual(bot.evernote.get_oauth_data.call_count, 1)
