import sys
from os.path import dirname, realpath

sys.path.insert(0, realpath(dirname(__file__)))

from telegram.api import BotApi


class TestBotApi(BotApi):

    async def sendMessage(self, chat_id, text, reply_markup=None):
        pass
