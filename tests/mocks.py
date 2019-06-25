import random


class TelegramApiMock:
    def __init__(self):
        self.history = []

    def __getattr__(self, name):
        self.history.append(name)

    def sendMessage(self, *args, **kwargs):
        return {
            "message_id": random.randint(1, 1000)
        }

    def editMessageReplyMarkup(self, *args, **kwargs):
        pass


class EvernoteClientMock:
    def get_oauth_data(self, user_id, session_key, evernote_config, access='basic'):
        return {
            "oauth_url": "oauth_url",
            "oauth_token": "token",
            "oauth_token_secret": "oauth_token_secret",
            "callback_key": "callback_key",
        }
