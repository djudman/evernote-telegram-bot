import functools
import json
from urllib.parse import parse_qs

import asyncio
from aiohttp import web
from requests_oauthlib.oauth1_session import TokenRequestDenied

import settings
from bot.model import User, StartSession, ModelNotFound


async def oauth_callback(request):
    logger = request.app.logger
    bot = request.app.bot
    config = settings.EVERNOTE['basic_access']

    params = parse_qs(request.query_string)
    callback_key = params.get('key', [''])[0]
    session_key = params.get('session_key')[0]

    try:
        session = StartSession.get({'oauth_data.callback_key': callback_key})
        user_data = session.data['user']
        first_name = user_data['first_name']
        last_name = user_data['last_name']
        username = user_data['username']
        user = User(id=session.id,
                    name="{0} {1} [{2}]".format(first_name, last_name, username),
                    telegram_chat_id=session.data['chat_id'],
                    mode='multiple_notes',
                    places={},
                    settings={'evernote_access': 'basic'},
                    username=username,
                    first_name=first_name,
                    last_name=last_name)
    except ModelNotFound as e:
        logger.error(e, exc_info=1)
        return web.HTTPForbidden()

    if session.key != session_key:
        text = "Session is expired. Please, send /start command to create new session"
        asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))
        return web.HTTPFound(bot.url)

    try:
        if params.get('oauth_verifier'):
            future = asyncio.ensure_future(
                bot.evernote_api.get_access_token(
                    config['key'],
                    config['secret'],
                    session.oauth_data['oauth_token'],
                    session.oauth_data['oauth_token_secret'],
                    params['oauth_verifier'][0]
                )
            )
            future.add_done_callback(functools.partial(set_access_token, bot, user))
            text = 'Evernote account is connected.\nFrom now you can just send message and note be created.'
            asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))
            user.save()
        else:
            # User decline access
            logger.info('User declined access. No access token =(')
            text = "We are sorry, but you declined authorization 😢"
            asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))

    except TokenRequestDenied as e:
        logger.error(e, exc_info=1)
        text = "We are sorry, but we have some problems with Evernote connection. Please try again later"
        asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))
    except Exception as e:
        logger.fatal(e, exc_info=1)
        text = "Oops. Unknown error. Our best specialist already working to fix it"
        if user:
            asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))

    return web.HTTPFound(bot.url)


def set_access_token(bot, user, future_access_token):
    access_token = future_access_token.result()
    user.evernote_access_token = access_token
    user.save()
    future = asyncio.ensure_future(bot.evernote_api.get_default_notebook(access_token))
    future.add_done_callback(functools.partial(on_notebook_info, bot, user))


def on_notebook_info(bot, user, future_notebook):
    notebook = future_notebook.result()
    user.current_notebook = {
        'guid': notebook.guid,
        'name': notebook.name,
    }
    text = 'Current notebook: %s\nCurrent mode: %s' % (notebook.name, user.mode.replace('_', ' ').capitalize())
    asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))
    user.save()


async def oauth_callback_full_access(request):
    logger = request.app.logger
    bot = request.app.bot
    hide_keyboard_markup = json.dumps({'hide_keyboard': True})
    params = parse_qs(request.query_string)
    callback_key = params.get('key', [''])[0]
    session_key = params.get('session_key')[0]

    try:
        session = StartSession.get({'oauth_data.callback_key': callback_key})
        user = User.get({'id': session.id})
    except ModelNotFound as e:
        logger.error(e, exc_info=1)
        return web.HTTPForbidden()

    if session.key != session_key:
        text = "Session is expired. Please, send /start command to create new session"
        asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))
        return web.HTTPFound(bot.url)

    try:
        if params.get('oauth_verifier'):
            oauth_verifier = params['oauth_verifier'][0]
            config = settings.EVERNOTE['full_access']
            future = asyncio.ensure_future(
                bot.evernote_api.get_access_token(
                    config['key'],
                    config['secret'],
                    session.oauth_data['oauth_token'],
                    session.oauth_data['oauth_token_secret'],
                    oauth_verifier)
            )
            future.add_done_callback(functools.partial(switch_to_one_note_mode, bot, user.id))
            text = 'From now this bot in "One note" mode'
            asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text, hide_keyboard_markup))
        else:
            # User decline access
            logger.info('User declined full access =(')
            text = "We are sorry, but you deny read/update access😢"
            asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text, hide_keyboard_markup))

    except TokenRequestDenied as e:
        logger.error(e, exc_info=1)
        text = "We are sorry, but we have some problems with Evernote connection. Please try again later"
        asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text, hide_keyboard_markup))
    except Exception as e:
        logger.fatal(e, exc_info=1)
        text = "Oops. Unknown error. Our best specialist already working to fix it"
        asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text, hide_keyboard_markup))

    return web.HTTPFound(bot.url)


def switch_to_one_note_mode(bot, user_id, access_token_future):
    user = User.get({'id': user_id})
    access_token = access_token_future.result()
    user.evernote_access_token = access_token
    user.settings['evernote_access'] = 'full'
    user.mode = 'one_note'
    user.save()
    future = asyncio.ensure_future(
        bot.evernote_api.new_note(user.evernote_access_token,
                                  user.current_notebook['guid'],
                                  text='',
                                  title='Note for Evernoterobot')
    )
    future.add_done_callback(functools.partial(save_default_note_guid, user_id))


def save_default_note_guid(user_id, note_guid_future):
    user = User.get({'id': user_id})
    note_guid = note_guid_future.result()
    user.places[user.current_notebook['guid']] = note_guid
    user.save()
