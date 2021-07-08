import os
from wsgiref.simple_server import make_server
from evernotebot.app import EvernoteBotApplication


host = '127.0.0.1'
port = 8080
envs = (
    'TELEGRAM_API_TOKEN',
    'EVERNOTE_BASIC_ACCESS_KEY',
    'EVERNOTE_BASIC_ACCESS_SECRET',
    'EVERNOTE_FULL_ACCESS_KEY',
    'EVERNOTE_FULL_ACCESS_SECRET',
)


def run():
    for name in envs:
        os.environ[name] = 'debug'
    app = EvernoteBotApplication()
    try:
        with make_server(host, port, app) as httpd:
            print(f'Starting `evernotebot` at http://{host}:{port}...')
            httpd.serve_forever()
    except KeyboardInterrupt:
        app.shutdown()


run()
