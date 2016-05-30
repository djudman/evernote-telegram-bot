import inspect
import importlib
import os
import sys
from os.path import realpath, dirname, join

from telegram.bot import TelegramBot, TelegramBotCommand


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

    def __init__(self):
        super(EvernoteBot, self).__init__()
        for cmd_class in get_commands():
            self.add_command(cmd_class)

    async def on_message_received(self, message):
        pass
