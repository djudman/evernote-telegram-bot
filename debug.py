import os

import uvicorn


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
    try:
        print(f'Starting `evernotebot` at http://{host}:{port}...')
        config = uvicorn.Config('evernotebot.wsgi:app', host=host, port=port, log_level='debug')
        server = uvicorn.Server(config)
        server.run()
    except KeyboardInterrupt:
        pass
        # TODO:
        # app.shutdown()
