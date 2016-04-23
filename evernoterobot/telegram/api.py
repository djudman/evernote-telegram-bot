import logging
import asyncio
import aiohttp


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
            self.logger.debug("API request %(http_method)s %(url)s?%(qs)s" % {
                    'http_method': 'GET',
                    'url': url,
                    'qs': '',
                })
            async with session.get(url, params=kwargs) as response:
                data = await response.json()
                self.logger.debug("API response: %s" % str(data))
        return data

    def sync_call(self, future):
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(future)
        return result

    async def setWebhook(self, url):
        return await self.__request('setWebhook', url=url)
