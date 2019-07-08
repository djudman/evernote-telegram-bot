from urllib.parse import urlparse

from evernotebot.config import load_config
from evernotebot.web.views import telegram_hook, evernote_oauth, get_logs,\
    retry_failed_update, send_broadcast_message, html


config = load_config()
webhook_url = config["webhook_url"]
webhook_path = urlparse(webhook_url).path

urls = (
    # Bot hooks
    ("POST", r"^{}$".format(webhook_path), telegram_hook),
    ("GET", r"^/evernote/oauth$", evernote_oauth),
    # View
    ("GET", r"^/$", html("dashboard.html")),
    ("GET", r"^/logs$", html("logs.html")),
    ("GET", r"^/retry$", html("retrying.html")),
    # API
    ("GET", r"^/api/logs$", get_logs),
    ("POST", r"^/api/retry$", retry_failed_update),
    ("POST", r"^/api/broadcast$", send_broadcast_message),
)
