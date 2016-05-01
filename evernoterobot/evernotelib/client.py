import hashlib
from evernotelib import EvernoteSdk
import evernote.edam.type.ttypes as Types


class EvernoteOauthData:

    def __init__(self, request_token, oauth_url, callback_key):
        self.oauth_url = oauth_url
        self.oauth_token = request_token['oauth_token']
        self.oauth_token_secret = request_token['oauth_token_secret']
        self.callback_key = callback_key


class EvernoteClient:

    def __init__(self, consumer_key, consumer_secret, oauth_callback,
                 sandbox=True):
        self.oauth_callback = oauth_callback
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.sandbox = sandbox
        self.sdk = EvernoteSdk(consumer_key=consumer_key,
                               consumer_secret=consumer_secret,
                               sandbox=sandbox)

    def get_request_token(self, callback_url):
        return self.sdk.get_request_token(callback_url)

    def get_authorize_url(self, request_token):
        return self.sdk.get_authorize_url(request_token)

    def get_access_token(self, oauth_token, oauth_token_secret,
                         oauth_verifier):
        return self.sdk.get_access_token(oauth_token, oauth_token_secret,
                                         oauth_verifier)

    async def get_access_token_async(self, oauth_token, oauth_token_secret,
                                     oauth_verifier):
        # TODO:
        pass

    def get_oauth_data(self, user_id):
        bytes_key = ('%s%s%s' % (self.consumer_key, self.consumer_secret,
                                 user_id)).encode()
        callback_key = hashlib.sha1(bytes_key).hexdigest()
        callback_url = "%(callback_url)s?key=%(key)s" % {
            'callback_url': self.oauth_callback,
            'key': callback_key,
        }
        request_token = self.get_request_token(callback_url)
        oauth_url = self.get_authorize_url(request_token)
        return EvernoteOauthData(request_token, oauth_url, callback_key)

    async def get_oauth_url_async(self, user_id):
        # with ThreadPoolExecutor(max_workers=1) as executor:
        #     future = executor.submit(pow, 323, 1235)
        #     print(future.result())
        pass

    def create_note(self, auth_token, text, title=None, files=None):
        if files is None:
            files = []
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        # user_store = sdk.get_user_store()
        note_store = sdk.get_note_store()
        note = Types.Note()
        note.title = title or ('%s...' % text[:25] if len(text) > 30 else text)

        attachments = []
        for filename in files:
            with open(filename, 'rb') as f:
                data_bytes = f.read()
                md5 = hashlib.md5()
                md5.update(data_bytes)
                data = Types.Data()
                data.size = len(data_bytes)
                data.bodyHash = md5.digest()
                data.body = data_bytes
            attachments.append('<en-media type="%(mime_type)s" hash="%(md5)s" />' % {
                    'mime_type': 'image/jpg',  # TODO:
                    'md5': md5.hexdigest(),
            })

        note.content = '<?xml version="1.0" encoding="UTF-8"?>' \
            '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">' \
            '<en-note>%(text)s%(attachments)s</en-note>' % {
                'text': text,
                'attachments': ''.join(attachments),
            }
        created_note = note_store.createNote(note)
        return created_note
