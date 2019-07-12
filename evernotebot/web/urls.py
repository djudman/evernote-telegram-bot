from urllib.parse import urlparse

from evernotebot.config import load_config
from evernotebot.web.views import (
    telegram_hook, evernote_oauth, api_get_logs, api_retry_failed_update,
    api_login, api_send_broadcast_message, api_list_failed_updates, html
)


config = load_config()
secret = config["secret"]
webhook_url = config["telegram"]["webhook_url"]
webhook_path = urlparse(webhook_url).path

urls = (
    # Bot hooks
    ("POST", r"^{}$".format(webhook_path), telegram_hook),
    ("GET", r"^/evernote/oauth/{}$".format(secret), evernote_oauth),
    # View
    ("GET", r"^/$", html("dashboard.html")),
    ("GET", r"^/logs$", html("logs.html")),
    ("GET", r"^/retry$", html("retrying.html")),
    # API
    ("GET", r"^/api/login$", api_login),
    ("GET", r"^/api/logs$", api_get_logs),
    ("GET", r"^/api/failed_updates", api_list_failed_updates),
    ("POST", r"^/api/retry$", api_retry_failed_update),
    ("POST", r"^/api/broadcast$", api_send_broadcast_message),
)
