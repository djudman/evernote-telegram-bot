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
    def __init__(self, content: str=""):
        self.content = self.parse(content)
        self.resources = []

    def parse(self, content: str):
        matched = re.search(r"<en-note>(?P<content>.*)</en-note>", content)
        if not matched:
            return ""
        return matched.group("content")

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
            text = text.replace('\n', '<br />')
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
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"\
               "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">"\
               f"<en-note>{self.content}</en-note>"

    def __unicode__(self):
        return str(self)


def get_oauth_data(user_id, session_key, evernote_config, access="basic",
                   sandbox=False):
    access_config = evernote_config["access"][access]
    api_key = access_config["key"]
    api_secret = access_config["secret"]
    bytes_key = f"{api_key}{api_secret}{user_id}".encode()
    callback_key = hashlib.sha1(bytes_key).hexdigest()
    url=evernote_config["oauth_callback_url"]
    callback_url = f"{url}?access={access}&key={callback_key}&session_key={session_key}"
    sdk = EvernoteSdk(consumer_key=api_key, consumer_secret=api_secret, sandbox=sandbox)
    oauth_data = {"callback_key": callback_key}
    try:
        request_token = sdk.get_request_token(callback_url)
    except Exception as e:
        raise EvernoteApiError() from e
    if "oauth_token" not in request_token or "oauth_token_secret" not in request_token:
        raise EvernoteApiError("Can't obtain oauth token from Evernote")
    oauth_data["oauth_token"] = request_token["oauth_token"]
    oauth_data["oauth_token_secret"] = request_token["oauth_token_secret"]
    try:
        oauth_data["oauth_url"] = sdk.get_authorize_url(request_token)
    except Exception as e:
        raise EvernoteApiError() from e
    return oauth_data


def get_access_token(api_key, api_secret, sandbox=False, **oauth_kwargs):
    sdk = EvernoteSdk(consumer_key=api_key, consumer_secret=api_secret,
                        sandbox=sandbox)
    return sdk.get_access_token(oauth_kwargs["token"],
        oauth_kwargs["secret"], oauth_kwargs["verifier"])


class EvernoteApi:
    def __init__(self, access_token, sandbox=True):
        self._token = access_token
        self._sdk = EvernoteSdk(token=access_token, sandbox=sandbox)
        self._notes_store = self._sdk.get_note_store()

    def get_all_notebooks(self, query: dict=None):
        notebooks = self._notes_store.listNotebooks()
        notebooks = [{"guid": nb.guid, "name": nb.name} for nb in notebooks]
        if not query:
            return notebooks
        return list(
            filter(lambda nb: nb["guid"] == query.get("guid") \
                or nb["name"] == query.get("name"), notebooks)
        )

    def get_default_notebook(self):
        notebook = self._notes_store.getDefaultNotebook()
        return {
            'guid': notebook.guid,
            'name': notebook.name,
        }

    def create_note(self, notebook_id, text=None, title="Telegram bot", **kwargs):
        note = Types.Note()
        note.title = title.replace("\n", " ")  # Evernote doesn't support '\n' in titles
        note.notebookGuid = notebook_id
        content = NoteContent()
        content.append(text=text, html=kwargs.get("html"))
        if "files" in kwargs:
            list(map(lambda f: content.append(file=f), kwargs["files"]))
        note.content = str(content)
        note.resources = content.resources
        return self._notes_store.createNote(note)

    def update_note(self, note_id, text=None, title="Telegram bot", **kwargs):
        note = self.get_note(note_id)
        content = NoteContent(note.content)
        content.append(text=text, html=kwargs.get("html"))
        if "files" in kwargs:
            files = kwargs["files"]
            # We create new note for the files...
            attachments_note = self.create_note(note.notebookGuid, text="",
                title=title, files=files)
            # ...and put a link to this note into original note
            for file in files:
                url = self.get_note_link(attachments_note.guid)
                link = f"<a href=\"{url}\">{file['name']}</a>"
                content.append(html=link)
        note.content = str(content)
        return self._notes_store.updateNote(note)

    def get_note(self, note_guid, **kwargs):
        with_content = True
        with_resources_data = True,
        with_resources_recognition = False,
        with_resources_alternate_data = False
        return self._notes_store.getNote(note_guid, with_content,
            with_resources_data, with_resources_recognition,
            with_resources_alternate_data)

    def get_note_link(self, note_guid, app_link=False):
        user_store = self._sdk.get_user_store()
        user = user_store.getUser(self._token)
        user_id = user.id
        user = {"id": user_id, "shard_id": user.shardId}
        service = self._sdk.service_host
        shard = user["shard_id"]
        if app_link:
            return f"evernote:///view/{user_id}/{shard}/{note_guid}/{note_guid}/"
        return f"https://{service}/shard/{shard}/nl/{user_id}/{note_guid}/"

    def get_quota_info(self):
        user_store = self._sdk.get_user_store()
        user = user_store.getUser()
        state = self._notes_store.getSyncState()
        total_monthly_quota = user.accounting.uploadLimit
        used_so_far = state.uploaded
        quota_remaining = total_monthly_quota - used_so_far
        reset_date = datetime.datetime.fromtimestamp(
            user.accounting.uploadLimitEnd / 1000.0)
        return {
            "remaining": quota_remaining,
            "reset_date": reset_date, 
        }
