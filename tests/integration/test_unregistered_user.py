from time import time
from evernotebot.bot.core import EvernoteBot, EvernoteBotException

from tests.util.base import TestCase
from tests.util.mocks import TelegramApiMock


class TestUnregisteredUser(TestCase):
    def setUp(self):
        bot = EvernoteBot(self.config)
        bot.api = TelegramApiMock()
        self.bot = bot

    def test_unregistered_user(self):
        user_id = 6
        chat_id = 3
        update_data = {
            "update_id": 1,
            "message": {
                "message_id": 2,
                "date": time(),
                "text": 'Hello, World!',
                "from_user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": chat_id, "type": "private"},
            },
        }
        with self.assertRaises(EvernoteBotException) as ctx:
            self.bot.process_update(update_data)
        self.assertEqual(str(ctx.exception), f"Unregistered user {user_id}. You've to send /start command to register")
        self.assertEqual(self.bot.api.sendMessage.call_count, 1)
        self.assertEqual(self.bot.api.sendMessage.calls[0]["args"][0], chat_id)
        self.assertEqual(self.bot.api.sendMessage.calls[0]["args"][1], f"❌ Error. Unregistered user {user_id}. You've to send /start command to register")
