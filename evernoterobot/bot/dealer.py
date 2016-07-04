import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import traceback

from motor.motor_asyncio import AsyncIOMotorClient

import settings
from ext.evernote.client import NoteContent, Types, ErrorTypes, EvernoteSdk
from bot.model import TelegramUpdate, User
from telegram.api import BotApi


class NoteNotFound(Exception):

    def __init__(self, description):
        super(NoteNotFound, self).__init__(description)


class EvernoteApi:

    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.sandbox = settings.DEBUG
        self.logger = logging.getLogger('dealer')

    async def get_note(self, auth_token, note_guid):
        def fetch(note_guid):
            self.logger.info('Fetching note {0}'.format(note_guid))
            sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
            try:
                note_store = sdk.get_note_store()
                return note_store.getNote(note_guid, True, True, False, False)
            except ErrorTypes.EDAMNotFoundException:
                raise NoteNotFound("Note {0} not found".format(note_guid))

        return await self.loop.run_in_executor(self.executor, fetch, note_guid)

    async def save_note(self, auth_token, note):
        def save(note):
            self.logger.info('Saving note...')
            sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
            note_store = sdk.get_note_store()
            return note_store.createNote(note)

        return await self.loop.run_in_executor(self.executor, save, note)

    async def update_note(self, auth_token, note):
        def update(note):
            self.logger.info('Updating note {0}'.format(note.guid))
            sdk = EvernoteSdk(token=auth_token, sandbox=self.sandbox)
            note_store = sdk.get_note_store()
            try:
                note_store.updateNote(note)
            except ErrorTypes.EDAMNotFoundException:
                raise NoteNotFound(
                    "Can't update note. Note {0} not found".format(note.guid))

        await self.loop.run_in_executor(self.executor, update, note)


class EvernoteDealer:

    def __init__(self):
        self._db_client = AsyncIOMotorClient(settings.MONGODB_URI)
        self._db = self._db_client.get_default_database()
        self.loop = asyncio.get_event_loop()
        self._evernote_api = EvernoteApi(self.loop)
        self._telegram_api = BotApi(settings.TELEGRAM['token'])
        self.logger = logging.getLogger('dealer')

    def run(self):
        try:
            while True:
                task = asyncio.ensure_future(self.fetch_updates())
                updates = self.loop.run_until_complete(task)
                if updates:
                    self.loop.run_until_complete(
                        asyncio.wait(self.process(updates)))
                else:
                    time.sleep(0.5)
        except Exception as e:
            self.logger.fatal("{0}\n{1}".format(traceback.format_exc(), e))

    async def fetch_updates(self):
        updates_by_user = {}
        try:
            for update in await TelegramUpdate.get_sorted(100):
                user_id = update.user_id
                if not updates_by_user.get(user_id):
                    updates_by_user[user_id] = []
                updates_by_user[user_id].append(update)
        except Exception as e:
            err = "%s\n%s\nCan't load telegram updates from mongo" %\
                (traceback.format_exc(), e)
            self.logger.error(err)
        return updates_by_user

    def process(self, updates_by_user):
        return [
            asyncio.ensure_future(
                self.process_user_updates(user_id, update_list))
            for user_id, update_list in updates_by_user.items()
        ]

    async def process_user_updates(self, user_id, update_list):
        self.logger.debug(
            'Start update list processing (user_id = {0})'.format(user_id))
        try:
            user = await User.get({'user_id': user_id})

            if user.mode == 'one_note':
                await self.update_note(user, update_list)
            else:
                for update in update_list:
                    await self.create_note(user, update)

            for update in update_list:
                await self._telegram_api.editMessageText(
                    user.telegram_chat_id, update.status_message_id,
                    '✅ {0} saved'.format(update.request_type.capitalize()))
                await update.delete()

            self.logger.debug(
                'Finish update list processing (user_id = %s)' % user_id)
        except Exception:
            self.logger.error(
                "{0}\nCan't process updates for user {1}".format(
                    traceback.format_exc(), user_id))

    async def update_note(self, user, updates):
        notebook_guid = user.current_notebook['guid']
        note_guid = user.places.get(notebook_guid)
        if note_guid:
            try:
                note = await self._evernote_api.get_note(
                    user.evernote_access_token, note_guid)
            except NoteNotFound as e:
                self.logger.error(e)
                note = await self.create_note(user, updates[0], 'Note for Evernoterobot')
                updates = updates[1:]

            content = NoteContent(note)
            for update in updates:
                await self.update_content(content, update)
            note.resources = content.get_resources()
            note.content = str(content)
            try:
                await self._evernote_api.update_note(
                    user.evernote_access_token, note)
            except Exception:
                self.logger.error(e)
                self.logger.error(traceback.format_exc())
        else:
            self.logger.error(
                "There are no default note in notebook {0}".format(
                    user.current_notebook['name']))

    async def create_note(self, user, update, title=None):
        notebook_guid = user.current_notebook['guid']
        text = update.data.get('text', '')
        note = Types.Note()
        note.title = title or ('%s...' % text[:25] if len(text) > 30 else text)
        if notebook_guid is not None:
            note.notebookGuid = notebook_guid
        content = NoteContent(note)
        await self.update_content(content, update)
        note.resources = content.get_resources()
        note.content = str(content)
        return await self._evernote_api.save_note(
            user.evernote_access_token, note)

    async def update_content(self, content, telegram_update):
        request_type = telegram_update.request_type or 'text'
        if request_type == 'text':
            content.add_text(telegram_update.data.get('text', ''))
        else:
            raise Exception('Unsupported request type %s' % request_type)
