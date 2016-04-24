import logging
import asyncio
import aiohttp


class BotApiError(Exception):

    def __init__(self, code, description):
        super(BotApiError, self).__init__(description)
        self.code = code


class BotApi:

    def __init__(self, token):
        self.token = token
        self.logger = logging.getLogger()

    async def __request(self, method_name, **kwargs):
        url = "https://api.telegram.org/bot%(token)s/%(method_name)s" % {
            'token': self.token,
            'method_name': method_name,
        }
        # TODO: only 'GET' http method uses now. May be add support of 'POST'?
        with aiohttp.ClientSession() as session:
            self.logger.debug("API request %(http_method)s %(url)s, data: %(data)s" % {
                    'http_method': 'POST',
                    'url': url,
                    'data': str(kwargs),
                })
            async with session.post(url, data=kwargs) as response:
                data = await response.json()
                self.logger.debug("API response: %s" % str(data))

        if not data['ok']:
            raise BotApiError(data['error_code'], data['description'])
        return data

    def sync_call(self, future):
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(future)
        return result

    async def setWebhook(self, url):
        return await self.__request('setWebhook', url=url)

    async def sendMessage(self, chat_id, text, reply_markup=None):
        return await self.__request('sendMessage', chat_id=chat_id, text=text,
                                    reply_markup=reply_markup)

    async def editMessageReplyMarkup(self, chat_id, message_id, reply_markup):
        return await self.__request('editMessageReplyMarkup', chat_id=chat_id,
                                    message_id=message_id,
                                    reply_markup=reply_markup)
