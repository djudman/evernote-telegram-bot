from libevernote import EvernoteSdk


class Evernote:

    def __init__(self, consumer_key, consumer_secret):
        self.sdk = EvernoteSdk(consumer_key=consumer_key,
                               consumer_secret=consumer_secret,
                               sandbox=True)

    def get_request_token(self, callback_url):
        return self.sdk.get_request_token(callback_url)

    def get_authorize_url(self, request_token):
        return self.sdk.get_authorize_url(request_token)

    def get_access_token(self, oauth_token, oauth_verifier):
        return self.sdk.get_access_token(oauth_token, self.oauth_token_secret,
                                         oauth_verifier)
