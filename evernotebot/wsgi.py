import json
import hashlib
import logging
import traceback
from time import time
from os.path import dirname, realpath, join
from urllib.parse import urlparse

from uhttp import WsgiApplication
from uhttp.core import HTTPFound
from utelegram import Update, TelegramBotError

from evernotebot.config import load_config
from evernotebot.bot.core import EvernoteBot
from evernotebot.bot.shortcuts import evernote_oauth_callback


def _save_failed_update(dirpath: str, data: dict):
    current_time = time()
    key = "{time}{data}".format(time=current_time, data=data).encode()
    key_hash = hashlib.sha1(key).hexdigest()
    filename = join(dirpath, "{hash}.json".format(hash=key_hash))
    failed_update = {
        "created": current_time,
        "data": data,
        "exception": traceback.format_exc(),
    }
    with open(filename, 'w') as f:
        json.dump(failed_update, f)


def telegram_hook(request):
    data = request.json()
    bot = request.app.bot
    try:
        bot.process_update(data)
    except Exception as e:
        _save_failed_update(bot.config["failed_updates_root"], data)


def evernote_oauth(request):
    bot = request.app.bot
    evernote_oauth_callback(
        bot,
        callback_key=request.GET["key"],
        oauth_verifier=request.GET.get("oauth_verifier"),
        access_type=request.GET.get("access")
    )
    return HTTPFound(bot.url)


def create_app():
    config = load_config()
    webhook_url = config["webhook_url"]
    webhook_path = urlparse(webhook_url).path
    src_root = realpath(dirname(__file__))
    app = WsgiApplication(src_root, config=config, urls=(
        ("POST", webhook_path, telegram_hook),
        ("GET", r"^/evernote/oauth$", evernote_oauth),
    ))
    app.bot = EvernoteBot(config)
    return app


app = create_app()
webhook_url = app.config["webhook_url"]
try:
    app.bot.api.setWebhook(webhook_url)
except Exception:
    e = traceback.format_exc()
    message = f"Can't set up webhook url `{webhook_url}`.\n{e}"
    logging.getLogger('evernotebot').fatal({"exception": message})
