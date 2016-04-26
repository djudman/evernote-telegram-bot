from urllib.parse import parse_qs
from aiohttp import web


async def oauth_callback(request):
    logger = request.app.logger
    params = parse_qs(request.query_string)
    callback_key = params.get('key', '')

    key_info = await request.app.bot.verify_callback_key(callback_key)
    if not key_info:
        return web.HTTPForbidden()

    oauth_token = params['oauth_token'][0]
    if params.get('oauth_verifier'):
        oauth_verifier = params['oauth_verifier'][0]
        access_token = request.app.bot.evernote.get_access_token(
            oauth_token, oauth_verifier)
        logger.info('evernote access_token = %s' % access_token)
    else:
        # User decline access
        logger.info('User declined access. No access token =(')

    return web.HTTPFound('https://telegram.me/evernoterobot')
