import sys
import logging
import logging.config
from multiprocessing import Lock
import asyncio

from aiohttp import web

import settings
from telegram.robot import EvernoteRobot
from telegram.handler import handle_update
from libevernote.handler import oauth_callback

sys.path.insert(0, settings.PROJECT_DIR)

memcached_lock = Lock()

bot = EvernoteRobot(settings.SECRET['token'], {
        'key': settings.SECRET['evernote']['key'],
        'secret': settings.SECRET['evernote']['secret'],
        'oauth_callback': settings.EVERNOTE_OAUTH_CALLBACK,
    })

app = web.Application()
app.router.add_route('POST', '/%s' % settings.SECRET['token'], handle_update)
app.router.add_route('GET', '/evernote/oauth', oauth_callback)

if settings.DEBUG:
    app.router.add_route('GET', '/', handle_update)

logging.config.dictConfig(settings.LOG_SETTINGS)
app.logger = logging.getLogger()

asyncio.ensure_future(bot.api.setWebhook(settings.WEBHOOK_URL))

app.bot = bot
app.memcached_lock = memcached_lock
