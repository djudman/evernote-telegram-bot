import os
from pathlib import Path

import yaml

from evernotebot.util.logs import init_logging


def load_config():
    filename = Path(__file__).parent.parent.joinpath('config.yaml').absolute()
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    read_env(config)
    init_logging(config['debug'])
    return config


def getenv(name: str, default=None, required=False):
    value = os.getenv(name, default)
    if required and value is None:
        raise Exception(f'Environment variable `{name}` is not set')
    return value


def read_env(config):
    config['debug'] = getenv('EVERNOTEBOT_DEBUG', False)
    config['host'] = getenv('EVERNOTEBOT_HOSTNAME', 'evernotebot.djud.me')
    config['telegram'] = {
        'bot_name': getenv('TELEGRAM_BOT_NAME', 'evernotebot'),
        'token': getenv('TELEGRAM_API_TOKEN', required=True),
    }
    config['evernote'] = {
        'access': {
            'basic': {
                'key': getenv('EVERNOTE_BASIC_ACCESS_KEY', required=True),
                'secret': getenv('EVERNOTE_BASIC_ACCESS_SECRET', required=True),
            },
            'full': {
                'key': getenv('EVERNOTE_FULL_ACCESS_KEY', required=True),
                'secret': getenv('EVERNOTE_FULL_ACCESS_SECRET', required=True),
            },
        },
    }
