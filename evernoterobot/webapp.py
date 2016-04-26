import sys
import logging
import logging.config

from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient

import settings
from telegram.robot import EvernoteRobot
from telegram.handler import handle_update
from libevernote.handler import oauth_callback

sys.path.insert(0, settings.PROJECT_DIR)

logging.config.dictConfig(settings.LOG_SETTINGS)

bot = EvernoteRobot(settings.SECRET['token'], {
        'key': settings.SECRET['evernote']['key'],
        'secret': settings.SECRET['evernote']['secret'],
        'oauth_callback': settings.EVERNOTE_OAUTH_CALLBACK,
    })

app = web.Application()
app.logger = logging.getLogger()

app.router.add_route('POST', '/%s' % settings.SECRET['token'], handle_update)
app.router.add_route('GET', '/evernote/oauth', oauth_callback)

if settings.DEBUG:
    app.router.add_route('GET', '/', handle_update)

app.loop.run_until_complete(bot.api.setWebhook(settings.WEBHOOK_URL))

app.bot = bot
app.db = AsyncIOMotorClient(settings.MONGODB_URI)


async def on_cleanup(app):
    app.db.close()


app.on_cleanup.append(on_cleanup)
