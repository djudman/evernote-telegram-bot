from urllib.parse import parse_qs

import asyncio
from aiohttp import web
from requests_oauthlib.oauth1_session import TokenRequestDenied

import settings
from bot.model import User, StartSession, ModelNotFound


async def oauth_callback(request):
    logger = request.app.logger
    bot = request.app.bot

    try:
        params = parse_qs(request.query_string)
        callback_key = params.get('key', [''])[0]

        session = StartSession.get({'oauth_data.callback_key': callback_key})
        user = User.get({'id': session.user_id})

        if params.get('oauth_verifier'):
            oauth_verifier = params['oauth_verifier'][0]
            # TODO: async
            access_token = bot.evernote.get_access_token(
                session.oauth_data['oauth_token'],
                session.oauth_data['oauth_token_secret'],
                oauth_verifier)

            logger.info('evernote access_token = %s' % access_token)

            notebook = bot.evernote.getDefaultNotebook(access_token)

            user.evernote_access_token = access_token
            user.current_notebook = {
                'guid': notebook.guid,
                'name': notebook.name,
            }
            user.save()

            if user.mode == 'one_note' and not hasattr(user, 'places'):
                note_guid = bot.evernote.create_note(
                    access_token, text='', title='Note for Evernoterobot')
                user.places = {
                    user.current_notebook['guid']: note_guid
                }
                user.save()

            text = "Evernote account is connected.\n\
From now you can just send message and note be created.\n\
\n\
Current notebook: %s\n\
Current mode: %s" % (notebook.name, user.mode.replace('_', ' ').capitalize())

            await bot.api.sendMessage(user.telegram_chat_id, text)
        else:
            # User decline access
            logger.info('User declined access. No access token =(')
            text = "We are sorry, but you declined authorization 😢"
            await bot.api.sendMessage(user.telegram_chat_id, text)

    except TokenRequestDenied as e:
        logger.error(e, exc_info=1)
        text = "We are sorry, but we have some problems with Evernote connection. Please try again later"
        await bot.api.sendMessage(user.telegram_chat_id, text)
    except ModelNotFound as e:
        logger.error(e, exc_info=1)
        return web.HTTPForbidden()
    except Exception as e:
        logger.fatal(e, exc_info=1)
        text = "Oops. Unknown error. Our best specialist already working to fix it"
        await bot.api.sendMessage(user.telegram_chat_id, text)

    return web.HTTPFound(bot.url)


async def oauth_callback_full_access(request):
    logger = request.app.logger
    bot = request.app.bot
    try:
        params = parse_qs(request.query_string)
        callback_key = params.get('key', [''])[0]

        session = StartSession.get({'oauth_data.callback_key': callback_key})
        user = User.get({'id': session.user_id})

        if params.get('oauth_verifier'):
            oauth_verifier = params['oauth_verifier'][0]
            config = settings.EVERNOTE['full_access']
            access_token = await bot.evernote_api.get_access_token(
                config['key'],
                config['secret'],
                session.oauth_data['oauth_token'],
                session.oauth_data['oauth_token_secret'],
                oauth_verifier)

            user.evernote_access_token = access_token
            user.settings['evernote_access'] = 'full'
            user.mode = 'one_note'
            # TODO: async
            note_guid = bot.evernote.create_note(user.evernote_access_token, text='', title='Note for Evernoterobot')
            user.places[user.current_notebook['guid']] = note_guid
            user.save()
            text = 'From now this bot in "One note" mode'
            asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))
        else:
            # User decline access
            logger.info('User declined full access =(')
            text = "We are sorry, but you deny read/update access😢"
            asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))

    except TokenRequestDenied as e:
        logger.error(e, exc_info=1)
        text = "We are sorry, but we have some problems with Evernote connection. Please try again later"
        asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))
    except ModelNotFound as e:
        logger.error(e, exc_info=1)
        return web.HTTPForbidden()
    except Exception as e:
        logger.fatal(e, exc_info=1)
        text = "Oops. Unknown error. Our best specialist already working to fix it"
        asyncio.ensure_future(bot.api.sendMessage(user.telegram_chat_id, text))

    return web.HTTPFound(bot.url)
