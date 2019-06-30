import traceback
from os.path import dirname, realpath
from urllib.parse import urlparse

from uhttp import WsgiApplication
from uhttp.core import HTTPFound
from utelegram.bot import TelegramBotError
from utelegram.models import Update

from evernotebot.config import load_config
from evernotebot.bot.core import EvernoteBot
from evernotebot.bot.shortcuts import evernote_oauth_callback


def telegram_hook(request):
    data = request.json()
    telegram_update = Update(**data)
    request.app.bot.process_update(telegram_update)


def evernote_oauth(request):
    bot = request.app.bot
    evernote_oauth_callback(
        bot,
        callback_key=request.GET['key'],
        oauth_verifier=request.GET.get('oauth_verifier'),
        access_type=request.GET.get('access')
    )
    return HTTPFound(bot.url)


def create_app():
    config = load_config()
    webhook_url = config['webhook_url']
    webhook_path = urlparse(webhook_url).path
    src_root = realpath(dirname(__file__))
    app = WsgiApplication(src_root, config=config, urls=(
        ('POST', webhook_path, telegram_hook),
        ('GET', r'^/evernote/oauth$', evernote_oauth),
    ))
    app.bot = EvernoteBot(config)
    return app


app = create_app()
webhook_url = app.config['webhook_url']
try:
    app.bot.api.setWebhook(webhook_url)
except Exception as e:
    str_traceback = ''.join(traceback.format_tb(e.__traceback__))
    message = f"Can't set up webhook url `{webhook_url}`. "\
              f"Exception:\n{str_traceback}"
    app.log(level='error', message=message)
