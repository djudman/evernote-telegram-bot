import unittest
from unittest import mock

from evernotebot.util.evernote.client import EvernoteApi
from mocks import EvernoteSdkMock


@mock.patch('evernotebot.util.evernote.client.EvernoteSdk', new=EvernoteSdkMock)
class TestEvernoteApi(unittest.TestCase):
    def test_get_oauth_data(self):
        config = {
            "access": {
                "basic": {
                    "key": "key",
                    "secret": "secret",
                }
            },
            "oauth_callback_url": "oauth_callback_url",
        }
        data = EvernoteApi.get_oauth_data(1, "session_key", config)
        self.assertEqual(data["oauth_token"], "test")
        self.assertEqual(data["oauth_token_secret"], "secret")
        self.assertEqual(data["oauth_url"], "https://")
