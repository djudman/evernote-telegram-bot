from libevernote import EvernoteSdk


class Evernote:

    def __init__(self, consumer_key, consumer_secret):
        self.sdk = EvernoteSdk(consumer_key=consumer_key,
                               consumer_secret=consumer_secret,
                               sandbox=True)
        self.oauth_url = None
        self.oauth_token = None

    def get_oauth_url(self, callback_url):
        if not self.oauth_url:
            request_token = self.sdk.get_request_token(callback_url)
            self.oauth_token = request_token['oauth_token']
            self.oauth_token_secret = request_token['oauth_token_secret']
            self.oauth_url = self.sdk.get_authorize_url(request_token)
        return self.oauth_url

    def get_access_token(self, oauth_token, oauth_verifier):
        return self.sdk.get_access_token(oauth_token, self.oauth_token_secret,
                                         oauth_verifier)
