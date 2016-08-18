import asyncio
import aiomcache
import json

from ext.evernote.api import AsyncEvernoteApi
from ext.evernote.client import Types


class NoteProvider:

    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self.cache = aiomcache.Client("127.0.0.1", 11211)
        self._api = AsyncEvernoteApi(self._loop)

    def get_cache_key(self, guid):
        return 'evernote_note_{0}'.format(guid)

    async def __cache_note(self, note):
        cache_key = self.get_cache_key(note.guid)
        data = {
            'title': note.title,
            'notebookGuid': note.notebookGuid,
            'content': note.content,
        }
        await self.cache.set(cache_key, json.dumps(data).encode())

    async def get_note(self, access_token, guid):
        cache_key = self.get_cache_key(guid)
        cached_data = await self.cache.get(cache_key)
        note_data = json.loads(cached_data.decode())
        if note_data:
            note = Types.Note()
            note.title = note_data.get('title')
            note.notebookGuid = note_data.get('notebookGuid')
            note.content = note_data.get('content')
        else:
            note = await self._api.get_note(access_token, guid)
            self.__cache_note(note)
        return note

    async def update_note(self, access_token, note):
        await self._api.update_note(access_token, note)
        await self.__cache_note(note)

    async def save_note(self, access_token, note):
        await self._api.save_note(access_token, note)
        await self.__cache_note(note)
