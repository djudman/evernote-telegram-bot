from urllib.parse import parse_qs
from aiohttp import web


async def oauth_callback(request):
    logger = request.app.logger
    robot = request.app.bot
    params = parse_qs(request.query_string)
    callback_key = params.get('key', [''])[0]

    session = await robot.get_start_session(callback_key)
    if not session:
        return web.HTTPForbidden()

    if params.get('oauth_verifier'):
        oauth_verifier = params['oauth_verifier'][0]
        # TODO: async
        access_token = robot.evernote.get_access_token(
            session['oauth_token'],
            session['oauth_token_secret'],
            oauth_verifier)

        logger.info('evernote access_token = %s' % access_token)
        await robot.register_user(session, access_token)

        notebook = robot.evernote.getDefaultNotebook(access_token)
        text = "Evernote account is connected.\n\
Now you can just send message and note be created.\n\
Current notebook: %s" % notebook.name
        await robot.send_message(session['user_id'], text)
    else:
        # User decline access
        logger.info('User declined access. No access token =(')
        text = "We are sorry, but you declined authorization 😢"
        await robot.send_message(session['user_id'], text)

    return web.HTTPFound(robot.bot_url)
