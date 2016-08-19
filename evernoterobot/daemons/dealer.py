import asyncio
import logging
import time
import traceback

import aiomcache

import settings
from bot.model import TelegramUpdate, User
from ext.evernote.api import NoteNotFound
from ext.evernote.client import NoteContent, Types
from ext.evernote.provider import NoteProvider
from ext.telegram.api import BotApi
from .daemon import Daemon


class EvernoteDealer:

    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._telegram_api = BotApi(settings.TELEGRAM['token'])
        self.logger = logging.getLogger('dealer')
        self.cache = aiomcache.Client("127.0.0.1", 11211)
        self._note_provider = NoteProvider(self._loop)

    def run(self):
        self._loop.run_until_complete(self.async_run())
        self.logger.info('Dealer done.')

    async def async_run(self):
        try:
            while True:
                updates_by_user = self.fetch_updates()
                if not updates_by_user:
                    continue
                for user_id, updates in updates_by_user.items():
                    await self.process_user_updates(user_id, updates)
        except Exception:
            self.logger.fatal('Dealer DOWN!!!', exc_info=1)


    def fetch_updates(self):
        self.logger.debug('Fetching telegram updates...')
        updates_by_user = {}
        try:
            fetched_updates = []
            for entry in TelegramUpdate.get_sorted(condition={'in_process': {'$exists': False}}):
                update = TelegramUpdate.find_and_modify(
                    query={'_id': entry._id, 'in_process': {'$exists': False}},
                    update={'$set': {'in_process': True}})
                fetched_updates.append(TelegramUpdate(**update))
            self.logger.debug('Fetched {0} updates'.format(len(fetched_updates)))

            for update in fetched_updates:
                user_id = update.user_id
                if not updates_by_user.get(user_id):
                    updates_by_user[user_id] = []
                updates_by_user[user_id].append(update)
        except Exception as e:
            err = "{0}\nCan't load telegram updates from mongo".format(e)
            self.logger.error(err, exc_info=1)
        return updates_by_user

    def process(self, updates_by_user):
        return [
            asyncio.ensure_future(
                self.process_user_updates(user_id, update_list)
            )
            for user_id, update_list in updates_by_user.items()
        ]

    async def process_user_updates(self, user_id, update_list):
        if not update_list:
            self.logger.info('no updates for user {0}'.format(user_id))
            return
        self.logger.debug('Start update list processing (user_id = {0})'.format(user_id))
        try:
            user = User.get({'user_id': user_id})
            if user.mode == 'one_note':
                self.logger.debug('one_note mode. Try update note')
                await self.update_note(user, update_list)
                self.logger.debug('Note updated.')
            else:
                self.logger.debug('multiple_note mode. Try create note')
                for update in update_list:
                    try:
                        await self.create_note(user, update)
                        update._processed = True
                    except Exception as e:
                        self.logger.error(e)

            self.logger.debug('Cleaning up...')
            for update in filter(lambda u: hasattr(u, '_processed') and u._processed, update_list):
                await self._telegram_api.editMessageText(
                    user.telegram_chat_id, update.status_message_id,
                    '✅ {0} saved'.format(update.request_type.capitalize()))
                update.delete()
            self.logger.debug('Finish update list processing (user_id = %s)' % user_id)
        except Exception as e:
            self.logger.error(
                "{0}\nCan't process updates for user {1}".format(e, user_id),
                exc_info=1)

    async def update_note(self, user, updates):
        notebook_guid = user.current_notebook['guid']
        note_guid = user.places.get(notebook_guid)
        if note_guid:
            try:
                self.logger.debug('Getting note from evernote')
                note = await self._note_provider.get_note(user.evernote_access_token, note_guid)
            except NoteNotFound as e:
                self.logger.error("{0}\nNote not found. Creating new note".format(e), exc_info=1)
                note = await self.create_note(user, updates[0], 'Note for Evernoterobot')
                updates = updates[1:]
                user.places[notebook_guid] = note.guid
                user.save()
                self.logger.info('New note created')

            content = NoteContent(note)
            for update in updates:
                try:
                    self.logger.info('Trying update content')
                    await self.update_content(content, update)
                    update._processed = True
                    self.logger.info('Telegram update processed.')
                except Exception as e:
                    self.logger.error(e, exc_info=1)
            note.resources = content.get_resources()
            note.content = str(content)
            self.logger.info('Updating note...')
            await self._note_provider.update_note(user.evernote_access_token, note)
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
        return await self._note_provider.save_note(user.evernote_access_token, note)

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
