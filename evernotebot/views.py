from evernotebot.util.http import HTTPFound, Request

from evernotebot.bot.shortcuts import evernote_oauth_callback, OauthParams


def telegram_hook(request: Request):
    data = request.json()
    bot = request.app.bot
    try:
        bot.process_update(data)
    except Exception:
        bot.fail_update(data)
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
