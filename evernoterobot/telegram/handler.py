from aiohttp import web


async def handle_update(request):
    data = await request.json()

    request.app.logger.info(request.path_qs)
    request.app.logger.info(str(data))

    await request.app.bot.handle_update(data)

    return web.Response(body=b'ok')
