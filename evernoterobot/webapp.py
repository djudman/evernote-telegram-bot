import sys
import logging
import logging.config

from aiohttp import web

import settings
from telegram.api import BotApi
from handler import handle_update

sys.path.insert(0, settings.PROJECT_DIR)


app = web.Application()
app.router.add_route('POST', '/%s' % settings.SECRET['token'], handle_update)

logging.config.dictConfig(settings.LOG_SETTINGS)
app.logger = logging.getLogger('aiohttp.server')

bot = BotApi(settings.SECRET['token'])
bot.sync_call(bot.setWebhook(settings.WEBHOOK_URL))
