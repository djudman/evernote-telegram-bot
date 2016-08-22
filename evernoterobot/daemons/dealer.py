import asyncio
import logging
import time
import traceback
import os

import aiomcache

import settings
from bot.model import TelegramUpdate, User, DownloadTask
from daemons.downloader import TelegramDownloader
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
        self.downloader = TelegramDownloader('/tmp/')

    def run(self):
        try:
            asyncio.ensure_future(self.async_run())
            self._loop.run_forever()
            self.logger.info('Dealer done.')
        except Exception as e:
            self.logger.fatal('Dealer fail')
            self.logger.fatal(e, exc_info=1)

    async def async_run(self):
        try:
            while True:
                updates_by_user = self.fetch_updates()
                if not updates_by_user:
                    await asyncio.sleep(0.1)
                    continue
                for user_id, updates in updates_by_user.items():
                    try:
                        user = User.get({'user_id': user_id})
                        asyncio.ensure_future(self.process_user_updates(user, updates))
                    except Exception as e:
                        # TODO: put updates data to special collection ('failed_updates')
                        self.logger.error("Can't process updates for user {0}\n{1}".format(user_id, e))
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

    async def process_user_updates(self, user, update_list):
        start_ts = time.time()
        self.logger.debug('Start update list processing (user_id = {0})'.format(user.user_id))
        if user.mode == 'one_note':
            await self.update_note(user, update_list)
        elif user.mode == 'multiple_notes':
            for update in update_list:
                try:
                    await self.create_note(user, update)
                except Exception as e:
                    # TODO: put failed update data to special collection
                    self.logger.error(e, exc_info=1)
        else:
            raise Exception('Invalid user mode {0}'.format(user.mode))

        self.logger.debug('Cleaning up...')
        for update in update_list:
            update.delete()
            await self._telegram_api.editMessageText(user.telegram_chat_id, update.status_message_id,
                                                     '✅ {0} saved ({1} s)'.format(update.request_type.capitalize(),
                                                                                  time.time() - start_ts))

        self.logger.debug('Done. (user_id = {0}). Processing takes {1} s'.format(user.user_id, time.time() - start_ts))

    async def update_note(self, user, updates):
        notebook_guid = user.current_notebook['guid']
        note_guid = user.places.get(notebook_guid)
        if not note_guid:
            raise Exception('There are no default note in notebook {0}'.format(user.current_notebook['name']))

        try:
            note = await self._note_provider.get_note(user.evernote_access_token, note_guid)
        except NoteNotFound:
            self.logger.warning("Note {0} not found. Creating new note".format(note_guid))
            note = await self.create_note(user, updates[0], 'Note for Evernoterobot')
            updates = updates[1:]
            user.places[notebook_guid] = note.guid
            user.save()

        content = NoteContent(note)
        for update in updates:
            if update.request_type in ['photo', 'document', 'voice']:
                new_note = await self.create_note(user, update, update.request_type.capitalize())
                note_link = await self._note_provider.get_note_link(user.evernote_access_token, new_note)
                content.add_text('{0}: {1}'.format(update.request_type.capitalize(), note_link))
            else:
                await self.update_content(content, update)
        note.resources = content.get_resources()
        note.content = str(content)
        await self._note_provider.update_note(user.evernote_access_token, note)

    async def create_note(self, user, update, title=None):
        notebook_guid = user.current_notebook['guid']
        text = update.data.get('text') or update.data.get('caption') or ''
        note = Types.Note()
        if title is None:
            title = update.request_type
        note.title = title or ('%s...' % text[:25] if len(text) > 30 else text)
        note.notebookGuid = notebook_guid
        content = NoteContent(note)
        await self.update_content(content, update)
        note.resources = content.get_resources()
        note.content = str(content)
        return await self._note_provider.save_note(user.evernote_access_token, note)

    async def update_content(self, content, telegram_update):
        request_type = telegram_update.request_type or 'text'
        if request_type == 'text':
            content.add_text(telegram_update.data.get('text', ''))
        elif request_type == 'photo':
            files = telegram_update.data.get('photo')
            files = sorted(files, key=lambda x: x.get('file_size'), reverse=True)
            file_path, mime_type = await self.get_downloaded_file(file_id=files[0]['file_id'])
            content.add_file(file_path, mime_type)
        elif request_type == 'document':
            file_id = telegram_update.data['document']['file_id']
            file_path, mime_type = await self.get_downloaded_file(file_id=file_id)
            content.add_file(file_path, mime_type)
        elif request_type == 'voice':
            file_id = telegram_update.data['voice']['file_id']
            ogg_file_path, mime_type = await self.get_downloaded_file(file_id=file_id)

            mime_type = 'audio/wav'
            wav_filename = "{0}.wav".format(ogg_file_path)
            try:
                # convert to wav
                os.system('opusdec %s %s' % (ogg_file_path, wav_filename))
            except Exception:
                self.logger.error("Can't convert ogg to wav, %s" %
                                  traceback.format_exc())
                wav_filename = ogg_file_path
                mime_type = 'audio/ogg'

            content.add_file(wav_filename, mime_type)
        elif request_type == 'location':
            location = telegram_update.data['location']
            latitude = location['latitude']
            longitude = location['longitude']
            maps_url = "https://maps.google.com/maps?q=%(lat)f,%(lng)f" % {
                'lat': latitude,
                'lng': longitude,
            }
            title = 'Location'
            text = "<a href='%(url)s'>%(url)s</a>" % {'url': maps_url}

            venue = telegram_update.data.get('venue')
            if venue:
                address = venue.get('address', '')
                title = venue.get('title', '')
                text = "%(title)s<br />%(address)s<br />\
                    <a href='%(url)s'>%(url)s</a>" % {
                    'title': title,
                    'address': address,
                    'url': maps_url
                }
                foursquare_id = venue.get('foursquare_id')
                if foursquare_id:
                    url = "https://foursquare.com/v/%s" % foursquare_id
                    text += "<br /><a href='%(url)s'>%(url)s</a>" % {'url': url}
            content.add_text(text)
        else:
            raise Exception('Unsupported request type %s' % request_type)

    async def get_downloaded_file(self, file_id):
        task = DownloadTask.get({'file_id': file_id})
        while not task.completed:
            await asyncio.sleep(1)
            task = DownloadTask.get({'_id': task._id})
        return task.file, task.mime_type


class EvernoteDealerDaemon(Daemon):

    def run(self):
        dealer = EvernoteDealer()
        dealer.run()
