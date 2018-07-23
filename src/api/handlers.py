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
    try:
        status_message = bot.api.sendMessage(chat_id, 'Accepted')
        bot.handle_telegram_update(telegram_update)
    except Exception as e:
        chat_id = telegram_update.message.chat.id
        bot.api.sendMessage(chat_id, str(e)) # TODO: form error message


def evernote_oauth(request):
    return b'evernote_oauth'


def error(request):
    raise Exception('Some application error')
