import hashlib
import logging
import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient as EvernoteSdk


class EvernoteApiError(Exception):
    pass


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
        note.title = title
        note.notebookGuid = notebook_guid
        note.content = text
        sdk = EvernoteSdk(token=token, sandbox=self.sandbox)
        note_store = sdk.get_note_store()
        note_store.createNote(note)
