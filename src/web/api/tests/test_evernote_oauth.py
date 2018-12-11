from web.api.handlers import evernote_oauth
from web.app import Application
from util.http import Request
from test import TestCase
from test import MockMethod


class TestEvernoteOauth(TestCase):
    def test_base(self):
        request = Request({'QUERY_STRING': 'key=secret&oauth_verifier=verifier&access=basic'})
        request.app = Application(self.config)
        request.app.bot.oauth_callback = MockMethod()
        response = evernote_oauth(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.headers[0][0], 'Location')
        method = request.app.bot.oauth_callback
        self.assertEqual(method.call_count, 1)
        args = method.calls[0]['args']
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0], 'secret')
        self.assertEqual(args[1], 'verifier')
        self.assertEqual(args[2], 'basic')
