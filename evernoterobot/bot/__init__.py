import inspect
import importlib
import os
import sys
import time
from os.path import realpath, dirname, join

from telegram.bot import TelegramBot, TelegramBotCommand
from settings import MONGODB_CLIENT


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


class StartSession:

    db = MONGODB_CLIENT

    def __init__(self, user_id, chat_id, oauth_data):
        self.created = time.time()
        self.user_id = user_id
        self.telegram_chat_id = chat_id
        self.oauth_token = oauth_data.oauth_token
        self.oauth_token_secret = oauth_data.oauth_token_secret
        self.oauth_url = oauth_data.oauth_url
        self.callback_key = oauth_data.callback_key

    async def save(self):
        data = {}
        for k, v in self.__dict__.items():
            data[k] = getattr(self, k)
        data['_id'] = data['user_id']
        db = self.db.evernoterobot
        await db.start_sessions.save(data)

    async def find(self, evernote_callback_key: str):
        db = self.db.evernoterobot
        session = await db.start_sessions.find_one(
            {'callback_key': evernote_callback_key})
        if session:
            session['user_id'] = session['_id']
            del session['_id']
            return StartSession(session)


class EvernoteBot(TelegramBot):

    def __init__(self, token, name, memcached_client):
        super(EvernoteBot, self).__init__(token, name)
        self.cache = memcached_client
        for cmd_class in get_commands():
            self.add_command(cmd_class)

    async def create_start_session(self, user_id, oauth_data):
        pass

    async def on_message_received(self, message):
        pass
