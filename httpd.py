import os
from wsgiref.simple_server import make_server
from evernotebot.app import EvernoteBotApplication


host = '127.0.0.1'
port = 8080
env_vars = (
    'TELEGRAM_API_TOKEN',
    'EVERNOTE_BASIC_ACCESS_KEY',
    'EVERNOTE_BASIC_ACCESS_SECRET',
    'EVERNOTE_FULL_ACCESS_KEY',
    'EVERNOTE_FULL_ACCESS_SECRET',
)
app = EvernoteBotApplication()
for name in env_vars:
    os.environ[name] = 'debug'
try:
    with make_server(host, port, app) as httpd:
        print(f'Starting `evernotebot` at http://{host}:{port}...')
        httpd.serve_forever()
except KeyboardInterrupt:
    app.shutdown()
