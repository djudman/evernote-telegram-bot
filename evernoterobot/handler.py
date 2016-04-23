from aiohttp import web


async def handle_update(request):
    data = await request.text()
    request.app.logger.info(request.path_qs)
    request.app.logger.info(str(data))
    return web.Response(body=b'ok')
