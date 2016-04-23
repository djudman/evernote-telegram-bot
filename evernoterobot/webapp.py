import sys
import logging
import logging.config

from aiohttp import web

import settings
from telegram.api import BotApi

sys.path.insert(0, settings.PROJECT_DIR)


async def handle_update(request):
    data = await request.text()
    request.app.logger.info(data)
    return web.Response(body=b'ok')


app = web.Application()
app.router.add_route('POST', '/%s' % settings.SECRET['token'], handle_update)

logging.config.dictConfig(settings.LOG_SETTINGS)
app.logger = logging.getLogger('aiohttp.server')

bot = BotApi(settings.SECRET['token'])
bot.setWebhook(settings.WEBHOOK_URL)
