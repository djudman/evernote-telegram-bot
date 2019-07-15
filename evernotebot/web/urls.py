from urllib.parse import urlparse

from evernotebot.config import load_config
from evernotebot.web.views import telegram_hook, evernote_oauth


config = load_config()
secret = config["secret"]
webhook_url = config["telegram"]["webhook_url"]
webhook_path = urlparse(webhook_url).path

urls = (
    ("POST", r"^{}$".format(webhook_path), telegram_hook),
    ("GET", r"^/evernote/oauth/{}$".format(secret), evernote_oauth),
)
