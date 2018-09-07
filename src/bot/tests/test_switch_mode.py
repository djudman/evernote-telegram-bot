from collections import namedtuple

from api.handlers import evernote_oauth
from app import Application
from bot.commands import start_command
from bot.commands import switch_mode_command
from bot.handlers.text import handle_text
from bot.models import User
from telegram.models import TelegramUpdate
from test import MockMethod
from test import TestCase
from util.http import Request


class TestSwitchNote(TestCase):
    def test_base(self):
        request = Request({})
        request.app = Application(self.config)
        request.app.bot.api.sendMessage = MockMethod(result={'message_id': 1})
        request.app.bot.api.editMessageReplyMarkup = MockMethod()
        update = TelegramUpdate(self.fixtures['start_command'])
        start_command(request.app.bot, update.message)
        self.assertEqual(request.app.bot.api.sendMessage.call_count, 1)
        self.assertEqual(request.app.bot.api.editMessageReplyMarkup.call_count, 1)

        update = TelegramUpdate(self.fixtures['switch_mode_command'])
        switch_mode_command(request.app.bot, update.message)
        users = request.app.bot.get_storage(User).get_all({})
        user_id = users[0].id
        callback_key = users[0].evernote.oauth.callback_key
        self.assertEqual(users[0].state, 'switch_mode')
        self.assertEqual(request.app.bot.api.sendMessage.call_count, 2)
        self.assertEqual(request.app.bot.api.editMessageReplyMarkup.call_count, 1)

        fake_oauth_data = {
            'oauth_url': 'url',
            'oauth_token': 'token',
            'oauth_token_secret': 'secret',
            'callback_key': callback_key,
        }
        request.app.bot.evernote.get_oauth_data = MockMethod(result=fake_oauth_data)
        update = TelegramUpdate(self.fixtures['one_note_mode_text'])
        request.app.bot.handle_message(update.message)
        self.assertEqual(request.app.bot.evernote.get_oauth_data.call_count, 1)
        self.assertEqual(request.app.bot.api.sendMessage.call_count, 4)
        user = request.app.bot.get_storage(User).get(user_id)
        self.assertEqual(user.state, '')
        self.assertEqual(user.bot_mode, 'multiple_notes')

        request.app.bot.evernote.get_access_token = MockMethod(result='token')
        request.app.bot.evernote.get_note_link = MockMethod()
        Note = namedtuple('Note', ['guid', 'content'])
        request.app.bot.evernote.create_note = MockMethod(result=Note(guid='guid:123', content=''))
        oauth_request = Request({'QUERY_STRING': 'key={key}&oauth_verifier=x&access=full'.format(key=callback_key)})
        oauth_request.app = request.app
        response = evernote_oauth(oauth_request)
        self.assertIsNotNone(response)
        self.assertEqual(request.app.bot.evernote.create_note.call_count, 1)
        user = request.app.bot.get_storage(User).get(user_id)
        self.assertEqual(user.bot_mode, 'one_note')
        self.assertEqual(user.evernote.shared_note_id, 'guid:123')

        # NOTE: try save text
        request.app.bot.api.editMessageText = MockMethod()
        request.app.bot.evernote.update_note = MockMethod(result=Note(content='', guid='guid:123'))
        data = self.fixtures['simple_text']
        update = TelegramUpdate(data)
        handle_text(request.app.bot, update.message)
        self.assertEqual(request.app.bot.evernote.update_note.call_count, 1)
        args = request.app.bot.evernote.update_note.calls[0]['args']
        self.assertTrue(args[1] == 'guid:123')
        self.assertEqual(request.app.bot.api.editMessageText.call_count, 1)
