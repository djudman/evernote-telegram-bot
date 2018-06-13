from datetime import datetime
from router import UrlRouter
from config import SETTINGS


class Request:
    def __init__(self, wsgi_environ):
        self.init_time = datetime.now()
        self.body = wsgi_environ.get('wsgi.input')
        self.method = wsgi_environ['REQUEST_METHOD']
        self.query_string = wsgi_environ['QUERY_STRING']
        self.raw_uri = wsgi_environ['RAW_URI']
        self.server_protocol = wsgi_environ['SERVER_PROTOCOL']
        self.user_agent = wsgi_environ['HTTP_USER_AGENT']
        self.path = wsgi_environ['PATH_INFO']

    def read():
        if not self.body:
            return
        return self.body.read()


class Response:

    statuses = {
        200: 'OK',
        500: 'Inernal server error',
    }

    def __init__(self, body, status_code=200, headers=None):
        self.body = body if body else b''
        if headers is None:
            self.headers = [
                ('Content-Type', 'text/plain'),
                ('Content-Length', str(len(self.body))),
            ]
        status_message = self.statuses.get(status_code, 'UNKNOWN')
        self.status = '{0} {1}'.format(status_code, status_message)


def handle_request(wsgi_environ):
    request = Request(wsgi_environ)
    project_root = SETTINGS['project_root']
    url_router = UrlRouter(project_root)
    handler = url_router.get_handler(request.path)
    response_data = handler(request)
    response = Response(body=response_data)
    return response.status, response.headers, response.body


def make_request(url, method='GET', params=None):
    pass
