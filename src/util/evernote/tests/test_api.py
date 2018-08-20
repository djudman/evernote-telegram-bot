from test import TestCase
from util.evernote.client import EvernoteClient


class TestApi(TestCase):
    def test_base(self):
        client = EvernoteClient()
        user_id = 123
        session_key = 'abc'
        evernote_config = self.config['evernote']
        data = client.get_oauth_data(user_id, session_key, evernote_config)
        self.assertIsNotNone(data['oauth_url'])
        self.assertIsNotNone(data['oauth_token'])
        self.assertIsNotNone(data['oauth_token_secret'])
        self.assertIsNotNone(data['callback_key'])
