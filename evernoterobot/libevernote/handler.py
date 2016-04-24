from urllib.parse import parse_qs
from aiohttp import web


async def oauth_callback(request):
    logger = request.app.logger
    logger.info("oauth_callback(). query string: %s" % request.query_string)
    params = parse_qs(request.query_string)
    logger.info("oauth_token: %s" % params['oauth_token'])
    logger.info("oauth_verifier: %s" % params['oauth_verifier'])
    # TODO: get access token
    return web.HTTPFound('https://telegram.me/evernoterobot')
