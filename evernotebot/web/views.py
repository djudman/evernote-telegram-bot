import logging
import math
import re
import traceback
from time import time
from os.path import join

from uhttp.core import HTTPFound, Request, Response
from uhttp.shortcuts import restricted

from evernotebot.config import load_config
from evernotebot.bot.core import EvernoteBotException
from evernotebot.bot.shortcuts import evernote_oauth_callback


def telegram_hook(request):
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


def evernote_oauth(request):
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


def html(filename):
    @restricted
    def handler(request):
        config = load_config()
        nonlocal filename
        filename = join(config["html_root"], filename)
        with open(filename, "r") as f:
            data = f.read().encode()
        return Response(data, headers=[('Content-Type', 'text/html')])
    return handler


@restricted
def api_get_logs(request: Request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))
    filename = config["logging"]["handlers"]["evernotebot"]["filename"]
    with open(filename, "r") as f:
        lines = reversed(f.readlines())
    total_cnt = len(lines)
    num_pages = math.ceil(total_cnt / page_size)
    index = page_size * page
    return {
        "total": total_cnt,
        "num_pages": num_pages,
        "data": lines[index:index + page_size],
    }


@restricted
def api_list_failed_updates(request: Request):
    bot = request.app.bot
    bot.failed_updates.get_all()
    raise Exception("Not implemented")


@restricted
def api_retry_failed_update(request: Request):
    raise Exception("Not implemented")


@restricted
def api_send_broadcast_message(request: Request):  # to all users
    raise Exception("Not implemented")
