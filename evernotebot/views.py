import traceback

from evernotebot.bot.api import BotApiError
from evernotebot.bot.errors import EvernoteBotException
from evernotebot.util.http import HTTPFound, Request


def telegram_hook(request: Request):
    data = request.json()
    if data:
        bot = request.app.bot
        try:
            bot.process_update(data)
        except BotApiError as e:
            bot.logger.error(f'{traceback.format_exc()} {e}')
        return 'ok'
    return 'request body is empty'


def evernote_oauth(request: Request):
    bot = request.app.bot
    params = request.GET
    callback_key = params['key']
    access_type = params['access']
    if access_type not in {'basic', 'full'}:
        raise Exception(f'Invalid access type {access_type}')
    verifier = params.get('oauth_verifier')
    try:
        bot.evernote_auth(callback_key, access_type, verifier)
    except EvernoteBotException as e:
        bot.send_message(e.message)

    return HTTPFound(bot.url)
