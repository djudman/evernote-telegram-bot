import json
import time
import os
from os.path import realpath, dirname, join
import logging
import asyncio
import traceback

from evernotelib.client import EvernoteClient, EvernoteOauthData
from telegram.api import BotApi
from telegram.user import User


class EvernoteRobot:

    def __init__(self, telegram: BotApi, evernote: EvernoteClient, db_client,
                 memcached_client):
        self.bot_url = 'https://telegram.me/evernoterobot'
        self.telegram = telegram
        self.evernote = evernote
        self.db = db_client
        self.cache = memcached_client
        self.logger = logging.getLogger()
        self.commands = self.collect_commands(
                join(realpath(dirname(__file__)), 'commands')
            )

    def collect_commands(self, dir_path: str):
        # TODO:
        from .commands.help import help
        from .commands.start import start
        from .commands.notebook import notebook
        return {
            'start': start,
            'help': help,
            'notebook': notebook,
        }

    async def handle_update(self, data: dict):
        if 'message' in data:
            await self.handle_message(data['message'])
        elif 'inline_query' in data:
            self.logger.info('Inline query: %s' % data)
            # TODO: process inline query
        elif 'chosen_inline_result' in data:
            self.logger.info('Chosen inline result: %s' % data)
            # TODO: process inline result
        elif 'callback_query' in data:
            self.logger.info('Callback query: %s' % data)
            await self.handle_callback_query(data['callback_query'])
        else:
            self.logger.error('Unsupported update: %s' % data)

    async def user_exists(self, user):
        db = self.db.evernoterobot
        user_info = await db.users.find_one({'_id': user.id})
        return user_info is not None

    async def handle_message(self, message: dict):
        self.chat_id = message['chat']['id']
        if message.get('from'):
            self.user = User(message.get('from'))
        if not await self.user_exists(self.user):
            await self.send_message(self.user.id,
                                    'You should sign in to Evernote first')
            return await self.execute_command('start')

        if message.get('photo'):
            await self.handle_photo(message)
        elif message.get('document'):
            await self.handle_document(message)
        elif message.get('voice'):
            await self.handle_voice(message)
        elif message.get('location'):
            await self.handle_location(message)
        else:
            commands = []
            for entity in message.get('entities', []):
                if entity['type'] == 'bot_command':
                    offset = entity['offset']
                    length = entity['length']
                    cmd = message.get('text', '')[offset:length]
                    if cmd.startswith('/'):
                        cmd = cmd.replace('/', '')
                    commands.append(cmd)

            if commands:
                for cmd in commands:
                    await self.execute_command(cmd)
            else:
                text = message.get('text')
                if text:
                    await self.handle_text_message(self.chat_id, text)

    async def execute_command(self, cmd_name: str):
        try:
            callable_func = self.commands.get(cmd_name)
            if callable_func:
                if asyncio.iscoroutinefunction(callable_func):
                    await callable_func(self, self.chat_id, self.telegram)
                else:
                    callable_func(self, self.chat_id, self.telegram)
            else:
                text = "WTF? I don't know this words: '%s'" % cmd_name
                await self.telegram.sendMessage(self.chat_id, text)
                # TODO: send list available commands
                # help_cmd = self.commands['help']
                # await help_cmd(self.chat_id, self.telegram)
                self.logger.error("Unsupported command '%s'" % cmd_name)
        except Exception:
            text = "Houston, we have a problem. Please try again later"
            await self.telegram.sendMessage(self.chat_id, text)
            self.logger.error(traceback.format_exc())

    async def send_message(self, user_id, text):
        db = self.db.evernoterobot
        session = await db.start_sessions.find_one({'_id': user_id})
        await self.telegram.sendMessage(session['telegram_chat_id'], text)

    # async def edit_message(self, chat_id, message_id, text):
    #     await self.telegram.editMessageText(chat_id, message_id, text)

    async def create_start_session(self, user_id,
                                   evernote_oauth_data: EvernoteOauthData):
        session = {
            '_id': user_id,
            'created': time.time(),
            'telegram_chat_id': self.chat_id,
            'oauth_token': evernote_oauth_data.oauth_token,
            'oauth_token_secret': evernote_oauth_data.oauth_token_secret,
            'oauth_url': evernote_oauth_data.oauth_url,
            'callback_key': evernote_oauth_data.callback_key,
        }
        db = self.db.evernoterobot
        await db.start_sessions.save(session)

    async def get_start_session(self, evernote_callback_key: str):
        db = self.db.evernoterobot
        session = await db.start_sessions.find_one(
            {'callback_key': evernote_callback_key})
        if session:
            session['user_id'] = session['_id']
            del session['_id']
            return session

    async def register_user(self, start_session, evernote_access_token):
        user_id = start_session['user_id']
        await self.cache.set(str(user_id).encode(),
                             evernote_access_token.encode())
        notebook = self.evernote.getDefaultNotebook()
        await self.cache.set("{0}_nb".format(user_id).encode(),
                             notebook.guid.encode())
        db = self.db.evernoterobot
        user = {
            '_id': start_session['user_id'],
            'evernote_access_token': evernote_access_token,
            'notebook_guid': notebook.guid,
        }
        await db.users.save(user)

    async def get_evernote_access_token(self, user_id):
        key = str(user_id).encode()
        token = await self.cache.get(key)
        if token:
            notebook_guid = await self.cache.get(
                "{0}_nb".format(user_id).encode()
            )
            return token.decode(), notebook_guid
        else:
            db = self.db.evernoterobot
            user = await db.users.find_one({'_id': self.user.id})
            token = user['evernote_access_token']
            notebook_guid = user['notebook_guid']
            await self.cache.set(key, token.encode())
            return token, notebook_guid

    async def handle_text_message(self, chat_id, text):
        reply = await self.telegram.sendMessage(chat_id, '🔄 Accepted')
        access_token, guid = await self.get_evernote_access_token(self.user.id)
        self.evernote.create_note(access_token, text, notebook_guid=guid)  # TODO: async
        await self.telegram.editMessageText(chat_id, reply['message_id'],
                                            '✅ Text saved')

    async def handle_photo(self, message):
        chat_id = message['chat']['id']
        reply = await self.telegram.sendMessage(chat_id, '🔄 Accepted')
        caption = message.get('caption', '')
        title = caption or 'Photo'

        files = sorted(message['photo'], key=lambda x: x.get('file_size'),
                       reverse=True)
        file_id = files[0]['file_id']
        filename = await self.telegram.downloadFile(file_id)
        access_token, guid = await self.get_evernote_access_token(self.user.id)
        self.evernote.create_note(access_token, caption, title,
                                  files=[(filename, 'image/jpeg')],
                                  notebook_guid=guid)

        await self.telegram.editMessageText(chat_id, reply['message_id'],
                                            '✅ Image saved')

    async def handle_voice(self, message):
        chat_id = message['chat']['id']
        reply = await self.telegram.sendMessage(chat_id, '🔄 Accepted')
        caption = message.get('caption', '')
        title = caption or 'Voice'

        file_id = message['voice']['file_id']
        ogg_filename = await self.telegram.downloadFile(file_id)
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
        access_token, guid = await self.get_evernote_access_token(self.user.id)
        self.evernote.create_note(access_token, caption, title,
                                  files=[(wav_filename, mime_type)],
                                  notebook_guid=guid)

        await self.telegram.editMessageText(chat_id, reply['message_id'],
                                            '✅ Voice saved')

    async def handle_location(self, message):
        chat_id = message['chat']['id']
        reply = await self.telegram.sendMessage(chat_id, '🔄 Accepted')
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

        access_token, guid = await self.get_evernote_access_token(self.user.id)
        self.evernote.create_note(access_token, text, title, notebook_guid=guid)
        await self.telegram.editMessageText(chat_id, reply['message_id'],
                                            '✅ Location saved')

    async def handle_document(self, message):
        chat_id = message['chat']['id']
        reply = await self.telegram.sendMessage(chat_id, '🔄 Accepted')
        file_id = message['document']['file_id']
        short_file_name = message['document']['file_name']
        file_path = await self.telegram.downloadFile(file_id)
        mime_type = message['document']['mime_type']

        access_token, guid = await self.get_evernote_access_token(self.user.id)
        self.evernote.create_note(access_token, '', short_file_name,
                                  files=[(file_path, mime_type)],
                                  notebook_guid=guid)

        await self.telegram.editMessageText(chat_id, reply['message_id'],
                                            '✅ Document saved')

    async def handle_callback_query(self, query):
        data = json.loads(query['data'])
        cmd = data['cmd']
        if cmd == 'nb':
            chat_id = query['message']['chat']['id']
            if query.get('from'):
                self.user = User(query.get('from'))
            notebook_guid = data['id']
            db = self.db.evernoterobot
            await db.users.update(
                {"_id": self.user.id},
                {'$set': {'notebook_guid': notebook_guid}})
            await self.telegram.sendMessage(
                chat_id, 'Current notebook is: "%s"' % notebook_guid)
