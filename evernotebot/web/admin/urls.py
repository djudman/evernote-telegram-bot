from functools import partial
from uhttp.handlers import html, file

from evernotebot.web.admin.api import (
    api_get_logs, api_retry_failed_update, api_login,
    api_send_broadcast_message, api_list_failed_updates
)


authenticated_html = partial(html, auth_required=True, login_url="/login")
js_file = partial(file, content_type="text/javascript")
css_file = partial(file, content_type="text/css")

urls = (
    # static
    ("GET", r"^/evernotebot.js", js_file("js/evernotebot.js")),
    ("GET", r"^/evernotebot.css", css_file("css/evernotebot.css")),
    # View
    ("GET", r"^/login$", html("login.html")),
    ("GET", r"^/$", authenticated_html("dashboard.html")),
    ("GET", r"^/logs$", authenticated_html("logs.html")),
    ("GET", r"^/retry$", authenticated_html("retrying.html")),
    # API
    ("GET", r"^/api/login$", api_login),
    ("GET", r"^/api/logs$", api_get_logs),
    ("GET", r"^/api/failed_updates", api_list_failed_updates),
    ("POST", r"^/api/retry$", api_retry_failed_update),
    ("POST", r"^/api/broadcast$", api_send_broadcast_message),
)
