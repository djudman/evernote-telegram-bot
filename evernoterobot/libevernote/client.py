from libevernote import EvernoteSdk


class Evernote:

    def __init__(self, consumer_key, consumer_secret):
        self.sdk = EvernoteSdk(consumer_key=consumer_key,
                               consumer_secret=consumer_secret,
                               sandbox=True)
        self.oauth_url = None

    def get_oauth_url(self, callback_url):
        if not self.oauth_url:
            request_token = self.sdk.get_request_token(callback_url)
            self.oauth_url = self.sdk.get_authorize_url(request_token)
        return self.oauth_url
