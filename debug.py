import os

from evernotebot.app import EvernoteBotApplication


# This file uses for debug only


def set_var(name, value):
    os.environ[name] = value


if __name__ == '__main__':
    map(set_var, (
        # We have to define some required env vars
        ('TELEGRAM_API_TOKEN', 'debug'),
        ('EVERNOTE_READONLY_KEY', 'debug'),
        ('EVERNOTE_READONLY_SECRET', 'debug'),
        ('EVERNOTE_READWRITE_KEY', 'debug'),
        ('EVERNOTE_READWRITE_SECRET', 'debug'),
    ))

    host = '127.0.0.1'
    port = 8000
    app = EvernoteBotApplication(host, port)
    try:
        print(f'Starting `{app.bot.name}` at http://{host}:{port}...')
        app.run()
    except KeyboardInterrupt:
        app.shutdown()
