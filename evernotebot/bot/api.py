import hashlib
import json
import logging
import random
from json import JSONDecodeError
from time import time
from typing import Optional

import aiohttp


logger = logging.getLogger('telegram.api')


class BotApiError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self):
        return f'{self.code} {self.message}'


def log_http_request(method):
    async def wrapper(obj, url: str, params: dict):
        h = hashlib.sha256()
        h.update('{0}_{1}_{2}'.format(time(), url, random.random()).encode())  # nosec
        request_id = h.hexdigest()
        logger.debug({
            'ts': time(),
            'type': 'request',
            'request': {'id': request_id, 'url': url, 'params': params},
        })
        raw_response = await method(obj, url, params)
        logger.debug({
            'ts': time(),
            'type': 'response',
            'request': {'id': request_id},
            'response': raw_response.decode(),
        })
        return raw_response

    return wrapper


class BotApi:
    def __init__(self, token: str, api_url: str):
        self.token = token
        self.api_url = api_url.rstrip('/')

    @log_http_request
    async def __http_post_request(self, url: str, params: dict) -> bytes:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.post(url, json=params) as response:
                data = await response.read()
        return data

    async def __api_request(self, api_method: str, **kwargs) -> dict:
        url = f'{self.api_url}/bot{self.token}/{api_method}'
        request_params = {k: v for k, v in kwargs.items() if v is not None}
        raw_response = await self.__http_post_request(url, request_params)
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

    async def setWebhook(self, url: str, certificate=None, max_connections=40, allowed_updates=None):
        if allowed_updates is None:
            allowed_updates = []
        return await self.__api_request(
            'setWebhook',
            url=url,
            certificate=certificate,
            max_connections=max_connections,
            allowed_updates=allowed_updates
        )

    async def sendMessage(self, chat_id: int, text: str, reply_markup: Optional[str] = None, parse_mode=None) -> dict:
        return await self.__api_request(
            'sendMessage',
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    async def editMessageReplyMarkup(self, chat_id: int, message_id, reply_markup):
        return await self.__api_request(
            'editMessageReplyMarkup',
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup
        )

    async def editMessageText(self, chat_id: int, message_id, text, reply_markup=None):
        return await self.__api_request(
            'editMessageText',
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup
        )

    async def getFile(self, file_id: str):
        response = await self.__api_request('getFile', file_id=file_id)
        path = response['file_path']
        return f'{self.api_url}/file/bot{self.token}/{path}'
