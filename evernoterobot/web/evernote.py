from urllib.parse import parse_qs
from aiohttp import web


async def oauth_callback(request):
    logger = request.app.logger
    bot = request.app.bot
    params = parse_qs(request.query_string)
    callback_key = params.get('key', [''])[0]

    session = await bot.get_start_session(callback_key)
    if not session:
        logger.error("Session for callback key = %s not found" % callback_key)
        return web.HTTPForbidden()

    if params.get('oauth_verifier'):
        oauth_verifier = params['oauth_verifier'][0]
        # TODO: async
        access_token = bot.evernote.get_access_token(
            session.oauth_token,
            session.oauth_token_secret,
            oauth_verifier)

        logger.info('evernote access_token = %s' % access_token)
        await bot.register_user(session, access_token)

        notebook = bot.evernote.getDefaultNotebook(access_token)
        text = "Evernote account is connected.\n\
Now you can just send message and note be created.\n\
Current notebook: %s" % notebook.name
        await bot.send_message(session.user_id, text)
    else:
        # User decline access
        logger.info('User declined access. No access token =(')
        text = "We are sorry, but you declined authorization 😢"
        await bot.send_message(session.user_id, text)

    return web.HTTPFound(bot.url)
