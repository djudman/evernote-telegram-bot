import sys
import logging.config
from os.path import realpath, dirname, join

import aiohttp.web
import aiohttp_jinja2
import jinja2

from web.dashboard import list_downloads, list_failed_updates, login, dashboard, \
    list_updates, fix_failed_update

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

aiohttp_jinja2.setup(app,
    loader=jinja2.FileSystemLoader(
        join(dirname(__file__), 'html')
    )
)

secret_key = settings.SECRET['secret_key']

app.router.add_route('POST', '/%s' % settings.TELEGRAM['token'], handle_update)
app.router.add_route('GET', '/evernote/oauth', oauth_callback)

# dashboard
app.router.add_route('GET', '/a', login)
app.router.add_route('GET', '/a/dashboard/%s' % secret_key, dashboard)
app.router.add_route('GET', '/a/downloads/%s' % secret_key, list_downloads)
app.router.add_route('GET', '/a/failed_updates/%s' % secret_key, list_failed_updates)
app.router.add_route('GET', '/a/queue/%s' % secret_key, list_updates)
app.router.add_route('POST', '/a/fix_failed_update/%s' % secret_key, fix_failed_update)

app.loop.run_until_complete(bot.api.setWebhook(settings.TELEGRAM['webhook_url']))

app.bot = bot
