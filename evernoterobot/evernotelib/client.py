import hashlib
from evernotelib import EvernoteSdk


class EvernoteClient:

    def __init__(self, consumer_key, consumer_secret, oauth_callback):
        self.oauth_callback = oauth_callback
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
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

    def get_oauth_url(self, user_id):
        bytes_key = ('%s%s%s' % (self.consumer_key, self.consumer_secret,
                                 user_id)).encode()
        key = hashlib.sha1(bytes_key).hexdigest()
        callback_url = "%(callback_url)s?key=%(key)s" % {
            'callback_url': self.oauth_callback,
            'key': key,
        }
        request_token = self.evernote.get_request_token(callback_url)
        oauth_token = request_token['oauth_token']
        oauth_token_secret = request_token['oauth_token_secret']
        oauth_url = self.get_authorize_url(request_token)
        return oauth_url

    async def get_oauth_url_async(self, user_id):
        # with ThreadPoolExecutor(max_workers=1) as executor:
        #     future = executor.submit(pow, 323, 1235)
        #     print(future.result())
        pass
