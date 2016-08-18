import pytest
from ext.evernote.api import AsyncEvernoteApi
from ext.evernote.client import EvernoteClient, NoteContent
from settings import EVERNOTE


@pytest.mark.skip(reason='Broken')
@pytest.mark.async_test
async def test_get_note():
    auth_token = EVERNOTE['access_token']
    api = AsyncEvernoteApi()
    # notebook = await api.get_default_notebook(auth_token)
    # assert notebook
    # assert notebook.guid
    # note = await api.new_note(auth_token, notebook.guid, 'Note created from auto test', 'Autotest note')
    # assert note
    # assert note.guid
    note = await api.get_note(auth_token, 'e524d4d6-fb01-40b5-a2f0-19abb60ccf89')
    assert note
    assert note.guid
