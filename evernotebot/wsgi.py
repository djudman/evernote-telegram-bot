import logging
import traceback
from os.path import dirname, realpath

from uhttp import WsgiApplication

from evernotebot.config import load_config
from evernotebot.bot.core import EvernoteBot
from evernotebot.web.views import telegram_hook, evernote_oauth


class EvernoteBotApplication(WsgiApplication):
    def __init__(self):
        config = load_config()
        super().__init__(
            src_root=realpath(dirname(__file__)),
            urls=self.get_urls(),
            config=config
        )
        self.bot = EvernoteBot(config)
        webhook_url = config['telegram']['webhook_url']
        self.set_telegram_webhook(webhook_url)

    def get_urls(self):
        telegram_api_token = self.config['telegram']['token']
        return (
            ('POST', f'^/{telegram_api_token}$', telegram_hook),
            ('GET', r'^/evernote/oauth$', evernote_oauth),
        )

    def set_telegram_webhook(self, webhook_url):
        try:
            self.bot.api.setWebhook(webhook_url)
        except Exception:
            e = traceback.format_exc()
            message = f"Can't set up webhook url `{webhook_url}`.\n{e}"
            logging.getLogger('evernotebot').fatal({'exception': message})


app = EvernoteBotApplication()
