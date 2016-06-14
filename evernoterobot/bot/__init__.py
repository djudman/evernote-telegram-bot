import inspect
import importlib
import os
import sys
from os.path import realpath, dirname, join

from telegram.bot import TelegramBot, TelegramBotCommand
from bot.model import StartSession, User


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
                           issubclass(klass, TelegramBotCommand):
                            commands.append(klass)
    return commands


class EvernoteBot(TelegramBot):

    def __init__(self, token, name, memcached_client):
        super(EvernoteBot, self).__init__(token, name)
        self.cache = memcached_client
        for cmd_class in get_commands():
            self.add_command(cmd_class)

    async def create_start_session(self, user_id, chat_id, oauth_data):
        session = StartSession(user_id, chat_id, oauth_data)
        await session.save()

    async def get_start_session(self, callback_key):
        await StartSession.find(callback_key)

    async def register_user(self, start_session, evernote_access_token):
        user_id = start_session.user_id
        await self.cache.set(str(user_id).encode(),
                             evernote_access_token.encode())
        notebook = self.evernote.getNotebook(evernote_access_token)
        await self.cache.set("{0}_nb".format(user_id).encode(),
                             notebook.guid.encode())
        user = User(user_id, evernote_access_token, notebook.guid)
        await user.save()

    async def get_evernote_access_token(self, user_id):
        key = str(user_id).encode()
        token = await self.cache.get(key)
        if token:
            notebook_guid = await self.cache.get(
                "{0}_nb".format(user_id).encode())
            return token.decode(), notebook_guid.decode()
        else:
            entry = await User.find_one({'_id': user_id})
            token = entry['evernote_access_token']
            notebook_guid = entry['notebook_guid']
            await self.cache.set(key, token.encode())
            await self.cache.set("{0}_nb".format(user_id).encode(),
                                 notebook_guid.encode())
            return token, notebook_guid

    async def on_message_received(self, message):
        pass
