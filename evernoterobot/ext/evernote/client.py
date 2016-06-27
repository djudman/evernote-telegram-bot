import hashlib
import logging
import traceback
from os.path import basename
from ext.evernote import EvernoteSdk
import evernote.edam.type.ttypes as Types


class NoteContent:

    def __init__(self, note=None):
        self.content_objects = []
        self._old_content = ''
        self._old_resources = []
        if note is not None:
            self._old_resources = note.resources or []
            self._old_content = self._parse_content(note.content)
        self._new_content = ''

    def _parse_content(self, xml_content):
        pass

    def add_file(self, path, mime_type):
        resource, hexdigest = self._make_resource(path, mime_type)
        self.content_objects.append({
                'type': 'file',
                'path': path,
                'mime_type': mime_type,
                'resource': resource,
                'hexdigest': hexdigest,
            })

    def add_text(self, text):
        if text:
            self.content_objects.append({
                    'type': 'string',
                    'value': text,
                })

    def _make_resource(self, filename, mime_type):
        with open(filename, 'rb') as f:
            data_bytes = f.read()
            md5 = hashlib.md5()
            md5.update(data_bytes)

            data = Types.Data()
            data.size = len(data_bytes)
            data.bodyHash = md5.digest()
            data.body = data_bytes

            resource = Types.Resource()
            resource.mime = mime_type
            resource.data = data
            short_name = basename(filename)
            resource.attributes = Types.ResourceAttributes(fileName=short_name)
        return resource, md5.hexdigest()

    def get_resources(self):
        resources = [r for r in self._old_resources]
        for entry in self.content_objects:
            if entry['type'] == 'file':
                resources.append(entry['resource'])
        return resources

    def __str__(self):
        new_content = ''
        for entry in self.content_objects:
            content_entry = ''
            if entry['type'] == 'file':
                content_entry = '<br /><en-media type="%(mime_type)s" hash="%(md5)s" />' % {
                    'mime_type': entry['mime_type'],
                    'md5': entry['hexdigest'],
                }
            elif entry['type'] == 'string':
                content_entry = entry['value']
            new_content += content_entry

        return '<?xml version="1.0" encoding="UTF-8"?>' \
'<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">' \
'<en-note>%(old_content)s<br />%(new_content)s</en-note>' % {
                'old_content': self._old_content,
                'new_content': new_content,
            }


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
        return {
            'oauth_url': oauth_url,
            'oauth_token': request_token['oauth_token'],
            'oauth_token_secret': request_token['oauth_token_secret'],
            'callback_key': callback_key
        }

    async def get_oauth_url_async(self, user_id):
        # with ThreadPoolExecutor(max_workers=1) as executor:
        #     future = executor.submit(pow, 323, 1235)
        #     print(future.result())
        pass

    def create_note(self, auth_token, text, title=None, files=None,
                    notebook_guid=None):
        if files is None:
            files = []
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        # user_store = sdk.get_user_store()
        note_store = sdk.get_note_store()
        note = Types.Note()
        note.title = title or ('%s...' % text[:25] if len(text) > 30 else text)
        if notebook_guid is not None:
            note.notebookGuid = notebook_guid

        attachments = []
        for filename, mime_type in files:
            with open(filename, 'rb') as f:
                data_bytes = f.read()
                md5 = hashlib.md5()
                md5.update(data_bytes)

                data = Types.Data()
                data.size = len(data_bytes)
                data.bodyHash = md5.digest()
                data.body = data_bytes

                resource = Types.Resource()
                resource.mime = mime_type
                resource.data = data
                resource.attributes = Types.ResourceAttributes(fileName=basename(filename))

                # Now, add the new Resource to the note's list of resources
                note.resources = [resource]

            attachments.append('<br /><en-media type="%(mime_type)s" hash="%(md5)s" />' % {
                    'mime_type': mime_type,
                    'md5': md5.hexdigest(),
            })

        note.content = '<?xml version="1.0" encoding="UTF-8"?>' \
            '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">' \
            '<en-note>%(text)s<br />%(attachments)s</en-note>' % {
                'text': text,
                'attachments': ''.join(attachments),
            }
        try:
            created_note = note_store.createNote(note)
        except Exception as e:
            print(e)
            logging.getLogger().error(traceback.format_exc())
        return created_note.guid

    def getDefaultNotebook(self, auth_token):
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        return note_store.getDefaultNotebook()

    def getNotebook(self, auth_token, guid=None):
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        if guid is None:
            return note_store.getDefaultNotebook()
        return note_store.getNotebook(guid)

    def list_notebooks(self, auth_token):  # TODO: async version
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        # List all of the notebooks in the user's account
        return note_store.listNotebooks()

    def get_note(self, auth_token, note_guid):
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        return note_store.getNote(note_guid, True, True, False, False)

    def update_note(self, auth_token, guid, text, files=None):
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        note = note_store.getNote(guid, True, True, False, False)

        content = NoteContent(note)
        content.add_text(text)
        if files is not None:
            for filename, mime_type in files:
                content.add_file(filename, mime_type)

        note.resources = content.get_resources()
        note.content = str(content)

        note_store.update_note(note)
