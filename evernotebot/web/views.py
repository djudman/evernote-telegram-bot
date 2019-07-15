import logging
import re
import traceback
from time import time

from uhttp.core import HTTPFound, Request

from evernotebot.bot.core import EvernoteBotException
from evernotebot.bot.shortcuts import evernote_oauth_callback


def telegram_hook(request: Request):
    data = request.json()
    bot = request.app.bot
    try:
        bot.process_update(data)
    except Exception:
        str_exc = traceback.format_exc()
        failed_update = {
            "created": time(),
            "data": data,
            "exception": str_exc,
        }
        entry_id = bot.failed_updates.create(failed_update, auto_generate_id=True)
        logging.getLogger("evernotebot").error({
            "exception": str_exc,
            "failed_update_id": entry_id,
        })


def evernote_oauth(request: Request):
    params = request.GET
    bot = request.app.bot
    callback_key = params["key"]
    if not re.match(r"^[a-z0-9]{40}$", callback_key):
        raise EvernoteBotException("Invalid callback key")
    access_type = params.get("access")
    if access_type not in ("basic", "full"):
        raise EvernoteBotException("Invalid access")
    evernote_oauth_callback(
        bot,
        callback_key=callback_key,
        oauth_verifier=params.get("oauth_verifier"),
        access_type=access_type,
    )
    return HTTPFound(bot.url)
