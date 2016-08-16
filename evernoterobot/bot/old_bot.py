import importlib
import inspect
import json
import os
import sys
import traceback
from os.path import realpath, dirname, join

import aiomcache

import settings
from bot.model import User, ModelNotFound
from ext.evernote.client import EvernoteClient
from ext.telegram.bot import TelegramBot, TelegramBotCommand


def get_commands(cmd_dir=None):
    commands = []
    if cmd_dir is None:
        cmd_dir = join(realpath(dirname(__file__)), 'commands')
    exclude_modules = ['__init__']
    for dirpath, dirnames, filenames in os.walk(cmd_dir):
        for filename in filenames:
            file_path = join(dirpath, filename)
            ext = file_path.split('.')[-1]
            if ext in ['py']:
                sys_path = list(sys.path)
                sys.path.insert(0, cmd_dir)
                module_name = inspect.getmodulename(file_path)
                if module_name not in exclude_modules:
                    module = importlib.import_module(module_name)
                    sys.path = sys_path
                    for name, klass in inspect.getmembers(module):
                        if inspect.isclass(klass) and\
                           issubclass(klass, TelegramBotCommand) and\
                           klass != TelegramBotCommand:
                            commands.append(klass)
    return commands


class EvernoteBot(TelegramBot):

    def __init__(self, token, name):
        super(EvernoteBot, self).__init__(token, name)
        self.evernote = EvernoteClient(
            settings.EVERNOTE['key'],
            settings.EVERNOTE['secret'],
            settings.EVERNOTE['oauth_callback'],
            sandbox=settings.DEBUG
        )
        self.cache = aiomcache.Client("127.0.0.1", 11211)
        for cmd_class in get_commands():
            self.add_command(cmd_class)

    async def list_notebooks(self, user):
        key = "list_notebooks_{0}".format(user.user_id).encode()
        data = await self.cache.get(key)
        if not data:
            access_token = user.evernote_access_token
            notebooks = [{'guid': nb.guid, 'name': nb.name} for nb in
                         self.evernote.list_notebooks(access_token)]
            await self.cache.set(key, json.dumps(notebooks).encode())
        else:
            notebooks = json.loads(data.decode())
        return notebooks

    async def update_notebooks_cache(self, user):
        key = "list_notebooks_{0}".format(user.user_id).encode()
        access_token = user.evernote_access_token
        notebooks = [{'guid': nb.guid, 'name': nb.name} for nb in
                     self.evernote.list_notebooks(access_token)]
        await self.cache.set(key, json.dumps(notebooks).encode())

    async def get_user(self, message):
        try:
            user = await User.get({'user_id': message['from']['id']})
            if user.telegram_chat_id != message['chat']['id']:
                user.telegram_chat_id = message['chat']['id']
                await user.save()
            return user
        except ModelNotFound:
            self.logger.warn("User %s not found" % message['from']['id'])

    async def set_current_notebook(self, user, notebook_name):
        all_notebooks = await self.list_notebooks(user)
        for notebook in all_notebooks:
            if notebook['name'] == notebook_name:
                user.current_notebook = notebook
                user.state = None
                await user.save()

                markup = json.dumps({'hide_keyboard': True})
                await self.api.sendMessage(
                    user.telegram_chat_id,
                    'From now your current notebook is: %s' % notebook_name,
                    reply_markup=markup)
                break
        else:
            await self.api.sendMessage(user.telegram_chat_id,
                                       'Please, select notebook')

    async def save_to_evernote(self, user, text, title=None, files=None):
        notebook_guid = user.current_notebook['guid']
        if user.mode == 'one_note':
            note_guid = user.places.get(notebook_guid)
            if not note_guid:
                note_guid = self.evernote.create_note(
                    user.evernote_access_token, text, title=title, files=files,
                    notebook_guid=notebook_guid)
                user.places[notebook_guid] = note_guid
                await user.save()
            else:
                self.evernote.update_note(
                    user.evernote_access_token, note_guid, text, files=files)
        else:
            self.evernote.create_note(
                user.evernote_access_token, text, title=title, files=files,
                notebook_guid=notebook_guid)

    async def on_text(self, user, message, text):
        if user.state == 'select_notebook':
            if text.startswith('> ') and text.endswith(' <'):
                text = text[2:-2]
            await self.set_current_notebook(user, text)
        else:
            reply = await self.api.sendMessage(user.telegram_chat_id,
                                               '🔄 Accepted')
            await self.save_to_evernote(user, text)
            await self.api.editMessageText(user.telegram_chat_id,
                                           reply['message_id'],
                                           '✅ Text saved')

    async def on_photo(self, user, message):
        reply = await self.api.sendMessage(user.telegram_chat_id, '🔄 Accepted')
        caption = message.get('caption', '')
        title = caption or 'Photo'

        files = sorted(message['photo'], key=lambda x: x.get('file_size'),
                       reverse=True)
        file_id = files[0]['file_id']
        filename = await self.api.downloadFile(file_id)
        self.evernote.create_note(user.evernote_access_token, caption, title,
                                  files=[(filename, 'image/jpeg')],
                                  notebook_guid=user.current_notebook['guid'])

        await self.api.editMessageText(user.telegram_chat_id,
                                       reply['message_id'], '✅ Image saved')
        os.unlink(filename)

    async def on_voice(self, user, message):
        reply = await self.api.sendMessage(user.telegram_chat_id, '🔄 Accepted')
        caption = message.get('caption', '')
        title = caption or 'Voice'

        file_id = message['voice']['file_id']
        ogg_filename = await self.api.downloadFile(file_id)
        wav_filename = ogg_filename + '.wav'
        mime_type = 'audio/wav'
        try:
            # convert to wav
            os.system('opusdec %s %s' % (ogg_filename, wav_filename))
        except Exception:
            self.logger.error("Can't convert ogg to wav, %s" %
                              traceback.format_exc())
            wav_filename = ogg_filename
            mime_type = 'audio/ogg'
        self.evernote.create_note(user.evernote_access_token, caption, title,
                                  files=[(wav_filename, mime_type)],
                                  notebook_guid=user.current_notebook['guid'])
        await self.api.editMessageText(user.telegram_chat_id,
                                       reply['message_id'],
                                       '✅ Voice saved')
        os.unlink(ogg_filename)
        os.unlink(wav_filename)

    async def on_location(self, user, message):
        reply = await self.api.sendMessage(user.telegram_chat_id, '🔄 Accepted')
        # TODO: use google maps API for getting location image
        location = message['location']
        latitude = location['latitude']
        longitude = location['longitude']
        maps_url = "https://maps.google.com/maps?q=%(lat)f,%(lng)f" % {
            'lat': latitude,
            'lng': longitude,
        }
        title = 'Location'
        text = "<a href='%(url)s'>%(url)s</a>" % {'url': maps_url}

        if message.get('venue'):
            address = message['venue'].get('address', '')
            title = message['venue'].get('title', '')
            text = "%(title)s<br />%(address)s<br />\
                <a href='%(url)s'>%(url)s</a>" % {
                'title': title,
                'address': address,
                'url': maps_url
            }
            foursquare_id = message['venue'].get('foursquare_id')
            if foursquare_id:
                url = "https://foursquare.com/v/%s" % foursquare_id
                text += "<br /><a href='%(url)s'>%(url)s</a>" % {'url': url}

        self.evernote.create_note(user.evernote_access_token, text, title,
                                  notebook_guid=user.current_notebook['guid'])
        await self.api.editMessageText(user.telegram_chat_id,
                                       reply['message_id'],
                                       '✅ Location saved')

    async def on_document(self, user, message):
        reply = await self.api.sendMessage(user.telegram_chat_id, '🔄 Accepted')
        file_id = message['document']['file_id']
        short_file_name = message['document']['file_name']
        file_path = await self.api.downloadFile(file_id)
        mime_type = message['document']['mime_type']

        self.evernote.create_note(user.evernote_access_token, '',
                                  short_file_name,
                                  files=[(file_path, mime_type)],
                                  notebook_guid=user.current_notebook['guid'])

        await self.api.editMessageText(user.telegram_chat_id,
                                       reply['message_id'],
                                       '✅ Document saved')
        os.unlink(file_path)
