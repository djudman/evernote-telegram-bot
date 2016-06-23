import sys
import logging
import logging.config
from os.path import realpath, dirname

import aiohttp

sys.path.insert(0, realpath(dirname(dirname(__file__))))

import settings
from bot import EvernoteBot
from web.telegram import handle_update
from web.evernote import oauth_callback

sys.path.insert(0, settings.PROJECT_DIR)

logging.config.dictConfig(settings.LOG_SETTINGS)

bot = EvernoteBot(settings.TELEGRAM['token'], 'evernoterobot')

app = aiohttp.web.Application()
app.logger = logging.getLogger()

app.router.add_route('POST', '/%s' % settings.TELEGRAM['token'], handle_update)
app.router.add_route('GET', '/evernote/oauth', oauth_callback)

if settings.DEBUG:
    app.router.add_route('GET', '/', handle_update)

app.loop.run_until_complete(
    bot.api.setWebhook(settings.TELEGRAM['webhook_url'])
)

app.bot = bot


# async def on_cleanup(app):
#     app.db.close()


# app.on_cleanup.append(on_cleanup)
