import traceback
from aiohttp import web


async def handle_update(request):
    data = await request.json()

    request.app.logger.info(request.path_qs)
    request.app.logger.info(str(data))

    try:
        await request.app.bot.handle_update(data)
    except Exception:
        request.app.logger.fatal(traceback.format_exc())

    return web.Response(body=b'ok')
