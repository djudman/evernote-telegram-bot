import random


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
        self.sendMessage = MockMethod(result={"message_id": random.randint(1, 1000)})
        self.editMessageReplyMarkup = MockMethod()

    def __getattr__(self, name):
        self.history.append(name)


class EvernoteClientMock:
    def __init__(self):
        default_oauth_data = {
            "oauth_url": "oauth_url",
            "oauth_token": "token",
            "oauth_token_secret": "oauth_token_secret",
            "callback_key": "callback_key",
        }
        self.get_oauth_data = MockMethod(result=default_oauth_data)
