import json
import logging
from datetime import datetime
from time import time

from bot.models import MessageLogEntry
from util.http import HTTPFound
from telegram.models import TelegramUpdate


def telegram_hook(request):
    start_ts = time()
    bot = request.app.bot
    log_entry = bot.get_storage(MessageLogEntry).create_model({})
    logging.getLogger().info('Telegram update: {}'.format(request.body))
    data = request.json()
    telegram_update = TelegramUpdate(data)
    bot.handle_telegram_update(telegram_update)
    log_entry.user_id = telegram_update.message.from_user.id
    log_entry.message_type = telegram_update.message.get_type()
    log_entry.request_duration = time() - start_ts
    log_entry.save()


def evernote_oauth(request):
    callback_key = request.GET['key']
    oauth_verifier = request.GET.get('oauth_verifier')
    access = request.GET.get('access', 'basic')
    bot = request.app.bot
    bot.oauth_callback(callback_key, oauth_verifier, access)
    return HTTPFound(bot.url)
