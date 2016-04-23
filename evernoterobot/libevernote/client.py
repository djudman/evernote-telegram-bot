from libevernote import EvernoteSdk


class Evernote:

    def __init__(self, consumer_key, consumer_secret):
        self.sdk = EvernoteSdk(consumer_key=consumer_key,
                               consumer_secret=consumer_secret,
                               sandbox=True)

    def get_oauth_url(self, callback_url):
        # TODO: cache oauth URL
        request_token = self.sdk.get_request_token(callback_url)
        return self.sdk.get_authorize_url(request_token)
