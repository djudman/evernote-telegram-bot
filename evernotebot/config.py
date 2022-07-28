import os
from pathlib import Path

from evernotebot.util.logs import init_logging


def root_dir(path: str = '') -> str:
    return str(Path(__file__).parent.parent.joinpath(path).resolve())


def make_dirs(config):
    dirs = (
        config['logs_root'],
        config['tmp_root'],
        config['storage']['dirpath'],
    )
    for path in dirs:
        os.makedirs(path, exist_ok=True)


def load_config():
    bot_name = os.getenv('TELEGRAM_BOT_NAME') or 'evernoterobot'
    host = os.getenv('EVERNOTEBOT_HOSTNAME') or '127.0.0.1'
    port = os.getenv('EVERNOTEBOT_EXPOSE_PORT') or 8000
    bot_api_token = os.getenv('TELEGRAM_API_TOKEN') or 'bot_api_token'
    is_debug = int(os.getenv('EVERNOTEBOT_DEBUG') or 0)
    oauth_url = (host == '127.0.0.1') and f'{host}:{port}/evernote/oauth' or f'{host}/evernote/oauth'
    default_oauth_url = is_debug and f'http://{oauth_url}' or f'https://{oauth_url}'
    default_bot_api_url = is_debug and 'http://127.0.0.1:11000/' or 'https://api.telegram.org/'
    webhook_url = (host == '127.0.0.1') and f'{host}:{port}/{bot_api_token}' or f'{host}/{bot_api_token}'
    default_webhook_url = is_debug and f'http://{webhook_url}' or f'https://{webhook_url}'
    config = {
        'debug': is_debug,
        'default_mode': 'multiple_notes',
        'host': host,
        'port': port,
        'oauth_callback_url': os.getenv('OAUTH_CALLBACK_URL') or default_oauth_url,
        'webhook_url': os.getenv('WEBHOOK_URL') or default_webhook_url,
        'logs_root': root_dir('logs/'),
        'tmp_root': os.getenv('TMP_ROOT') or root_dir('tmp/'),
        'telegram': {
            'bot_name': bot_name,
            'token': bot_api_token,
            'api_url': os.getenv('BOT_API_URL') or default_bot_api_url
        },
        'evernote': {
            'access': {
                'readonly': {
                    'key': os.getenv('EVERNOTE_READONLY_KEY'),
                    'secret': os.getenv('EVERNOTE_READONLY_SECRET'),
                },
                'readwrite': {
                    'key': os.getenv('EVERNOTE_READWRITE_KEY'),
                    'secret': os.getenv('EVERNOTE_READWRITE_SECRET'),
                },
            },
        },
        'storage': {
            'provider': 'evernotebot.storage.providers.sqlite.Sqlite',
            'db_name': bot_name,
            'dirpath': root_dir('db/'),
        },
    }
    make_dirs(config)
    init_logging(config['logs_root'], debug=is_debug)
    return config
