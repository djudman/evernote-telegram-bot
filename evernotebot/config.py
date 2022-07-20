import os

from evernotebot.util.logs import init_logging


def load_config():
    bot_name = os.getenv('BOT_NAME', 'evernotebot')
    host = os.getenv('HOST', '127.0.0.1:8081')
    bot_api_token = os.getenv('BOT_API_TOKEN', 'bot_api_token')
    is_debug = os.getenv('DEBUG', True)
    default_oauth_url = is_debug and f'http://{host}/evernote/oauth' or f'https://{host}/evernote/oauth'
    default_bot_api_url = is_debug and 'http://127.0.0.1:11000/' or 'https://api.telegram.org/'
    default_webhook_url = is_debug and f'http://{host}/{bot_api_token}' or f'https://{host}/{bot_api_token}'
    config = {
        'debug': is_debug,
        'default_mode': 'multiple_notes',
        'host': host,
        'oauth_callback_url': os.getenv('OAUTH_CALLBACK_URL', default_oauth_url),
        'webhook_url': os.getenv('WEBHOOK_URL', default_webhook_url),
        'tmp_root': os.getenv('TMP_ROOT', '/tmp/'),
        'telegram': {
            'bot_name': bot_name,
            'token': bot_api_token,
            'api_url': os.getenv('BOT_API_URL', default_bot_api_url)
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
            'db_name': os.getenv('DBNAME', bot_name),
            'dirpath': os.getenv('DATA_DIR', f'/tmp/{bot_name}-data/')
        },
    }
    init_logging(debug=is_debug)
    return config
