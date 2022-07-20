import json
import logging.config
import os
from logging import Formatter
from os.path import exists
from pathlib import Path


def logs_root(path=''):
    return Path(__file__).parent.parent.parent.joinpath('logs', path).absolute()


formatters = {
    'default': {
        'class': 'logging.Formatter',
        'format': '%(asctime)s [PID:%(process)d][%(name)s] - %(levelname)s - %(message)s (%(pathname)s:%(lineno)s)',
    },
    'json': {
        'class': 'evernotebot.util.logs.JsonFormatter',
    }
}

handlers = {
    # 'stdout': {
    #     'class': 'logging.StreamHandler',
    #     'formatter': 'default',
    # },
    'evernotebot': {
        'class': 'logging.message_handlers.RotatingFileHandler',
        'filename': logs_root('evernotebot.log'),
        'maxBytes': 10485760,
        'backupCount': 1,
        'formatter': 'default',
    },
}

loggers = {
    'wsgi': {
        'level': 'DEBUG',
        'propagate': True,
        'message_handlers': ['evernotebot'],
    },
    'evernotebot': {
        'level': 'DEBUG',
        'propagate': True,
        'message_handlers': ['evernotebot'],
    },
}

config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': formatters,
    'message_handlers': handlers,
    'loggers': loggers,
}


class JsonFormatter(Formatter):
    def format(self, record):
        return json.dumps({
            'logger': record.name,
            'file': '{0}:{1}'.format(record.pathname, record.lineno),
            'data': record.msg,
        })


def init_logging(debug=False):
    # if debug:
    #     for name, data in loggers.items():
    #         data['message_handlers'].append('stdout')
    logs_dir = logs_root()
    if not exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    logging.config.dictConfig(config)
