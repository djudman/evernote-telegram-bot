import datetime
import hashlib
import mimetypes
import logging
import re

import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient as EvernoteSdk


class EvernoteApiError(Exception):
    pass


class NoteContent:
    def __init__(self, content=''):
        if not isinstance(content, str):
            raise Exception('Content must have `string` type')
        self.content = self.parse(content)
        self.resources = []

    def parse(self, content):
        matched = re.search(r'<en-note>(?P<content>.*)</en-note>', content)
        if not matched:
            return ''
        return matched.group('content')

    def make_resource(self, file_info):
        with open(file_info['path'], 'rb') as f:
            data_bytes = f.read()
        md5 = hashlib.md5()
        md5.update(data_bytes)

        data = Types.Data()
        data.size = len(data_bytes)
        data.bodyHash = md5.digest()
        data.body = data_bytes

        name = file_info['name']
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

    def append(self, *, text='', html='', file=None):
        new_content = ''
        if text:
            text = text.replace('&', '&amp;')
            text = text.replace('>', '&gt;')
            text = text.replace('<', '&lt;')
            new_content += '<div>{}</div>'.format(text)
        if html:
            new_content += html
        if file:
            resource_data = self.make_resource(file)
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
    def __init__(self, sandbox=False):
        self.sandbox = False

    def get_oauth_data(self, user_id, session_key, evernote_config, access='basic'):
        access_config = evernote_config['access'][access]
        api_key = access_config['key']
        api_secret = access_config['secret']
        bytes_key = '{0}{1}{2}'.format(api_key, api_secret, user_id).encode()
        callback_key = hashlib.sha1(bytes_key).hexdigest()
        callback_url = "{url}?access={access}&key={key}&session_key={session_key}".format(
            access=access,
            url=evernote_config['oauth_callback_url'],
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

    def get_note_store(self, token):
        sdk = EvernoteSdk(token=token, sandbox=self.sandbox)
        return sdk.get_note_store()

    def get_all_notebooks(self, token, query=None):
        note_store = self.get_note_store(token)
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
        note_store = self.get_note_store(token)
        notebook = note_store.getDefaultNotebook()
        return {
            'guid': notebook.guid,
            'name': notebook.name,
        }

    def create_note(self, token, notebook_guid, text=None, title=None, files=None, html=None):
        note = Types.Note()
        title = title.replace('\n', ' ')  # Evernote doesn't support \n in titles
        note.title = title or 'Telegram bot'
        note.notebookGuid = notebook_guid
        content = NoteContent()
        content.append(text=text, html=html)
        if files:
            for file in files:
                content.append(file=file)
        note.content = str(content)
        note.resources = content.resources
        note_store = self.get_note_store(token)
        return note_store.createNote(note)

    def update_note(self, token, note_guid, text=None, title=None, files=None, html=None):
        note = self.get_note(token, note_guid)
        content = NoteContent(note.content)
        content.append(text=text, html=html)
        if files:
            attachments_note = self.create_note(token, note.notebookGuid, '', 'Uploaded by Telegram bot', files)
            for file in files:
                link = '<a href="{url}">{filename}</a>'.format(url=self.get_note_link(token, attachments_note.guid), filename=file['name'])
                content.append(html=link)
        note.content = str(content)
        note_store = self.get_note_store(token)
        return note_store.updateNote(note)

    def get_note(self, token, note_guid, with_content=True, with_resources_data=True, with_resources_recognition=False, with_resources_alternate_data=False):
        note_store = self.get_note_store(token)
        return note_store.getNote(
            note_guid,
            with_content,
            with_resources_data,
            with_resources_recognition,
            with_resources_alternate_data
        )

    def get_note_link(self, auth_token, note_guid, app_link=False):
        user = self.get_user(auth_token)
        if not user:
            raise EvernoteApiError('User not found (token = {})'.format(auth_token))
        app_link_template = 'evernote:///view/{user_id}/{shard}/{note_guid}/{note_guid}/'
        web_link_template = 'https://{service}/shard/{shard}/nl/{user_id}/{note_guid}/'
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        params = {
            'service': sdk.service_host,
            'shard': user['shard_id'],
            'user_id': user['id'],
            'note_guid': note_guid,
        }
        if app_link:
            return app_link_template.format(**params)
        return web_link_template.format(**params)

    def get_user(self, auth_token):
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        user_store = sdk.get_user_store()
        user = user_store.getUser(auth_token)
        return {
            'id': user.id,
            'shard_id': user.shardId,
        }

    def get_quota_info(self, auth_token):
        sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
        user_store = sdk.get_user_store()
        note_store = self.get_note_store(auth_token)
        user = user_store.getUser()
        state = note_store.getSyncState()
        total_monthly_quota = user.accounting.uploadLimit
        used_so_far = state.uploaded
        quota_remaining = total_monthly_quota - used_so_far
        reset_date = datetime.datetime.fromtimestamp(user.accounting.uploadLimitEnd / 1000.0)
        return {
            'remaining': quota_remaining,
            'reset_date': reset_date, 
        }
