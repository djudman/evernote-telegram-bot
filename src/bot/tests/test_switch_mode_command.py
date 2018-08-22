from collections import namedtuple

from app import Application
from bot.commands import start_command
from bot.commands import switch_mode
from bot.commands import switch_mode_command
from bot.handlers.text import handle_text
from bot.models import User
from util.http import Request
from telegram.models import TelegramUpdate
from test import MockMethod
from test import TestCase


class TestSwitchNoteCommand(TestCase):
    def test_base(self):
        # TODO:
        request = Request({})
        request.app = Application(self.config)
        request.app.bot.api.sendMessage = MockMethod(result={'message_id': 1})
        request.app.bot.api.editMessageReplyMarkup = MockMethod()
        Note = namedtuple('Note', ['guid'])
        request.app.bot.evernote.create_note = MockMethod(result=Note(guid='guid:123'))
        data = self.fixtures['start_command']
        update = TelegramUpdate(data)
        start_command(request.app.bot, update.message)
        data = self.fixtures['switch_mode_command']
        update = TelegramUpdate(data)
        switch_mode_command(request.app.bot, update.message)
        data = self.fixtures['switch_mode_text']
        update = TelegramUpdate(data)
        handle_text(request.app.bot, update.message)
        users = request.app.bot.get_storage(User).get_all({})
        self.assertEqual(users[0].evernote.shared_note_id, 'guid:123')
        self.assertEqual(users[0].bot_mode, 'one_note')
        data = self.fixtures['simple_text']
        update = TelegramUpdate(data)
        handle_text(request.app.bot, update.message)
