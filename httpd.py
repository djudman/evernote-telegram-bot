from wsgiref.simple_server import make_server
from evernotebot.wsgi import app


host = '127.0.0.1'
port = 8080
print(f'Starting `evernotebot` at http://{host}:{port}...')
try:
    with make_server(host, port, app) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    app.shutdown()
