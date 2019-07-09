import traceback
from time import time
from os.path import join

from uhttp.core import HTTPFound, Request, Response
from uhttp.shortcuts import restricted

from evernotebot.config import load_config
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


def html(filename):
    def handler(request):
        config = load_config()
        nonlocal filename
        filename = join(config["html_root"], filename)
        with open(filename, "r") as f:
            data = f.read().encode()
        return Response(data, headers=[('Content-Type', 'text/html')])
    return handler

@restricted
def get_logs(request: Request):
    raise Exception("Not implemented")


@restricted
def retry_failed_update(request: Request):
    raise Exception("Not implemented")


@restricted
def send_broadcast_message(request: Request):  # to all users
    raise Exception("Not implemented")
