import hashlib
import json
import math
import random
import string
from time import time

from uhttp.auth import login, auth_required
from uhttp.core import HTTPFound, Request, Response


def api_response(status=True, data=None, error=None, headers=None):
    response = { "status": status }
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    body = json.dumps(response)
    return Response(body, headers=headers)


def api_login(request: Request):
    response = login(request)
    if response:
            return api_response(data={"token": response.body.decode()}, headers=response.headers)
    return api_response(False, error="Access denied")


@auth_required
def api_get_logs(request: Request):
    request.no_log = True
    config = request.app.config
    filename = str(config["logging"]["handlers"]["evernotebot"]["filename"])
    data = []
    with open(filename, "r") as f:
        for line in f:
            data.insert(0, json.loads(line))
    total_cnt = len(data)
    page = int(request.GET.get("page", 1)) - 1
    page_size = int(request.GET.get("page_size", 10))
    num_pages = math.ceil(total_cnt / page_size)
    start = page_size * page
    data = {
        "total": total_cnt,
        "num_pages": num_pages,
        "data": data[start:(start + page_size)],
    }
    return api_response(data=data)


@auth_required
def api_list_failed_updates(request: Request):
    bot = request.app.bot
    bot.failed_updates.get_all()
    return api_response(error="Not implemented")


@auth_required
def api_retry_failed_update(request: Request):
    return api_response(error="Not implemented")


@auth_required
def api_send_broadcast_message(request: Request):  # to all users
    return api_response(error="Not implemented")
