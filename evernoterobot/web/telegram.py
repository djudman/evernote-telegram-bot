import asyncio
from aiohttp import web


async def handle_update(request):
    try:
        data = await request.json()
        request.app.logger.info(request.path_qs)
        request.app.logger.info(str(data))
        asyncio.ensure_future(request.app.bot.handle_update(data))
    except Exception as e:
        request.app.logger.fatal(e, exc_info=1)

    return web.Response(body=b'ok')
