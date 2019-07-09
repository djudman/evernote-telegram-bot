import logging
import traceback
from os.path import dirname, realpath

from uhttp import WsgiApplication

from evernotebot.config import load_config
from evernotebot.bot.core import EvernoteBot
from evernotebot.web.urls import urls


config = load_config()
src_root = realpath(dirname(__file__))
app = WsgiApplication(src_root, config=config, urls=urls)
app.bot = EvernoteBot(config)

webhook_url = config["telegram"]["webhook_url"]
try:
    app.bot.api.setWebhook(webhook_url)
except Exception:
    e = traceback.format_exc()
    message = f"Can't set up webhook url `{webhook_url}`.\n{e}"
    logging.getLogger('evernotebot').fatal({"exception": message})
