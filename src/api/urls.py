from ..config import TELEGRAM
from handlers import telegram_hook
from handlers import evernote_oauth


telegram_token = TELEGRAM['token']
urls = (
    ('POST', '/{0}/'.format(telegram_token), telegram_hook),
    ('GET', '/evernote/access/basic/', evernote_oauth),
    ('GET', '/evernote/access/full/', evernote_oauth),
)
