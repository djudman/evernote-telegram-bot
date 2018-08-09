from app import Application
from bot.commands import start_command
from bot.models import User
from util.http import Request
from telegram.models import TelegramUpdate
from test import MockMethod
from test import TestCase


class TestStartCommand(TestCase):
    def test_base(self):
        request = Request({})
        request.app = Application(self.config)
        request.app.bot.api.sendMessage = MockMethod(result={'message_id': 1})
        request.app.bot.api.editMessageReplyMarkup = MockMethod()
        data = self.fixtures['start_command']
        update = TelegramUpdate(data)
        start_command(request.app.bot, update.message)
        users = request.app.bot.get_storage(User).get_all({})
        self.assertEqual(len(users), 1)
        oauth = users[0].evernote.oauth
        self.assertIsNotNone(oauth.token)
        self.assertIsNotNone(oauth.secret)
        self.assertIsNotNone(oauth.url)
        self.assertIsNotNone(oauth.callback_key)
