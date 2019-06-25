import unittest

from evernotebot.bot.core import EvernoteBot
from mocks import TelegramApiMock, EvernoteClientMock
from config import bot_config


class TestStartCommad(unittest.TestCase):
    def test_start(self):
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
                    "id": 5,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": 9, "type": ""},
            },
        }
        bot = EvernoteBot(bot_config)
        bot.api = TelegramApiMock()
        bot.evernote = EvernoteClientMock()
        bot.process_update(update_data)
