import unittest
import tempfile
from collections import namedtuple

from uhttp import Request

from evernotebot.bot.core import EvernoteBot
from evernotebot.wsgi import create_app, telegram_hook
from util.config import bot_config


class TestWsgi(unittest.TestCase):
    def test_telegram_hook_failed(self):
        bot = EvernoteBot(bot_config)
        app = namedtuple("App", ["bot"])(bot=bot)
        data = b'{"test": "abc"}'
        with tempfile.NamedTemporaryFile(mode="rb+", suffix=".txt",
                                         dir="/tmp") as wsgi_input:
            wsgi_input.write(data)
            wsgi_input.seek(0, 0)
            request = Request({
                'wsgi.input': wsgi_input,
                'CONTENT_LENGTH': len(data),
            })
            request.app = app
            self.assertEqual(len(list(iter(bot.failed_updates.get_all()))), 0)
            telegram_hook(request)
            failed_updates = list(iter(bot.failed_updates.get_all()))
            self.assertEqual(len(failed_updates), 1)
            self.assertEqual(failed_updates[0]["data"]["test"], "abc")
