from app import Application
from bot.commands import help_command
from bot.models import User
from util.http import Request
from telegram.models import TelegramUpdate
from test import MockMethod
from test import TestCase


class TestHelpCommand(TestCase):
    def test_base(self):
        request = Request({})
        request.app = Application(self.config)
        request.app.bot.api.sendMessage = MockMethod(result={'message_id': 1})
        data = self.fixtures['help_command']
        update = TelegramUpdate(data)
        help_command(request.app.bot, update.message)
        self.assertEqual(request.app.bot.api.sendMessage.call_count, 1)
        args = request.app.bot.api.sendMessage.calls[0]['args']
        text = args[1]
        self.assertTrue('You can send to bot:' in text)
