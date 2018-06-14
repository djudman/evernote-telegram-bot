import json
import logging
from datetime import datetime
from telegram.models import TelegramUpdate


def telegram_hook(request):
    logger = logging.getLogger()
    logger.info('Telegram update: {}'.format(request.body))
    data = request.body.decode()
    if isinstance(data, str):
        data = json.loads(data)
    return str(data)


def evernote_oauth(request):
    return b'evernote_oauth'


def error(request):
    raise Exception('Some application error')
