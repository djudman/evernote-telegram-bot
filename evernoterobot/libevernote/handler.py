from aiohttp import web


async def oauth_callback(request):
    data = await request.text()
    request.app.logger.info('oauth_callback: %s' % data)
    return web.Response(body=b'ok')
