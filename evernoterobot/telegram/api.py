import aiohttp


class BotApi:

    def __init__(self, token):
        self.token = token

    async def __request(self, method_name, **kwargs):
        url = "https://api.telegram.org/bot%(token)s/%(method_name)s" % {
            'token': self.token,
            'method_name': method_name,
        }
        # TODO: only 'GET' http method uses now. May be add support of 'POST'?
        with aiohttp.ClientSession() as session:
            async with session.get(url, params=kwargs) as response:
                data = await response.json()
        return data

    async def setWebhook(self, url):
        return await self.__request('setWebhook', url=url)
