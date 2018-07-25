import json
import logging
from datetime import datetime

from telegram.models import TelegramUpdate


def welcome(request):
    return b'Welcome!'


def telegram_hook(request):
    logger = logging.getLogger()
    logger.info('Telegram update: {}'.format(request.body))
    data = request.json()
    telegram_update = TelegramUpdate(data)
    bot = request.app.bot
    bot.handle_telegram_update(telegram_update)


def evernote_oauth(request):
    callback_key = request.GET['key']
    session_key = request.GET['session_key']
    oauth_verifier = request.GET.get('oauth_verifier')
    bot = request.app.bot
    bot.oauth_callback(callback_key, oauth_verifier, access='basic')

    return b'evernote_oauth'


def error(request):
    raise Exception('Some application error')
