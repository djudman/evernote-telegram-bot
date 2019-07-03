import datetime
import unittest
from unittest import mock

from utelegram.models import Message

from evernotebot.bot.core import EvernoteBot, EvernoteBotException
from evernotebot.bot.models import BotUser
from util.config import bot_config
from util.mocks import EvernoteSdkMock


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

    def test_switch_notebook(self):
        bot_user = BotUser(**self.default_user_data)
        bot = EvernoteBot(bot_config)
        bot.api = mock.Mock()
        bot.api.sendMessage = mock.Mock()
        bot.evernote = mock.Mock()
        all_notebooks = [
            {"guid": "xxx", "name": "xxx"},
            {"guid": "zzz", "name": "zzz"},
        ]
        bot.evernote().get_all_notebooks = lambda query: list(filter(lambda nb: nb["name"] == query["name"], all_notebooks))
        with self.assertRaises(EvernoteBotException) as ctx:
            bot.switch_notebook(bot_user, "> www <")
        self.assertEqual(str(ctx.exception), "Notebook 'www' not found")
        bot.switch_notebook(bot_user, "zzz")
        self.assertEqual(bot_user.evernote.notebook.name, "zzz")
        self.assertEqual(bot_user.evernote.notebook.guid, "zzz")
        bot.api.sendMessage.assert_called_once()
        bot.switch_notebook(bot_user, "xxx")
        self.assertEqual(bot_user.evernote.notebook.guid, "xxx")
        bot.switch_notebook(bot_user, "xxx")
        self.assertEqual(bot_user.evernote.notebook.guid, "xxx")

    def test_switch_mode(self):
        bot_user = BotUser(**self.default_user_data)
        bot = EvernoteBot(bot_config)
        with self.assertRaises(EvernoteBotException) as ctx:
            bot.switch_mode(bot_user, "invalid")
        self.assertEqual(str(ctx.exception), "Unknown mode 'invalid'")

        bot.api = mock.Mock()
        bot.api.sendMessage = mock.Mock()
        bot.switch_mode(bot_user, "multiple_notes")
        bot.api.sendMessage.assert_called_once_with(1,
            "The bot already in 'multiple_notes' mode.",
            "{\"hide_keyboard\": true}")

        bot.switch_mode_one_note = mock.Mock()
        bot.switch_mode(bot_user, "one_note")
        bot.switch_mode_one_note.assert_called_once()

        bot_user.bot_mode = "one_note"
        bot_user.evernote.shared_note_id = 123
        bot.api.sendMessage = mock.Mock()
        bot.switch_mode(bot_user, "multiple_notes")
        bot.api.sendMessage.assert_called_once_with(1,
            "The bot has switched to 'multiple_notes' mode.",
            "{\"hide_keyboard\": true}")
        self.assertIsNone(bot_user.evernote.shared_note_id)
        self.assertEqual(bot_user.bot_mode, "multiple_notes")

    def test_evernote_quota(self):
        bot = EvernoteBot(bot_config)
        bot.api = mock.Mock()
        bot.api.getFile = mock.Mock(return_value="https://google.com/robots.txt")
        bot.storage = mock.Mock()
        bot.storage.get = mock.Mock(return_value=self.default_user_data)
        bot.evernote = mock.Mock()
        now = datetime.datetime.now()
        bot.evernote().get_quota_info = mock.Mock(return_value={"remaining": 99, "reset_date": now})
        bot.save_note = mock.Mock()
        message = Message(
            message_id=1,
            date=1,
            document={"file_id": 123, "file_size": 100},
            from_user={"id": 2, "is_bot": False, "first_name": "John"},
            caption="My document",
        )
        with self.assertRaises(EvernoteBotException) as ctx:
            bot.on_document(message)
        self.assertTrue(str(ctx.exception).startswith("Your evernote quota is out"))

    def test_audio(self):
        bot = EvernoteBot(bot_config)
        bot.api = mock.Mock()
        bot.api.getFile = mock.Mock(return_value="https://google.com/robots.txt")
        bot.storage = mock.Mock()
        bot.storage.get = mock.Mock(return_value=self.default_user_data)
        bot.evernote = mock.Mock()
        bot.evernote().get_quota_info = mock.Mock(return_value={"remaining": 100})
        bot.save_note = mock.Mock()
        message = Message(
            message_id=1,
            date=1,
            voice={"file_id": 123, "file_size": 100, "duration": 5},
            from_user={"id": 2, "is_bot": False, "first_name": "John"},
            caption="My voice",
        )
        bot.on_audio(message)
        bot.api.getFile.assert_called_once()
        bot.evernote().get_quota_info.assert_called_once()
        bot.save_note.assert_called_once()

    def test_location(self):
        bot = EvernoteBot(bot_config)
        bot.storage = mock.Mock()
        bot.storage.get = mock.Mock(return_value=self.default_user_data)
        bot.save_note = mock.Mock()
        message = Message(
            message_id=1,
            date=1,
            from_user={"id": 2, "is_bot": False, "first_name": "John"},
            location = {"longitude": 1.2, "latitude": 3.4},
            venue = {
                "location": {"longitude": 1.2, "latitude": 3.4},
                "title": "Kremlin",
                "address": "Red Square, 1",
                "foursquare_id": "123",
            }
        )
        bot.on_location(message)
        bot.save_note.assert_called_once()
        user = bot.save_note.call_args[0][0]
        self.assertIsInstance(user, BotUser)
        title = bot.save_note.call_args[1]["title"]
        html = bot.save_note.call_args[1]["html"]
        self.assertEqual(title, "Kremlin")
        self.assertEqual(html, "Kremlin<br />Red Square, 1<br />"
        "<a href='https://maps.google.com/maps?q=3.4,1.2'>"
            "https://maps.google.com/maps?q=3.4,1.2"
        "</a><br />"
        "<a href='https://foursquare.com/v/123'>https://foursquare.com/v/123</a>")
