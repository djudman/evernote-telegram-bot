import importlib
import importlib.util
import json
import logging
import os
import re
import traceback
from os.path import exists, join

from .http import Request, Response


class UrlRouter:
    def __init__(self, src_root, config=None):
        if config is None:
            config = {}
        if not isinstance(config, dict):
            raise Exception('Invalid config. Non-empty dict is expected.')
        self.config = config
        url_files = []
        if not exists(src_root):
            raise Exception(f'Invalid source root: `{src_root}`')
        for dirpath, _, files in os.walk(src_root):
            paths = [join(dirpath, filename) for filename in files if filename == 'urls.py']
            url_files.extend(paths)
        url_files.sort()
        self.handlers = []
        for filename in url_files:
            urls = self.import_urls(filename)
            for method, regex, handler in urls:
                handler_info = (method, re.compile(regex), handler)
                self.handlers.append(handler_info)

    def import_urls(self, filename):
        spec = importlib.util.spec_from_file_location('urls', filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if callable(module.urls):
            return module.urls(self.config)
        return module.urls

    def get_handler(self, url_path, http_method):
        for method, regex_object, handler in self.handlers:
            if method == http_method and regex_object.search(url_path):
                return handler

    def add_route(self, path, callable_handler, *, method='GET'):
        self.handlers.append((method, re.compile(path), callable_handler))


class WsgiApplication:
    def __init__(self, src_root, *, urls=None, config=None):
        if config is None:
            config = {}
        self.config = config
        self.router = UrlRouter(src_root, config)
        self.logger = logging.getLogger('wsgi')
        if urls:
            for method, path, handler in urls:
                self.router.add_route(path, handler, method=method)

    def wsgi_request(self, wsgi_environ):
        request = None
        response = None
        exc = None
        try:
            request = Request(wsgi_environ)
            request.read()
            handler = self.router.get_handler(request.path, request.method)
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
            response = Response(body=b'Internal server error', status_code=500)
        finally:
            self.__log_request(request, response, exc)
        return response.status, response.headers, response.body

    def __log_request(self, request: Request, response: Response, str_exc: str):
        if hasattr(request, "no_log") and request.no_log and not str_exc:
            return
        message = {
            'request': request.__to_dict__(),
            'response': response.__to_dict__(),
        }
        if str_exc:
            message['exception'] = str_exc
            level = 'fatal'
        else:
            first_digit = response.status_code // 100
            error_level_map = {5: 'error', 4: 'warning'}
            level = error_level_map.get(first_digit, 'info')
        getattr(self.logger, level)(message)

    def __call__(self, environ, start_response):
        status, response_headers, response_body = self.wsgi_request(environ)
        start_response(status, response_headers)
        return [response_body]
