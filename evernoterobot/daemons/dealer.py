import asyncio
import logging
import time
import traceback

from motor.motor_asyncio import AsyncIOMotorClient

from .daemon import Daemon
import settings
from ext.evernote.client import NoteContent, Types
from bot.model import TelegramUpdate, User
from telegram.api import BotApi
from ext.evernote.api import AsyncEvernoteApi, NoteNotFound


class EvernoteDealer:

    def __init__(self, loop=None):
        self._db_client = AsyncIOMotorClient(settings.MONGODB_URI)
        self._db = self._db_client.get_default_database()
        self._loop = loop or asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._evernote_api = AsyncEvernoteApi(self._loop)
        self._telegram_api = BotApi(settings.TELEGRAM['token'])
        self.logger = logging.getLogger('dealer')

    def run(self):
        try:
            while True:
                updates = self._loop.run_until_complete(self.fetch_updates())
                if updates:
                    self.process(updates)
                else:
                    time.sleep(0.5)
        except Exception as e:
            self.logger.fatal(e)
            self.logger.fatal(traceback.format_exc())

    async def fetch_updates(self):
        self.logger.debug('Fetching telegram updates...')
        updates_by_user = {}
        try:
            for update in await TelegramUpdate.get_sorted(100):
                user_id = update.user_id
                if not updates_by_user.get(user_id):
                    updates_by_user[user_id] = []
                updates_by_user[user_id].append(update)
        except Exception as e:
            err = "{0}\nCan't load telegram updates from mongo".format(e)
            self.logger.error(err)
        return updates_by_user

    def process(self, updates_by_user):
        return [
            asyncio.ensure_future(
                self.process_user_updates(user_id, update_list),
                loop=self._loop
            )
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
                    try:
                        await self.create_note(user, update)
                        update.__processed = True
                    except Exception as e:
                        self.logger.error(e)

            for update in filter(lambda u: hasattr(u, '__processed') and u.__processed, update_list):
                await self._telegram_api.editMessageText(
                    user.telegram_chat_id, update.status_message_id,
                    '✅ {0} saved'.format(update.request_type.capitalize()))
                await update.delete()
            self.logger.debug('Finish update list processing (user_id = %s)' % user_id)
        except Exception as e:
            self.logger.error(
                "{0}\nCan't process updates for user {1}".format(e, user_id))

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
                user.places[notebook_guid] = note.guid
                await user.save()

            content = NoteContent(note)
            for update in updates:
                try:
                    await self.update_content(content, update)
                    update.__processed = True
                except Exception as e:
                    self.logger.error(e)
            note.resources = content.get_resources()
            note.content = str(content)

            await self._evernote_api.update_note(user.evernote_access_token, note)
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
        try:
            await self.update_content(content, update)
        except Exception as e:
            self.logger.error(e)
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


class EvernoteDealerDaemon(Daemon):

    def run(self):
        dealer = EvernoteDealer()
        dealer.run()