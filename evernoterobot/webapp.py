import logging
import logging.config

from aiohttp import web

import settings


async def handle_update(request):
    data = await request.text()
    request.app.logger.info(data)
    return web.Response(body=b'ok')


app = web.Application()
app.router.add_route('POST', '/%s' % settings.SECRET['token'], handle_update)

logging.config.dictConfig(settings.LOG_SETTINGS)
app.logger = logging.getLogger('aiohttp.server')
