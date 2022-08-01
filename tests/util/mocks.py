import random
import string
from collections import namedtuple
from unittest.mock import Mock


class MockMethod:
    def __init__(self, result=None):
        self.calls = []
        self.result = result

    def __call__(self, *args, **kwargs):
        call_data = {'args': args, 'kwargs': kwargs}
        self.calls.append(call_data)
        return self.result

    @property
    def call_count(self):
        return len(self.calls)


class TelegramApiMock:
    def __init__(self):
        self.history = []
        self.sendMessage = MockMethod(result={"message_id": random.randint(1, 1000)})  # nosec
        self.editMessageText = MockMethod()
        self.editMessageReplyMarkup = MockMethod()
        self.getFile = MockMethod(result="https://google.com/robots.txt")

    def __getattr__(self, name):
        self.history.append(name)


class EvernoteApiMock:
    def __init__(self):
        self._oauth_data = {
            "oauth_url": "oauth_url",
            "oauth_token": "token",
            "oauth_token_secret": "oauth_token_secret",
            "callback_key": self.__generate_secret_string(),
        }
        self.get_oauth_data = MockMethod(result=self._oauth_data)
        self.get_access_token = MockMethod(result="access_token")
        default_notebook = {"guid": "guid", "name": "Default"}
        self.get_default_notebook = MockMethod(result=default_notebook)
        Note = namedtuple("Note", "guid")
        self.create_note = MockMethod(result=Note(guid=self.__generate_secret_string()))
        self.update_note = MockMethod(result=Note(guid=self.__generate_secret_string()))
        quota_info = {"remaining": 1000}
        self.get_quota_info = MockMethod(result=quota_info)
        self.get_note_link = MockMethod()

    def __call__(self, *args, **kwargs):
        return self

    def __generate_secret_string(self):
        return ''.join(s for s in random.choices(string.ascii_letters, k=40))  # nosec


class EvernoteSdkMock(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_request_token = Mock(return_value={
            "oauth_token": "test_oauth_token",
            "oauth_token_secret": "test_oauth_secret",
        })
        self.get_authorize_url = Mock(return_value="auth_url")
        self.get_access_token = Mock(return_value="access_token")
