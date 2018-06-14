from config import TELEGRAM
from api.handlers import telegram_hook
from api.handlers import evernote_oauth
from api.handlers import error

telegram_token = TELEGRAM['token']
assert telegram_token

urls = (
    ('POST', r'^/{0}/'.format(telegram_token), telegram_hook),
    ('GET', r'^/evernote/access/basic/$', evernote_oauth),
    ('GET', r'^/evernote/access/full/$', evernote_oauth),
    ('GET', r'^/error', error),
)
