import hashlib

from evernote.api.client import EvernoteClient as EvernoteSdk


class EvernoteClient:
    def __init__(self, sandbox):
        self.sandbox = sandbox

    def get_oauth_data(self, user_id, session_key, evernote_config):
        api_key = evernote_config['key']
        api_secret = evernote_config['secret']
        oauth_callback_url = evernote_config['oauth_callback_url']
        bytes_key = '{0}{1}{2}'.format(api_key, api_secret, user_id).encode()
        callback_key = hashlib.sha1(bytes_key).hexdigest()
        callback_url = "{callback_url}?key={key}&session_key={session_key}".format(
            callback_url=oauth_callback_url,
            key=callback_key,
            session_key=session_key
        )
        sdk = EvernoteSdk(consumer_key=api_key, consumer_secret=api_secret, sandbox=self.sandbox)
        request_token = sdk.get_request_token(callback_url)
        oauth_url = sdk.get_authorize_url(request_token)
        return {
            'oauth_url': oauth_url,
            'oauth_token': request_token['oauth_token'],
            'oauth_token_secret': request_token['oauth_token_secret'],
            'callback_key': callback_key,
        }
