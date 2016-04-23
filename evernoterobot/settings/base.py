from os.path import dirname, join, realpath
import json


PROJECT_DIR = realpath(dirname(dirname(__file__)))
ROOT_DIR = realpath(dirname(PROJECT_DIR))
PROJECT_NAME = dirname(PROJECT_DIR).lower()
LOGS_DIR = join(realpath(dirname(PROJECT_DIR)), 'logs')

with open(join(PROJECT_DIR, 'settings/secret.json'), 'r') as f:
    SECRET = json.load(f)

SMTP = SECRET['smtp']
WEBHOOK_URL = "https://evernoterobot.djudman.info/%s" % SECRET['token']

LOG_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': '%(asctime)s - PID:%(process)d - %(levelname)s - %(message)s (%(pathname)s:%(lineno)d)',
        },
    },

    'handlers': {
        'accessfile': {
            'class': 'logging.FileHandler',
            'filename': join(LOGS_DIR, 'access.log')
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': join(LOGS_DIR, '%s.log' % PROJECT_NAME),
            'formatter': 'default',
        },
        'email': {
            'level': 'ERROR',
            'class': 'settings.logging.SslSMTPHandler',
            'mailhost': (SMTP['host'], SMTP['port']),
            'fromaddr': SMTP['email'],
            'toaddrs': [SMTP['email']],
            'subject': '',
            'credentials': (SMTP['user'], SMTP['password']),
            'secure': (),
        },
    },

    'loggers': {
        'aiohttp.access': {
            'level': 'INFO',
            'handlers': ['accessfile'],
            'propagate': True,
        },
        'aiohttp.server': {
            'level': 'INFO',
            'handlers': ['file', 'email'],
            'propagate': True,
        },
        'gunicorn.access': {
            'level': 'INFO',
            'handlers': ['accessfile'],
            'propagate': True,
        },
        'gunicorn.error': {
            'level': 'INFO',
            'handlers': ['file', 'email'],
            'propagate': True,
        },
    },
}
