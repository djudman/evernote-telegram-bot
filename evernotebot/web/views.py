import traceback
from time import time

from uhttp.core import HTTPFound

from evernotebot.bot.shortcuts import evernote_oauth_callback


def telegram_hook(request):
    data = request.json()
    bot = request.app.bot
    try:
        bot.process_update(data)
    except Exception:
        failed_update = {
            "created": time(),
            "data": data,
            "exception": traceback.format_exc(),
        }
        bot.failed_updates.create(failed_update, auto_generate_id=True)


def evernote_oauth(request):
    params = request.GET
    bot = request.app.bot
    evernote_oauth_callback(
        bot,
        callback_key=params["key"],
        oauth_verifier=params.get("oauth_verifier"),
        access_type=params.get("access")
    )
    return HTTPFound(bot.url)
