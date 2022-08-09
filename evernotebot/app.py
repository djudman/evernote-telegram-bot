import atexit
import json
import logging

from evernotebot import EvernoteBot
from evernotebot.config import load_config
from evernotebot.util.asgi import AsgiApplication
from evernotebot.views import evernote_oauth, telegram_hook


class EvernoteBotApplication(AsgiApplication):
    def __init__(self, host: str = None, port: int = None):
        config = load_config()
        self.config = config
        bot_api_token = config['telegram']['token']
        host = host or '127.0.0.1'
        port = port or 8000
        url_schema = (
            ('POST', f'^/{bot_api_token}$', telegram_hook),  # webhook_url
            ('GET', r'^/evernote/oauth$', evernote_oauth),  # oauth_callback_url
        )
        super().__init__(url_schema)
        atexit.register(self.shutdown)
        self.bot = EvernoteBot(config)
        webhook_url = config['webhook_url']
        try:
            self.bot.api.setWebhook(webhook_url)
        except Exception:
            message = f"Can't set up webhook url `{webhook_url}`"
            logging.getLogger('evernotebot').fatal(message, exc_info=True)
        logging.getLogger('evernotebot').info(json.dumps(self.config, indent=4))

    def shutdown(self):
        self.bot.stop()
