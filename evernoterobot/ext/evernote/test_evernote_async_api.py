import pytest
from ext.evernote.api import AsyncEvernoteApi
from ext.evernote.client import EvernoteClient, NoteContent
from settings import EVERNOTE


@pytest.mark.async_test
async def test_get_note():
    auth_token = EVERNOTE['access_token']
    api = AsyncEvernoteApi()
    notebook = await api.get_default_notebook(auth_token)
    assert notebook
    assert notebook.guid
    note = await api.new_note(auth_token, notebook.guid, 'Note created from auto test', 'Autotest note')
    assert note
    assert note.guid
    note = await api.get_note(auth_token, note.guid)
    assert note
    assert note.guid
