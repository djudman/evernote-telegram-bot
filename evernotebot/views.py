import logging
import traceback
from time import time

from util.http import HTTPFound, Request

from evernotebot.bot.shortcuts import evernote_oauth_callback, OauthParams


def telegram_hook(request: Request):
    data = request.json()
    bot = request.app.bot
    try:
        bot.process_update(data)
    except Exception:
        message = f'Telegram update failed. Data: `{data}`'
        logging.getLogger('evernotebot').error(message, exc_info=True)
        bot.failed_updates.create({
            'created': time(),
            'data': data,
            'exception': traceback.format_exc(),
        }, auto_generate_id=True)
    return ''


def evernote_oauth(request: Request):
    bot = request.app.bot
    params = request.GET
    callback_key = params['key']
    access_type = params['access']
    verifier = params.get('oauth_verifier')
    oauth_params = OauthParams(callback_key, verifier, access_type)
    evernote_oauth_callback(bot, oauth_params)
    return HTTPFound(bot.url)
