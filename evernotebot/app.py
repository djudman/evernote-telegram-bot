import atexit
import logging
from os.path import dirname, realpath

from evernotebot.bot.core import EvernoteBot
from evernotebot.config import load_config
from evernotebot.views import telegram_hook, evernote_oauth
from util.wsgi import WsgiApplication


class EvernoteBotApplication(WsgiApplication):
    def __init__(self):
        config = load_config()
        webhook_url = 'https://{host}/{token}'.format(
            host=config['host'], token=config['telegram']['token']
        )
        self.config = config
        super().__init__(
            src_root=realpath(dirname(__file__)),
            urls=self.get_urls(),
            config=config
        )
        self.bot = EvernoteBot(config)
        atexit.register(self.shutdown)
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
            message = f"Can't set up webhook url `{webhook_url}`"
            logging.getLogger('evernotebot').fatal(message, exc_info=True)

    def shutdown(self):
        self.bot.stop()
