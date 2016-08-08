import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import settings
from ext.evernote.client import NoteContent, Types, ErrorTypes, EvernoteSdk


class EvernoteApiError(Exception):
    def __init__(self, description):
        super(EvernoteApiError, self).__init__(description)


class NoteNotFound(EvernoteApiError):
    pass


class AsyncEvernoteApi:

    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.sandbox = settings.DEBUG
        self.logger = logging.getLogger('evernote_api')

    async def get_note(self, auth_token, note_guid):
        def fetch(note_guid):
            self.logger.debug('Fetching note {0}'.format(note_guid))
            try:
                sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
                note_store = sdk.get_note_store()
                return note_store.getNote(note_guid, True, True, False, False)
            except ErrorTypes.EDAMNotFoundException:
                self.logger.error("Note {0} not found".format(note_guid))
                raise NoteNotFound("Note {0} not found".format(note_guid))
            except Exception as e:
                self.logger.error('API error')
                raise EvernoteApiError(str(e))

        return await self.loop.run_in_executor(self.executor, fetch, note_guid)

    async def save_note(self, auth_token, note):
        def save(note):
            self.logger.debug('Saving note...')
            try:
                sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
                note_store = sdk.get_note_store()
                return note_store.createNote(note)
            except Exception as e:
                raise EvernoteApiError(str(e))

        return await self.loop.run_in_executor(self.executor, save, note)

    async def new_note(self, auth_token, notebook_guid, text,
                       title=None, files=None):
        def create():
            note = Types.Note()
            note.title = title or ('%s...' % text[:25] if len(text) > 30 else text)
            note.notebookGuid = notebook_guid
            content = NoteContent(note)
            content.add_text(text)
            if files:
                for path, mime_type in files:
                    content.add_file(path, mime_type)
            note.resources = content.get_resources()
            note.content = str(content)
            try:
                sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
                note_store = sdk.get_note_store()
                return note_store.createNote(note)
            except Exception as e:
                raise EvernoteApiError(str(e))

        return await self.loop.run_in_executor(self.executor, create)

    async def update_note(self, auth_token, note):
        def update(note):
            self.logger.debug('Updating note {0}'.format(note.guid))
            try:
                sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
                note_store = sdk.get_note_store()
                note_store.updateNote(note)
            except ErrorTypes.EDAMNotFoundException:
                raise NoteNotFound(
                    "Can't update note. Note {0} not found".format(note.guid))
            except Exception as e:
                raise EvernoteApiError(str(e))

        await self.loop.run_in_executor(self.executor, update, note)
