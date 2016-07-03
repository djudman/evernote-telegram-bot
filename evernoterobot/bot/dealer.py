import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from motor.motor_asyncio import AsyncIOMotorClient

import settings
from ext.evernote.client import NoteContent, Types, EvernoteSdk
from bot.model import TelegramUpdate, User
from telegram.api import BotApi


class EvernoteApi:

    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.sandbox = settings.DEBUG
        self.logger = logging.getLogger()

    async def get_note(self, auth_token, note_guid):
        def fetch(note_guid):
            self.logger.info('Fetching note {0}'.format(note_guid))
            sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
            note_store = sdk.get_note_store()
            return note_store.getNote(note_guid, True, True, False, False)

        return await self.loop.run_in_executor(self.executor, fetch, note_guid)

    async def save_note(self, auth_token, note):
        def save(note):
            self.logger.info('Saving note...')
            sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
            note_store = sdk.get_note_store()
            return note_store.createNote(note)

        await self.loop.run_in_executor(self.executor, save, note)

    async def update_note(self, auth_token, note):
        def update(note):
            self.logger.info('Updating note {0}'.format(note.guid))
            sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
            note_store = sdk.get_note_store()
            note_store.updateNote(note)

        await self.loop.run_in_executor(self.executor, update, note)


class EvernoteDealer:

    def __init__(self):
        self._db_client = AsyncIOMotorClient(settings.MONGODB_URI)
        self._db = self._db_client.get_default_database()
        self.loop = asyncio.get_event_loop()
        self._evernote_api = EvernoteApi(self.loop)
        self._telegram_api = BotApi(settings.TELEGRAM['token'])
        self.logger = logging.getLogger()

    def run(self):
        while True:
            updates = self.loop.run_until_complete(
                asyncio.ensure_future(self.fetch_updates())
            )
            self.loop.run_until_complete(asyncio.wait(self.process(updates)))

    async def fetch_updates(self):
        updates_by_user = {}
        for update in await TelegramUpdate.get_sorted(100):
            user_id = update.user_id
            if not updates_by_user.get(user_id):
                updates_by_user[user_id] = []
            updates_by_user[user_id].append(update)
        return updates_by_user

    def process(self, updates_by_user):
        futures = []
        for user_id, update_list in updates_by_user.items():
            futures.append(
                asyncio.ensure_future(self.process_one(user_id, update_list)))
        return futures

    async def process_one(self, user_id, update_list):
        self.logger.info('Start update list processing (user_id = {0})'.format(user_id))
        user = await User.get({'user_id': user_id})

        if user.mode == 'one_note':
            await self.update_note(user, update_list)
        else:
            for update in update_list:
                await self.create_note(user, update)

        for update in update_list:
            await self._telegram_api.editMessageText(
                user.telegram_chat_id, update.status_message_id, '✅ Saved')
            await update.delete()

    async def update_note(self, user, updates):
        notebook_guid = user.current_notebook['guid']
        note_guid = user.places.get(notebook_guid)
        note = await self._evernote_api.get_note(user.evernote_access_token, note_guid)
        content = NoteContent(note)
        for update in updates:
            await self.update_content(content, update)
        note.resources = content.get_resources()
        note.content = str(content)
        await self._evernote_api.update_note(user.evernote_access_token, note)

    async def create_note(self, user, update, title=None):
        notebook_guid = user.current_notebook['guid']
        text = update['message'].get('text', '')
        note = Types.Note()
        note.title = title or ('%s...' % text[:25] if len(text) > 30 else text)
        if notebook_guid is not None:
            note.notebookGuid = notebook_guid
        content = NoteContent(note)
        self.update_content(content, update)
        note.resources = content.get_resources()
        note.content = str(content)
        await self._evernote_api.save_note(user.evernote_access_token, note)

    async def update_content(self, content, telegram_update):
        request_type = telegram_update.request_type or 'text'
        if request_type == 'text':
            content.add_text(telegram_update.data['text'])
        else:
            raise Exception('Unsupported request type %s' % request_type)
