import json
import logging.config
from os import makedirs
from os.path import dirname
from os.path import join
from os.path import realpath


DEBUG = True
PROJECT_ROOT = lambda x: join(dirname(realpath(__file__)), x)
SETTINGS = {
    'project_root': PROJECT_ROOT(''), # FIXME: too many calls
    'tmp_root': PROJECT_ROOT('../tmp'),
    'logs_root': PROJECT_ROOT('../logs'),
}

with open('config.json', 'r') as f:
    local_config = json.load(f)

HOST = local_config['host']
EVERNOTE = local_config['evernote']
TELEGRAM = local_config['telegram']

makedirs(SETTINGS['logs_root'], exist_ok=True)
makedirs(SETTINGS['tmp_root'], exist_ok=True)

log_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - PID:%(process)d - %(levelname)s - %(message)s (%(pathname)s:%(lineno)d)',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': join(SETTINGS['logs_root'], 'evernoterobot.log')
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
logging.config.dictConfig(log_config)
