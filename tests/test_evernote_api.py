import unittest
from unittest import mock
from collections import namedtuple

import evernote.edam.type.ttypes as Types
import evernotebot.util.evernote.client as evernote_api
from evernotebot.util.evernote.client import EvernoteApi, EvernoteApiError

from mocks import EvernoteSdkMock


Notebook = namedtuple("Notebook", ["guid", "name"])


@mock.patch('evernotebot.util.evernote.client.EvernoteSdk',
            new_callable=EvernoteSdkMock)
class TestEvernoteApi(unittest.TestCase):
    def setUp(self):
        self.note_store = mock.Mock()
        self.config = {
            "access": {
                "basic": {"key": "key", "secret": "secret"}
            },
            "oauth_callback_url": "http://callback.url",
        }

    def test_get_oauth_data(self, sdk):
        data = evernote_api.get_oauth_data(1, "session_key", self.config)
        self.assertEqual(data["oauth_token"], "test_oauth_token")
        self.assertEqual(data["oauth_token_secret"], "test_oauth_secret")
        self.assertEqual(data["oauth_url"], "auth_url")
        sdk.assert_called_once_with(consumer_key="key",
            consumer_secret="secret", sandbox=False)
        callback_url = "http://callback.url?access=basic&key=2191f3da8abf9c31"\
                       "d9b64a887ffc5949ad0a35d4&session_key=session_key"
        sdk().get_request_token.assert_called_once_with(callback_url)
        request_token = {
            'oauth_token': 'test_oauth_token',
            'oauth_token_secret': 'test_oauth_secret'
        }
        sdk().get_authorize_url.assert_called_once_with(request_token)

    def test_get_oauth_data_when_get_request_token_failed(self, sdk):
        sdk().get_request_token = mock.Mock(side_effect=Exception("some error"))
        with self.assertRaises(EvernoteApiError) as ctx:
            evernote_api.get_oauth_data(1, "session_key", self.config)
        self.assertIsInstance(ctx.exception.__cause__, Exception)
        self.assertEqual(str(ctx.exception.__cause__), "some error")

    def test_get_oauth_data_when_get_authorize_url_failed(self, sdk):
        sdk().get_authorize_url = mock.Mock(side_effect=Exception("D'oh"))
        with self.assertRaises(EvernoteApiError) as ctx:
            evernote_api.get_oauth_data(1, "session_key", self.config)
        self.assertIsInstance(ctx.exception.__cause__, Exception)
        self.assertEqual(str(ctx.exception.__cause__), "D'oh")

    def test_get_access_token(self, sdk):
        token = evernote_api.get_access_token("api_key", "api_secret",
            sandbox=True, token="ouath_token", secret="oauth_secret",
            verifier="oauth_verifier")
        self.assertEqual(token, "access_token")
        sdk.assert_called_once_with(consumer_key="api_key",
            consumer_secret="api_secret", sandbox=True)
        sdk().get_access_token.assert_called_once_with('ouath_token',
            'oauth_secret', 'oauth_verifier')

    def test_get_all_notebooks(self, sdk):
        notebook1 = Notebook(guid="ABC", name="Notes")
        notebook2 = Notebook(guid="XXX", name="Personal")
        self.note_store().listNotebooks = mock.Mock(return_value=[notebook1, notebook2])
        sdk().get_note_store = self.note_store
        api = EvernoteApi("access_token")
        result = api.get_all_notebooks()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["guid"], "ABC")
        self.assertEqual(result[1]["guid"], "XXX")
        result = api.get_all_notebooks({"name": "Personal"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["guid"], "XXX")
        result = api.get_all_notebooks({"guid": "invalid"})
        self.assertEqual(len(result), 0)

    def test_get_default_notebook(self, sdk):
        default_notebook = Notebook(guid="default", name="Default")
        self.note_store().getDefaultNotebook = mock.Mock(return_value=default_notebook)
        sdk().get_note_store = self.note_store
        api = EvernoteApi("access_token")
        result = api.get_default_notebook()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["guid"], "default")

    def test_create_note(self, sdk):
        self.note_store().createNote = mock.Mock(return_value="created")
        sdk().get_note_store = self.note_store
        api = EvernoteApi("access_token")
        result = api.create_note("nb_guid", text="test text",
            html="<p>Test</p>",
            files=[{"path": "/etc/hosts", "name": "file.txt"}])
        self.assertEqual(result, "created")
        self.note_store().createNote.assert_called_once()
        call_args = self.note_store().createNote.call_args[0]
        self.assertEqual(len(call_args), 1)
        self.assertIsInstance(call_args[0], Types.Note)
        self.assertEqual(call_args[0].title, "Telegram bot")
        self.assertEqual(call_args[0].notebookGuid, "nb_guid")
        self.assertEqual(
            call_args[0].content,
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
            '<en-note><br />'
                '<div>test text</div>'
                '<p>Test</p><br />'
                '<en-media type="text/plain" hash="3350366d8d53bf5fe92a21020ae33d5b" />'
            '</en-note>')
        self.assertEqual(len(call_args[0].resources), 1)

    def test_update_note(self, sdk):
        content = '<?xml version="1.0" encoding="UTF-8"?>'\
            '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'\
            '<en-note><br />'\
                '<div>test text</div>'\
                '<p>Test</p><br />'\
            '</en-note>'
        note = Types.Note(guid="123", title="One big note", content=content)
        note.notebookGuid = "notebook"

        self.note_store().getNote = mock.Mock(return_value=note)
        self.note_store().createNote = mock.Mock(return_value=Types.Note(guid="new"))
        self.note_store().updateNote = mock.Mock(return_value="updated")
        sdk().get_note_store = self.note_store
        api = EvernoteApi("access_token")
        api.get_note_link = mock.Mock(return_value="http://evernote.com/123")
        result = api.update_note("123", text="Merry Christmas",
            title="Santa Claus",
            html="<p>New Year</p>",
            files=[{"path": "/etc/hosts", "name": "santa.jpg"}])
        self.assertEqual(result, "updated")
        self.note_store().createNote.assert_called_once()
        call_args = self.note_store().createNote.call_args[0]
        self.assertEqual(call_args[0].title, "Santa Claus")
        self.note_store().updateNote.assert_called_once()
        call_args = self.note_store().updateNote.call_args[0]
        self.assertEqual(len(call_args), 1)
        self.assertEqual(call_args[0].title, "One big note")
        self.assertEqual(call_args[0].notebookGuid, "notebook")
        self.assertEqual(
            call_args[0].content,
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
            '<en-note><br />'
                '<div>test text</div>'
                '<p>Test</p><br />'
                '<br /><div>Merry Christmas</div><p>New Year</p><br />'
                '<a href="http://evernote.com/123">santa.jpg</a>'
            '</en-note>')
