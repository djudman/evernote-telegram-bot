import json
import logging.config
from logging import Formatter
from os.path import join


class JsonFormatter(Formatter):
    def format(self, record):
        return json.dumps({
            'logger': record.name,
            'file': '{0}:{1}'.format(record.pathname, record.lineno),
            'data': record.msg,
        })


def init_logging(logs_dir: str, debug=False):
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s [PID:%(process)d][%(name)s] - %(levelname)s - %(message)s (%(pathname)s:%(lineno)s)',
            },
            'json': {
                'class': 'evernotebot.util.logs.JsonFormatter',
            }
        },
        'handlers': {
            # 'stdout': {
            #     'class': 'logging.StreamHandler',
            #     'formatter': 'default',
            # },
            'evernotebot': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': join(logs_dir, 'evernotebot.log'),
                'mode': 'a',
                'maxBytes': 10485760,
                'backupCount': 1,
                'formatter': 'default',
            },
        },
        'loggers': {
            'wsgi': {
                'level': 'DEBUG',
                'propagate': False,
                'handlers': ['evernotebot'],
            },
            'evernotebot': {
                'level': 'DEBUG',
                'propagate': False,
                'handlers': ['evernotebot'],
            },
        },
    }
    logging.config.dictConfig(config)
