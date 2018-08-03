from api.handlers import telegram_hook
from api.handlers import evernote_oauth
from api.handlers import error
from api.handlers import welcome


def urls(config):
    telegram_token = config['telegram']['token']
    return (
        ('POST', r'^/{0}'.format(telegram_token), telegram_hook),
        ('GET', r'^/evernote/access/basic/$', evernote_oauth),
        ('GET', r'^/evernote/access/full/$', evernote_oauth),
        ('GET', r'^/error', error),
        ('GET', r'^/?$', welcome),
    )
