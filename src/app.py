from bot import EvernoteBot
from data.storage import StorageMixin
from util.http import HttpApplication


class Application(HttpApplication):
    def __init__(self, config):
        super().__init__(config)
        self.bot = EvernoteBot(config)

