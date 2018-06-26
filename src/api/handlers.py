import json
import logging
from bot.core import EvernoteBot
from datetime import datetime
from telegram.models import TelegramUpdate


def telegram_hook(request):
    logger = logging.getLogger()
    logger.info('Telegram update: {}'.format(request.body))
    data = request.body.decode()
    if isinstance(data, str):
        data = json.loads(data)
    bot = EvernoteBot()
    telegram_update = TelegramUpdate(data)
    bot.handle_telegram_update(telegram_update)


def evernote_oauth(request):
    return b'evernote_oauth'


def error(request):
    raise Exception('Some application error')
