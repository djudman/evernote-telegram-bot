import asyncio
import logging
import os
import traceback

from bot import DownloadTask
from bot import TelegramUpdate
from bot import User
from ext.evernote.api import NoteNotFound
from ext.evernote.provider import NoteProvider
from ext.telegram.models import Message
from ext.evernote.client import NoteContent, Types


class BaseHandler:

    def __init__(self):
        self.logger = logging.getLogger()
        self._note_provider = NoteProvider()

    async def execute(self, user: User, update: TelegramUpdate):
        if user.mode == 'one_note':
            await self._update_note(user, update)
        elif user.mode == 'multiple_notes':
            await self._create_note(user, update)
        else:
            raise Exception('Invalid user mode {0}'.format(user.mode))

    async def _create_note(self, user: User, update: TelegramUpdate):
        message = Message(update.message)
        text = message.text or message.caption or ''
        note = Types.Note()
        title = update.request_type.capitalize()
        if text:
            title = ('%s...' % text[:15] if len(text) > 15 else text)
        note.title = "[BOT] {0}".format(title)
        note.notebookGuid = user.current_notebook['guid']
        content = NoteContent(note)
        await self.update_content(content, message)
        note.resources = content.get_resources()
        note.content = str(content)
        return await self._note_provider.save_note(user.evernote_access_token, note)

    async def _update_note(self, user: User, update: TelegramUpdate):
        notebook_guid = user.current_notebook['guid']
        note_guid = user.places.get(notebook_guid)
        if not note_guid:
            raise Exception('There are no default note in notebook {0}'.format(user.current_notebook['name']))
        try:
            note = await self._note_provider.get_note(user.evernote_access_token, note_guid)
        except NoteNotFound:
            self.logger.warning("Note {0} not found. Creating new note".format(note_guid))
            note = await self._create_note(user, update)
            user.places[notebook_guid] = note.guid
            user.save()

        content = NoteContent(note)
        if update.has_file():
            new_note = await self._create_note(user, update)
            note_link = await self._note_provider.get_note_link(user.evernote_access_token, new_note)
            content.add_text('{0}: <a href="{1}">{1}</a>'.format(update.request_type.capitalize(), note_link))
        else:
            message = Message(update.message)
            await self.update_content(content, message)
        note.resources = content.get_resources()
        note.content = str(content)
        await self._note_provider.update_note(user.evernote_access_token, note)

    async def update_content(self, content: NoteContent, message: Message):
        content.add_text(message.text)

    async def cleanup(self, user: User, update: TelegramUpdate):
        update.delete()


class FileHandler(BaseHandler):

    async def update_content(self, content: NoteContent, message: Message):
        file_id = self.get_file_id(message)
        file_path, mime_type = await self.get_downloaded_file(file_id)
        content.add_file(file_path, mime_type)

    def get_file_id(self, message: Message):
        pass

    async def get_downloaded_file(self, file_id):
        task = DownloadTask.get({'file_id': file_id})
        while not task.completed:
            await asyncio.sleep(1)
            task = DownloadTask.get({'id': task.id})
        return task.file, task.mime_type

    async def cleanup(self, user: User, update: TelegramUpdate):
        try:
            file_id = self.get_file_id(Message(update.message))
            task = DownloadTask.get({'file_id': file_id})
            assert task.completed
            assert task.file
            os.unlink(task.file)
            wav_file = "{0}.wav".format(task.file)
            if os.path.exists(wav_file):
                os.unlink(wav_file)
            task.delete()
        except Exception as e:
            self.logger.fatal('{0} cleanup failed: {1}'.format(self.__class__.__name__, e), exc_info=1)
        await super().cleanup(user, update)


class TextHandler(BaseHandler):
    pass


class PhotoHandler(FileHandler):

    def get_file_id(self, message: Message):
        files = sorted(message.photos, key=lambda x: x.file_size, reverse=True)
        return files[0].file_id


class DocumentHandler(FileHandler):

    def get_file_id(self, message: Message):
        return message.document.file_id


class VideoHandler(FileHandler):

    def get_file_id(self, message: Message):
        return message.video.file_id


class VoiceHandler(FileHandler):

    def get_file_id(self, message: Message):
        return message.voice.file_id

    async def update_content(self, content: NoteContent, message: Message):
        file_id = self.get_file_id(message)
        ogg_file_path, mime_type = await self.get_downloaded_file(file_id)

        mime_type = 'audio/wav'
        wav_filename = "{0}.wav".format(ogg_file_path)
        try:
            # convert to wav
            os.system('opusdec %s %s' % (ogg_file_path, wav_filename))
        except Exception:
            self.logger.error("Can't convert ogg to wav, %s" % traceback.format_exc())
            wav_filename = ogg_file_path
            mime_type = 'audio/ogg'

        content.add_file(wav_filename, mime_type)


class LocationHandler(BaseHandler):

    async def update_content(self, content: NoteContent, message: Message):
        latitude = message.location.latitude
        longitude = message.location.longitude
        maps_url = "https://maps.google.com/maps?q=%(lat)f,%(lng)f" % {
            'lat': latitude,
            'lng': longitude,
        }
        title = 'Location'
        text = "<a href='%(url)s'>%(url)s</a>" % {'url': maps_url}

        if hasattr(message, 'venue'):
            venue = message.venue
            address = venue.address
            title = venue.title
            text = "%(title)s<br />%(address)s<br />\
                <a href='%(url)s'>%(url)s</a>" % {
                'title': title,
                'address': address,
                'url': maps_url
            }
            foursquare_id = venue.foursquare_id
            if foursquare_id:
                url = "https://foursquare.com/v/%s" % foursquare_id
                text += "<br /><a href='%(url)s'>%(url)s</a>" % {'url': url}
        content.add_text(text)
