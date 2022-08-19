class EvernoteApiMock():
    @staticmethod
    def get_oauth_data(
        user_id: int,
        app_key: str,
        app_secret: str,
        callback_url: str,
        access='basic',
        sandbox=False
    ):
        return {
            'callback_key': 'callback_key',
            'token': 'token',
            'secret': 'secret',
            'oauth_url': 'oauth_url',
        }
