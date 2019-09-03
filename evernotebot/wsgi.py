import atexit
import functools
import logging
from os.path import dirname, realpath

from uhttp import WsgiApplication

from evernotebot.config import load_config
from evernotebot.bot.core import EvernoteBot
from evernotebot.views import telegram_hook, evernote_oauth


class EvernoteBotApplication(WsgiApplication):
    def __init__(self):
        config = load_config()
        self.config = config
        super().__init__(
            src_root=realpath(dirname(__file__)),
            urls=self.get_urls(),
            config=config
        )
        self.bot = EvernoteBot(config)

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
            message = f"Can't set up webhook url `{webhook_url}`"
            logging.getLogger('evernotebot').fatal(message, exc_info=True)


def shutdown(app):
    app.bot.stop()


app = EvernoteBotApplication()
atexit.register(functools.partial(shutdown, app))

webhook_url = app.config['telegram']['webhook_url']
app.set_telegram_webhook(webhook_url)
