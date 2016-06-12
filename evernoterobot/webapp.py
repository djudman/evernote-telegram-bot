import sys
import logging
import logging.config

import aiohttp
import aiomcache
from motor.motor_asyncio import AsyncIOMotorClient

import settings
from telegram.robot import EvernoteRobot
# from bot import EvernoteBot
from web.telegram import handle_update
from web.evernote import oauth_callback
from telegram.api import BotApi
from evernotelib.client import EvernoteClient

sys.path.insert(0, settings.PROJECT_DIR)

logging.config.dictConfig(settings.LOG_SETTINGS)


telegram_api = BotApi(settings.TELEGRAM['token'])

evernote_client = EvernoteClient(
        settings.EVERNOTE['key'],
        settings.EVERNOTE['secret'],
        settings.EVERNOTE['oauth_callback'],
        sandbox=settings.DEBUG
    )

db_client = AsyncIOMotorClient(settings.MONGODB_URI)
memcached_client = aiomcache.Client("127.0.0.1", 11211)
bot = EvernoteRobot(telegram_api, evernote_client, db_client, memcached_client)

app = aiohttp.web.Application()
app.logger = logging.getLogger()

app.router.add_route('POST', '/%s' % settings.TELEGRAM['token'], handle_update)
app.router.add_route('GET', '/evernote/oauth', oauth_callback)

if settings.DEBUG:
    app.router.add_route('GET', '/', handle_update)

app.loop.run_until_complete(
    bot.telegram.setWebhook(settings.TELEGRAM['webhook_url'])
)

app.bot = bot
app.db = db_client


async def on_cleanup(app):
    app.db.close()


app.on_cleanup.append(on_cleanup)
