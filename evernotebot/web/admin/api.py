import hashlib
import json
import math
from time import time

from uhttp.core import HTTPFound, Request, Response
from uhttp.shortcuts import auth_required


def api_login(request: Request):
    username = request.GET["username"]
    password = request.GET["password"]
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    config = request.app.config
    admins = request.app.config["uhttp"]["admins"]
    secret = config["secret"]
    for admin_username, admin_password_hash in admins:
        if admin_username == username and admin_password_hash == password_hash:
            key = f"{time()}{secret}{password_hash}"
            auth_token = hashlib.sha256(key.encode()).hexdigest()
            headers = [
                ("Location", "/"),
                ("Set-Cookie", f"auth_token={auth_token}; Secure; SameSite=Strict")
            ]
            return Response(None, 302, headers=headers)
    return Response(None, 401)


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
    return {
        "total": total_cnt,
        "num_pages": num_pages,
        "data": data[start:(start + page_size)],
    }


@auth_required
def api_list_failed_updates(request: Request):
    bot = request.app.bot
    bot.failed_updates.get_all()
    raise Exception("Not implemented")


@auth_required
def api_retry_failed_update(request: Request):
    raise Exception("Not implemented")


@auth_required
def api_send_broadcast_message(request: Request):  # to all users
    raise Exception("Not implemented")
