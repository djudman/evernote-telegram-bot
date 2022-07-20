import atexit
import logging

from evernotebot import EvernoteBot
from evernotebot.config import load_config
from evernotebot.views import telegram_hook, evernote_oauth
from evernotebot.util.wsgi import WsgiApplication


class EvernoteBotApplication(WsgiApplication):
    def __init__(self, host: str = None, port: int = None):
        config = load_config()
        self.config = config
        bot_api_token = config['telegram']['token']
        if not host or not port:
            host, port = config['host'].split(':', 1)
            port = port or 8080
        url_schema = (
            ('POST', f'^/{bot_api_token}$', telegram_hook),  # webhook_url
            ('GET', r'^/evernote/oauth$', evernote_oauth),  # oauth_callback_url
        )
        super().__init__(url_schema, bind=f'{host}:{port}')
        atexit.register(self.shutdown)
        self.bot = EvernoteBot(config)
        webhook_url = config['webhook_url']
        try:
            self.bot.api.setWebhook(webhook_url)
        except Exception:
            message = f"Can't set up webhook url `{webhook_url}`"
            logging.getLogger('evernotebot').fatal(message, exc_info=True)

    def shutdown(self):
        self.bot.stop()
