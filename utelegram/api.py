import hashlib
import json
import logging
import random
import ssl
from http.client import HTTPSConnection
from time import time
from urllib.parse import urlparse, urlencode


class BotApiError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class BotApi:
    def __init__(self, token):
        self.api_url = 'https://api.telegram.org/'
        self.token = token
        self.logger = logging.getLogger('utelegram.api')

    def __make_request(self, url, params):
        parse_result = urlparse(url)
        hostname = parse_result.netloc
        context = ssl.SSLContext()
        conn = HTTPSConnection(hostname, None, context=context)
        conn.connect()
        body = urlencode(params)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': len(body),
        }
        request_url = f"{parse_result.path}?{parse_result.query}"
        try:
            conn.request("POST", request_url, body, headers)
            response = conn.getresponse()
            data = response.read()
        finally:
            conn.close()
        return data

    def __request(self, api_method, **kwargs):
        url = '{base_url}bot{token}/{api_method}'.format(
            base_url=self.api_url,
            token=self.token,
            api_method=api_method
        )
        request_params = {k:v for k, v in kwargs.items() if v is not None}
        h = hashlib.sha256()
        h.update('{0}_{1}_{2}'.format(time(), url, random.random()).encode())
        request_id = h.hexdigest()
        self.logger.debug({
            "ts": time(),
            "type": "request", 
            "request": {"id": request_id, "url": url, "params": request_params},
        })
        raw_response = self.__make_request(url, request_params)
        self.logger.debug({
            "ts": time(),
            "type": "response",
            "request": {"id": request_id},
            "response": raw_response.decode(),
        })
        response = json.loads(raw_response.decode())
        if not response['ok']:
            raise BotApiError(response['error_code'], response['description'])
        return response['result']

    def setWebhook(self, url, certificate=None, max_connections=40, allowed_updates=None):
        if allowed_updates is None:
            allowed_updates = []
        return self.__request(
            'setWebhook',
            url=url,
            certificate=certificate,
            max_connections=max_connections,
            allowed_updates=allowed_updates
        )

    def sendMessage(self, chat_id, text, reply_markup=None, parse_mode=None):
        return self.__request(
            'sendMessage',
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    def editMessageReplyMarkup(self, chat_id, message_id, reply_markup):
        return self.__request(
            'editMessageReplyMarkup',
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup
        )

    def editMessageText(self, chat_id, message_id, text, reply_markup=None):
        return self.__request(
            'editMessageText',
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup
        )

    def getFile(self, file_id):
        response = self.__request('getFile', file_id=file_id)
        path = response['file_path']
        return f'{self.api_url}file/bot{self.token}/{path}'
