import json
import unittest
import tempfile
from collections import namedtuple
from urllib.parse import urlencode
from unittest import mock

from uhttp import Request

from evernotebot.bot.core import EvernoteBot
from evernotebot.bot.models import BotUser, EvernoteOauthData
from evernotebot.web.views import telegram_hook, evernote_oauth
from util.config import bot_config


class TestWebViews(unittest.TestCase):
    def setUp(self):
        self._files = []
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


    def tearDown(self):
        list(map(lambda f: f.close(), self._files))

    def create_request(self, data):
        bot = EvernoteBot(bot_config)
        app = namedtuple("App", ["bot"])(bot=bot)
        bytes_data = json.dumps(data).encode()
        wsgi_input = tempfile.NamedTemporaryFile(mode="rb+", suffix=".txt",
                                                 dir="/tmp")
        wsgi_input.write(bytes_data)
        wsgi_input.seek(0, 0)
        self._files.append(wsgi_input)
        request = Request({
            'wsgi.input': wsgi_input,
            'CONTENT_LENGTH': len(bytes_data),
            'QUERY_STRING': urlencode(data),
        })
        request.app = app
        return request

    def test_telegram_hook_failed(self):
        request = self.create_request({"test": "abc"})
        bot = request.app.bot
        self.assertEqual(len(list(iter(bot.failed_updates.get_all()))), 0)
        telegram_hook(request)
        failed_updates = list(iter(bot.failed_updates.get_all()))
        self.assertEqual(len(failed_updates), 1)
        self.assertEqual(failed_updates[0]["data"]["test"], "abc")

    def test_evernote_oauth_declined_auth(self):
        request = self.create_request({"key": "xxx"})
        bot = request.app.bot
        bot.api = mock.Mock()
        bot.api.sendMessage = mock.Mock()
        bot_user = BotUser(**self.default_user_data)
        bot_user.evernote.oauth = EvernoteOauthData(token="token",
            secret="secret", callback_key="xxx")
        bot.users.create(bot_user.asdict())
        evernote_oauth(request)
        bot.api.sendMessage.assert_called_once()
        self.assertEqual(bot.api.sendMessage.call_args[0][1],
            "We are sorry, but you have declined authorization.")
