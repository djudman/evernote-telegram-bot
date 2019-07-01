import unittest
from unittest import mock

from evernotebot.util.evernote.client import EvernoteApi
from mocks import EvernoteSdkMock


@mock.patch('evernotebot.util.evernote.client.EvernoteSdk',
            new_callable=EvernoteSdkMock)
class TestEvernoteApi(unittest.TestCase):
    def test_get_oauth_data(self, sdk):
        config = {
            "access": {
                "basic": {"key": "key", "secret": "secret"}
            },
            "oauth_callback_url": "http://callback.url",
        }
        data = EvernoteApi.get_oauth_data(1, "session_key", config)
        self.assertEqual(data["oauth_token"], "test_oauth_token")
        self.assertEqual(data["oauth_token_secret"], "test_oauth_secret")
        self.assertEqual(data["oauth_url"], "auth_url")
        sdk.assert_called_once_with(consumer_key="key",
            consumer_secret="secret", sandbox=False)
        callback_url = "http://callback.url?access=basic&key=2191f3da8abf9c31"\
                       "d9b64a887ffc5949ad0a35d4&session_key=session_key"
        sdk().get_request_token.assert_called_once_with(callback_url)
        request_token = {
            'oauth_token': 'test_oauth_token',
            'oauth_token_secret': 'test_oauth_secret'
        }
        sdk().get_authorize_url.assert_called_once_with(request_token)

    def test_get_access_token(self, sdk):
        token = EvernoteApi.get_access_token("api_key", "api_secret",
            sandbox=True, token="ouath_token", secret="oauth_secret",
            verifier="oauth_verifier")
        self.assertEqual(token, "access_token")
        sdk.assert_called_once_with(consumer_key="api_key",
            consumer_secret="api_secret", sandbox=True)
        sdk().get_access_token.assert_called_once_with('ouath_token',
            'oauth_secret', 'oauth_verifier')
