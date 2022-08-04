import json
import logging
import re
import traceback
from functools import partial

from gunicorn.app.base import BaseApplication

from .http import Request, Response


class WsgiApplication(BaseApplication):
    def __init__(self, url_schema, bind='127.0.0.1:11000', num_workers=5):
        self.bind = bind
        self.num_workers = num_workers
        self.application = self.handler_app
        super().__init__()
        self.handlers = []
        self.logger = logging.getLogger('wsgi')
        for method, path, handler in url_schema:
            self.handlers.append((method, re.compile(path), handler))

    def load(self):
        return self.application

    def load_config(self):
        self.cfg.set('bind', self.bind)
        self.cfg.set('workers', self.num_workers)

    def get_handler(self, url_path, http_method):
        for method, regex_object, handler in self.handlers:
            if method.lower() == http_method.lower() and (matched := regex_object.match(url_path)):
                groups = matched.groups()
                return partial(handler, *groups)

    def wsgi_request(self, wsgi_environ):
        request = None
        response = None
        exc = None
        try:
            request = Request(wsgi_environ)
            request.read()
            handler = self.get_handler(request.path, request.method)
            if handler:
                request.app = self
                response = handler(request)
                if isinstance(response, dict):
                    response = Response(body=json.dumps(response))
                elif isinstance(response, str) or isinstance(response, bytes):
                    response = Response(body=response)
                if not isinstance(response, Response):
                    raise Exception(f'Invalid response type `{str(type(response))}`. Expected types: `str` / `bytes` / `dict` / `Response`')
            else:
                response = Response(body=b'Not found', status_code=404)
        except Exception:
            exc = traceback.format_exc()
            response = Response(body=b'Internal wsgi app error', status_code=500)
        finally:
            self.__log_request(request, response, exc)
        return response.status, response.headers, response.body

    def __log_request(self, request: Request, response: Response, str_exc: str):
        if hasattr(request, "no_log") and request.no_log and not str_exc:
            return
        if not response:
            response = Response(body=b'Internal wsgi app error', status_code=500)
        message = {
            'request': request.__to_dict__(),
            'response': response.__to_dict__() or {},
        }
        if str_exc:
            message['exception'] = str_exc
            level = 'fatal'
        else:
            first_digit = response.status_code // 100
            error_level_map = {5: 'error', 4: 'warning'}
            level = error_level_map.get(first_digit, 'info')
        getattr(self.logger, level)(json.dumps(message, indent=4))

    def handler_app(self, environ, start_response):
        status, response_headers, response_body = self.wsgi_request(environ)
        start_response(status, response_headers)
        return [response_body]

    def __call__(self, *args, **kwargs):
        return self.handler_app(*args, **kwargs)
