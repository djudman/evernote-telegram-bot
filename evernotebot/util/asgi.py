import json
import logging
import re
import traceback
from functools import partial
from time import time
from typing import Coroutine
from urllib.parse import parse_qsl


class Jsonable:
    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return json.dumps(self.__to_dict__())


class Response(Jsonable):
    def __init__(self, send, status: int = None, headers: list[tuple[str, bytes]] = None, body: bytes = None):
        self.create_time = time()
        self._send = send
        self.status = status
        self.headers = headers
        self.body = body
        self.error = None

    async def send(self, status: int = None, headers: list[tuple[str, bytes]] = None, body: bytes = None):
        status = status or self.status
        body = body or self.body or b''
        headers = self.validate_headers(headers, body)
        await self._send({
            'type': 'http.response.start',
            'status': status,
            'headers': headers,
        })
        await self._send({
            'type': 'http.response.body',
            'body': body,
        })

    def validate_headers(self, headers: list[tuple[str, bytes]], body: bytes):
        headers = headers or []
        content_length = None
        content_type = None
        for name, value in headers:
            name = name.lower().strip().encode()
            if name == b'content-type':
                content_type = value
            elif name == b'content-length':
                content_length = value
        if not content_length:
            headers.append((b'content-length', str(len(body)).encode()))
        if not content_type:
            headers.append((b'content-type', b'text/plain'))
        return headers

    def __to_dict__(self):
        body = self.body and self.body.decode() or None
        return {
            'create_time': self.create_time,
            'body': body,
            'status': self.status,
            'error': self.error,
        }


class Request(Jsonable):
    def __init__(self, scope, receive, send):
        self._scope = scope
        self._receive = receive
        self._send = send
        self.create_time = time()
        self.body = None
        self.path = scope.get('path', '/')
        self.query_string = scope.get('query_string').decode()
        self.method = scope.get('method', 'GET')
        if self.query_string:
            qs_params = parse_qsl(self.query_string)
            self.GET = {name: value for name, value in qs_params}
        else:
            self.GET = {}

    def make_response(self, status: int, body: bytes) -> Response:
        response = Response(self._send)
        response.status = status
        response.body = body
        return response

    async def read(self) -> bytes:
        data = {'more_body': True}
        buffer = b''
        while data.get('more_body'):
            data = await self._receive()
            if data.get('type') == 'http.request':
                buffer += data.get('body', b'')
        self.body = buffer
        return buffer

    async def json(self) -> dict:
        if self.body is None:
            await self.read()
        data = self.body or None
        if not data:
            return {}
        return json.loads(data)

    def __to_dict__(self):
        body = self.body and self.body.decode() or None
        return {
            'create_time': self.create_time,
            'body': body,
        }


class AsgiApplication:
    def __init__(self, url_schema):
        self.handlers = []
        self.logger = logging.getLogger('wsgi')
        for method, path, handler in url_schema:
            self.handlers.append((method, re.compile(path), handler))

    def get_handler(self, url_path, http_method):
        for method, regex_object, handler in self.handlers:
            if method.lower() == http_method.lower() and (matched := regex_object.match(url_path)):
                groups = matched.groups()
                return partial(handler, *groups)

    async def http_request(self, request: Request, send: Coroutine) -> Response:
        exc = None
        response = Response(send, status=500)
        try:
            handler = self.get_handler(request.path, request.method)
            if not handler:
                response = Response(send, status=404, body=b'Not found')
                return response
            request.app = self
            response_data = await handler(request)
            if isinstance(response_data, Response):
                response = response_data
                return response_data
            if isinstance(response_data, dict):
                response_data = json.dumps(response_data)
            if isinstance(response_data, str):
                response_data = response_data.encode()
            if not isinstance(response_data, bytes):
                type_name = str(type(response_data))
                raise Exception(f'Invalid response type `{type_name}`')
            response.status = 200
            response.headers = [
                ('content-type', b'text/plain'),
                ('content-length', len(response_data)),
            ]
            response.body = response_data
        except Exception:
            response.status = 500
            response.body = b'Internal wsgi app error'
            response.error = traceback.format_exc()
        finally:
            self.__log_request(request, response, exc)
        return response

    async def __call__(self, scope: dict, receive: Coroutine, send: Coroutine):
        request = Request(scope, receive, send)
        await request.read()
        response = await self.http_request(request, send)
        await response.send()

    def __log_request(self, request: Request, response: Response, error: str):
        log_entry = {
            'request': request.__to_dict__(),
            'response': response.__to_dict__(),
        }
        if error:
            log_entry['exception'] = error
            level = 'fatal'
        else:
            first_digit = response.status // 100
            error_level_map = {5: 'error', 4: 'warning'}
            level = error_level_map.get(first_digit, 'info')
        text = json.dumps(log_entry, indent=4)
        log_method = getattr(self.logger, level)
        log_method(text)
