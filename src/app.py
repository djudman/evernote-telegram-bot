import logging
from bot import EvernoteBot
from data.storage.storage import StorageMixin
from util.http import HttpApplication


class Application(HttpApplication):
    def __init__(self, config):
        super().__init__(config)
        logging.getLogger().debug(config)
        self.bot = EvernoteBot(config)
        try:
            self.bot.api.setWebhook(config['webhook_url'])
        except:
            pass
