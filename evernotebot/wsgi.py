import logging
import traceback
from os.path import dirname, realpath

from uhttp import WsgiApplication

from evernotebot.config import load_config
from evernotebot.bot.core import EvernoteBot
from evernotebot.web.urls import urls


class EvernoteBotApplication(WsgiApplication):
    def __init__(self):
        config = load_config()
        super().__init__(
            src_root=realpath(dirname(__file__)),
            urls=urls,
            config=config
        )
        self.bot = EvernoteBot(config)
        webhook_url = config['telegram']['webhook_url']
        self.set_telegram_webhook(webhook_url)

    def set_telegram_webhook(self, webhook_url):
        try:
            self.bot.api.setWebhook(webhook_url)
        except Exception:
            e = traceback.format_exc()
            message = f"Can't set up webhook url `{webhook_url}`.\n{e}"
            logging.getLogger('evernotebot').fatal({'exception': message})


app = EvernoteBotApplication()
