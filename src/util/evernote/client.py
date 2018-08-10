import hashlib
import mimetypes
import logging
import re
from os.path import basename

import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient as EvernoteSdk


class EvernoteApiError(Exception):
    pass


class NoteContent:
    def __init__(self, content=None):
        self.content = self.parse(content)
        self.resources = []

    def parse(self, content):
        matched = re.search(r'<en-note>(?P<content>.*)</en-note>', content or '')
        if not matched:
            return ''
        return matched.group('content')

    def make_resource(self, filename):
        with open(filename, 'rb') as f:
            data_bytes = f.read()
        md5 = hashlib.md5()
        md5.update(data_bytes)

        data = Types.Data()
        data.size = len(data_bytes)
        data.bodyHash = md5.digest()
        data.body = data_bytes

        name = basename(filename)
        extension = name.split('.')[-1]
        mime_type = mimetypes.types_map.get('.{}'.format(extension), 'application/octet-stream')
        resource = Types.Resource()
        resource.mime = mime_type
        resource.data = data
        resource.attributes = Types.ResourceAttributes(fileName=name)
        return {
            'resource': resource,
            'mime_type': mime_type,
            'md5': md5.hexdigest(),
        }

    def append(self, *, text='', filename=None):
        new_content = ''
        if text:
            new_content += text.replace('&', '&amp;')
        if filename:
            resource_data = self.make_resource(filename)
            self.resources.append(resource_data['resource'])
            new_content += '<en-media type="{mime_type}" hash="{md5}" />'.format(
                mime_type=resource_data['mime_type'],
                md5=resource_data['md5']
            )
        if new_content:
            self.content += '<br />{0}'.format(new_content)


    def __str__(self):
        return '\
<?xml version="1.0" encoding="UTF-8"?>\
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">\
<en-note>{0}</en-note>'.format(self.content)

    def __unicode__(self):
        return str(self)


class EvernoteClient:
    def __init__(self, sandbox):
        self.sandbox = False

    def get_oauth_data(self, user_id, session_key, evernote_config, access='basic'):
        access_config = evernote_config['access'][access]
        api_key = access_config['key']
        api_secret = access_config['secret']
        bytes_key = '{0}{1}{2}'.format(api_key, api_secret, user_id).encode()
        callback_key = hashlib.sha1(bytes_key).hexdigest()
        callback_url = "{callback_url}?access={access}&key={key}&session_key={session_key}".format(
            access=access,
            callback_url=evernote_config['oauth_callback_url'],
            key=callback_key,
            session_key=session_key
        )
        sdk = EvernoteSdk(consumer_key=api_key, consumer_secret=api_secret, sandbox=self.sandbox)
        try:
            request_token = sdk.get_request_token(callback_url)
            if not request_token.get('oauth_token'):
                logging.getLogger().error('[X] EVERNOTE returns: {}'.format(request_token))
                raise EvernoteApiError("Can't obtain oauth token from Evernote")
            oauth_url = sdk.get_authorize_url(request_token)
        except Exception as e:
            raise EvernoteApiError(e)
        return {
            'oauth_url': oauth_url,
            'oauth_token': request_token['oauth_token'],
            'oauth_token_secret': request_token['oauth_token_secret'],
            'callback_key': callback_key,
        }

    def get_access_token(self, api_key, api_secret, oauth_token, oauth_token_secret, oauth_verifier):
        sdk = EvernoteSdk(consumer_key=api_key, consumer_secret=api_secret, sandbox=self.sandbox)
        return sdk.get_access_token(oauth_token, oauth_token_secret, oauth_verifier)

    def get_all_notebooks(self, token, query):
        sdk = EvernoteSdk(token=token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        notebooks = note_store.listNotebooks()
        notebooks = [{'guid': nb.guid, 'name': nb.name} for nb in notebooks]
        if not query:
            return notebooks
        # TODO: write better
        result = []
        for entry in notebooks:
            for k, v in query.items():
                if entry[k] != v:
                    break
            else:
                result.append(entry)
        return result

    def get_default_notebook(self, token):
        sdk = EvernoteSdk(token=token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        notebook = note_store.getDefaultNotebook()
        return {
            'guid': notebook.guid,
            'name': notebook.name,
        }

    def create_note(self, token, notebook_guid, text, title, files=None):
        note = Types.Note()
        note.title = title or 'Telegram bot'
        note.notebookGuid = notebook_guid
        content = NoteContent()
        content.append(text=text)
        if files:
            for name in files:
                content.append(filename=name)
                logging.getLogger().debug("Note content: {}".format(str(content)))
        note.content = str(content)
        note.resources = content.resources
        sdk = EvernoteSdk(token=token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        note_store.createNote(note)
