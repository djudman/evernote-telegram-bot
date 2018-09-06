from api.handlers import evernote_oauth
from api.handlers import telegram_hook
from urllib.parse import urlparse 


def urls(config):
    webhook_url = urlparse(config['webhook_url'])
    return (
        ('POST', webhook_url.path, telegram_hook),
        ('GET', r'^/evernote/oauth$', evernote_oauth),
    )
