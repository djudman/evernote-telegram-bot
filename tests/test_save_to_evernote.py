import unittest
from time import time

from utelegram.models import Message

from config import bot_config
from evernotebot.bot.core import EvernoteBot
from evernotebot.bot.commands import start_command
from mocks import TelegramApiMock, EvernoteClientMock


class TestSaveToEvernote(unittest.TestCase):
    def setUp(self):
        bot = EvernoteBot(bot_config)
        bot.api = TelegramApiMock()
        bot.evernote = EvernoteClientMock()
        message = Message(
            message_id=1,
            date=time(),
            from_user={"id": 6, "is_bot": False, "first_name": "test"},
            chat={"id": 1, "type": "private"}
        )
        start_command(bot, message)
        bot.evernote_oauth_callback("callback_key", "oauth_verifier", "basic")
        self.bot = bot

    def test_save_text(self):
        user_id = 6
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
                "chat": {"id": 2, "type": "private"},
            },
        }
        self.bot.process_update(update_data)
