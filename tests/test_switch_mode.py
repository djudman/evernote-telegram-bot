import unittest
from time import time

from utelegram.models import Message
from evernotebot.bot.core import EvernoteBot
from evernotebot.bot.commands import start_command
from evernotebot.bot.shortcuts import evernote_oauth_callback

from config import bot_config
from mocks import TelegramApiMock, EvernoteApiMock
from storage import MemoryStorage


class TestSwitchMode(unittest.TestCase):
    def setUp(self):
        bot = EvernoteBot(bot_config, storage=MemoryStorage())
        bot.api = TelegramApiMock()
        bot.evernote = EvernoteApiMock()
        message = Message(
            message_id=1,
            date=time(),
            from_user={"id": 8, "is_bot": False, "first_name": "test"},
            chat={"id": 1, "type": "private"}
        )
        start_command(bot, message)
        oauth_data =  bot.evernote._oauth_data
        evernote_oauth_callback(bot, oauth_data["callback_key"], "oauth_verifier", "basic")
        # creating new mocks because we want get a clean picture
        bot.api = TelegramApiMock()
        bot.evernote = EvernoteApiMock()
        self.bot = bot

    def test_switch_to_one_note_mode(self):
        user_id = 8
        update_data = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 123,
                "text": '/switch_mode',
                "entities": [{
                    "type": "bot_command",
                    "offset": 0,
                    "length": len("/switch_mode"),
                }],
                "from_user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": 9, "type": ""},
            },
        }
        self.bot.process_update(update_data)
        user_data = self.bot.storage.get(user_id)
        self.assertEqual(user_data["state"], "switch_mode")
        self.assertEqual(self.bot.api.sendMessage.call_count, 1)
        call = self.bot.api.sendMessage.calls[0]
        self.assertEqual(call["args"][1], "Please, select mode")
        update_data = {
            "update_id": 1,
            "message": {
                "message_id": 2,
                "date": time(),
                "text": 'One note',
                "from_user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "test",
                },
                "chat": {"id": 2, "type": "private"},
            },
        }
        self.assertEqual(self.bot.evernote.create_note.call_count, 0)
        self.bot.process_update(update_data)
        call = self.bot.api.sendMessage.calls[1]
        self.assertTrue(call["args"][1].startswith('To enable "One note" mode you have to allow'))
        oauth_data =  self.bot.evernote._oauth_data
        evernote_oauth_callback(self.bot, oauth_data["callback_key"], "oauth_verifier", "full")
        self.assertEqual(self.bot.evernote.create_note.call_count, 1)
        self.assertEqual(self.bot.evernote.get_note_link.call_count, 1)
