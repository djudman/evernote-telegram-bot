import json
import hashlib
import logging
import random
from datetime import datetime
from time import time
from util.http import make_request


class BotApiError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class BotApi:
    def __init__(self, token):
        self.api_url = 'https://api.telegram.org/'
        self.token = token
        self.logger = logging.getLogger('telegram_bot_api')

    def __request(self, api_method, **kwargs):
        url = '{base_url}bot{token}/{api_method}'.format(
            base_url=self.api_url,
            token=self.token,
            api_method=api_method
        )
        request_params = {}
        for k, v in kwargs.items():
            if v is None:
                continue
            request_params.update({k: v})
        h = hashlib.md5()
        h.update('{0}_{1}_{2}'.format(time(), url, random.random()).encode())
        request_id = h.hexdigest()
        self.logger.debug('{dt} - REQUEST {hash} - {method} {url}, params: {params}'.format(
            hash=request_id,
            dt=datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f'),
            method='POST',
            url=url,
            params=str(request_params)
        ))
        raw_response = make_request(url, method='POST', params=request_params)
        self.logger.debug('{dt} - RESPONSE {hash} - {response}'.format(
            hash=request_id,
            dt=datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f'),
            response=raw_response
        ))
        response = json.loads(raw_response.decode())
        if not response['ok']:
            raise BotApiError(response['error_code'], response['description'])
        return response['result']

    def setWebhook(self, url):
        return self.__request('setWebhook', url=url)

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
        file = self.__request('getFile', file_id=file_id)
        download_url = '{base_url}file/bot{token}/{path}'.format(
            base_url=self.api_url,
            token=self.token,
            path=file['file_path']
        )
        return download_url
