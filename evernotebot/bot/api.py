import hashlib
import json
import logging
import random
import ssl
from http.client import HTTPSConnection, HTTPConnection
from json import JSONDecodeError
from time import time
from urllib.parse import urlparse, urlencode


logger = logging.getLogger('telegram.api')


class BotApiError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self):
        return f'{self.code} {self.message}'


def log_http_request(method):
    def wrapper(obj, url, params):
        h = hashlib.sha256()
        h.update('{0}_{1}_{2}'.format(time(), url, random.random()).encode())
        request_id = h.hexdigest()
        logger.debug({
            'ts': time(),
            'type': 'request',
            'request': {'id': request_id, 'url': url, 'params': params},
        })
        raw_response = method(obj, url, params)
        logger.debug({
            'ts': time(),
            'type': 'response',
            'request': {'id': request_id},
            'response': raw_response.decode(),
        })
        return raw_response

    return wrapper


class BotApi:
    def __init__(self, token, api_url):
        self.token = token
        self.api_url = api_url.rstrip('/')

    @log_http_request
    def __http_post_request(self, url: str, params: dict) -> bytes:
        parse_result = urlparse(url)
        hostname = parse_result.netloc
        if url.startswith('https'):
            context = ssl.SSLContext()
            conn = HTTPSConnection(hostname, None, context=context)
        else:
            conn = HTTPConnection(hostname, None)
        body = urlencode(params)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': len(body),
        }
        request_url = f'{parse_result.path}?{parse_result.query}'
        conn.connect()
        try:
            conn.request('POST', request_url, body, headers)
            response = conn.getresponse()
            data = response.read()
        finally:
            conn.close()
        return data

    def __api_request(self, api_method: str, **kwargs) -> dict:
        url = f'{self.api_url}/bot{self.token}/{api_method}'
        request_params = {k: v for k, v in kwargs.items() if v is not None}
        raw_response = self.__http_post_request(url, request_params)
        try:
            response = json.loads(raw_response.decode())
        except JSONDecodeError:
            response = {
                'ok': False,
                'error_code': -1,
                'description': raw_response.decode(),
            }
        if not response['ok']:
            raise BotApiError(response['error_code'], response['description'])
        return response['result']

    def setWebhook(self, url, certificate=None, max_connections=40, allowed_updates=None):
        if allowed_updates is None:
            allowed_updates = []
        return self.__api_request(
            'setWebhook',
            url=url,
            certificate=certificate,
            max_connections=max_connections,
            allowed_updates=allowed_updates
        )

    def sendMessage(self, chat_id, text, reply_markup=None, parse_mode=None) -> dict:
        return self.__api_request(
            'sendMessage',
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    def editMessageReplyMarkup(self, chat_id, message_id, reply_markup):
        return self.__api_request(
            'editMessageReplyMarkup',
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup
        )

    def editMessageText(self, chat_id, message_id, text, reply_markup=None):
        return self.__api_request(
            'editMessageText',
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup
        )

    def getFile(self, file_id):
        response = self.__api_request('getFile', file_id=file_id)
        path = response['file_path']
        return f'{self.api_url}/file/bot{self.token}/{path}'
