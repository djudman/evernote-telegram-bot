from app import Application
from bot.commands import start_command
from bot.models import User
from util.http import Request
from telegram.models import TelegramUpdate
from test import MockMethod
from test import TestCase


class TestStartCommand(TestCase):
    # NOTE: in this test we call Evernote API
    def test_base(self):
        request = Request({})
        request.app = Application(self.config)
        request.app.bot.api.sendMessage = MockMethod(result={'message_id': 1})
        request.app.bot.api.editMessageReplyMarkup = MockMethod()
        fake_oauth_data = {
            'oauth_url': 'url',
            'oauth_token': 'token',
            'oauth_token_secret': 'secret',
            'callback_key': 'key',
        }
        request.app.bot.evernote.get_oauth_data = MockMethod(result=fake_oauth_data)
        data = self.fixtures['start_command']
        update = TelegramUpdate(data)
        start_command(request.app.bot, update.message)
        self.assertEqual(request.app.bot.api.sendMessage.call_count, 1)
        users = request.app.bot.get_storage(User).get_all({})
        self.assertEqual(len(users), 1)
        oauth = users[0].evernote.oauth
        self.assertIsNotNone(oauth.token)
        self.assertIsNotNone(oauth.secret)
        self.assertIsNotNone(oauth.callback_key)
        self.assertEqual(request.app.bot.api.editMessageReplyMarkup.call_count, 1)
        self.assertEqual(request.app.bot.evernote.get_oauth_data.call_count, 1)
