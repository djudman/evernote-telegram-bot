import json
import ssl
from http.client import HTTPConnection, HTTPSConnection
from time import time
from urllib.parse import parse_qsl, urlencode, urlparse


class Request:
    def __init__(self, wsgi_environ):
        self.create_time = time()
        self.body = None
        self._wsgi_environ = wsgi_environ

        content_length = wsgi_environ.get('CONTENT_LENGTH', 0)  # value of this variable depends on web server. Sometimes it may be '' (an empty string).
        self.content_length = int(content_length) if content_length else 0
        self.user_agent = wsgi_environ.get('HTTP_USER_AGENT')
        self.path = wsgi_environ.get('PATH_INFO', '/')
        self.query_string = wsgi_environ.get('QUERY_STRING')
        self.raw_uri = wsgi_environ.get('RAW_URI')
        self.method = wsgi_environ.get('REQUEST_METHOD', 'GET')
        self.server_protocol = wsgi_environ.get('SERVER_PROTOCOL')
        self.input = wsgi_environ.get('wsgi.input')
        self.http_variables = {name.upper(): value for name, value in wsgi_environ.items() if name.startswith("HTTP_")}
        if self.query_string:
            qs_params = parse_qsl(self.query_string)
            self.GET = {name: value for name, value in qs_params}
        else:
            self.GET = {}

    def read(self):
        if not self.body and self.input and self.content_length > 0:
            self.body = self.input.read(self.content_length)  # TODO: Whether can input be closed?
        return self.body

    def json(self):
        if not self.body:
            self.read()
        if not self.body:
            return
        data = self.body.decode()
        return json.loads(data)

    def __to_dict__(self):
        body = (self.body and self.body.decode()) or self.read()  # TODO: to check `Content-Type` header. If it is `application/octet-stream`, then to convert data to base64.
        data = {
            'create_time': self.create_time,
            'body': body,
        }
        for name, value in self._wsgi_environ.items():
            if isinstance(value, str) or isinstance(value, int):
                data[name] = value
        return data

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return json.dumps(self.__to_dict__())


class Response:
    statuses = {
        200: 'OK',
        301: 'Moved Permanently',
        302: 'Found',
        404: 'Not Found',
        500: 'Internal Server Error',
    }

    def __init__(self, body, status_code=200, headers=None):
        self.create_time = time()
        self.body = body if body else b''
        if isinstance(self.body, str):
            self.body = self.body.encode()
        elif isinstance(self.body, bytes):
            pass
        else:
            raise Exception('Parameter `body` must have `str` or `bytes` type.')
        headers = headers if headers is not None else []
        _headers = {name.lower(): value for name, value in headers}
        if 'content-type' not in _headers:
            _headers['content-type'] = 'text/plain'
        _headers['content-length'] = str(len(self.body))
        self.headers = [(name, value) for name, value in _headers.items()]
        status_message = self.statuses.get(status_code, 'Unknown')
        self.status_code = status_code
        self.status = f'{status_code} {status_message}'

    def __to_dict__(self):
        body = self.body.decode()  # TODO: to check `Content-Type` header. If it is `application/octet-stream`, then to convert data to base64.
        data = {
            'create_time': self.create_time,
            'body': body,
            'headers': self.headers,
            'status': self.status,
        }
        return data

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return json.dumps(self.__to_dict__())


class HTTPFound(Response):
    def __init__(self, redirect_url):
        headers = [('Location', redirect_url)]
        super().__init__(b'', 302, headers)


def make_request(url, method='GET', params=None, body=None, headers=None):
    parse_result = urlparse(url)
    protocol = parse_result.scheme
    hostname = parse_result.netloc
    port = None
    if ':' in hostname:
        hostname, port = hostname.split(':')
    if protocol == 'https':
        context = ssl.SSLContext()
        conn = HTTPSConnection(hostname, port, context=context)
    elif protocol == 'http':
        conn = HTTPConnection(hostname, port)
    else:
        raise Exception('Unsupported protocol {}'.format(protocol))
    if headers is None:
        headers = {}
    if method == 'POST':
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if params and not body:
            body = urlencode(params)
    request_url = f'{parse_result.path}?{parse_result.query}'
    conn.request(method, request_url, body, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return data
