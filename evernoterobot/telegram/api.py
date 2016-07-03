import logging
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
        args_data = {}
        for k, v in kwargs.items():
            if v is not None:
                args_data.update({k: v})
        with aiohttp.ClientSession() as session:
            self.logger.debug(
                "API request %(http_method)s %(url)s, data: %(data)s" % {
                    'http_method': 'POST',
                    'url': url,
                    'data': str(args_data),
                })
            async with session.post(url, data=args_data) as response:
                data = await response.json()
                self.logger.debug("API response: %s" % str(data))

        if not data['ok']:
            raise BotApiError(data['error_code'], data['description'])
        return data['result']

    async def setWebhook(self, url):
        return await self.__request('setWebhook', url=url)

    async def sendMessage(self, chat_id, text, reply_markup=None):
        return await self.__request('sendMessage', chat_id=chat_id, text=text,
                                    reply_markup=reply_markup)

    async def editMessageReplyMarkup(self, chat_id, message_id, reply_markup):
        return await self.__request('editMessageReplyMarkup', chat_id=chat_id,
                                    message_id=message_id,
                                    reply_markup=reply_markup)

    async def editMessageText(self, chat_id, message_id, text, reply_markup=None):
        return await self.__request('editMessageText', chat_id=chat_id,
                                    message_id=message_id, text=text,
                                    reply_markup=reply_markup)

    async def getFile(self, file_id):
        file = await self.__request('getFile', file_id=file_id)
        download_url = 'https://api.telegram.org/file/bot%(token)s/%(path)s' %\
            {
                'token': self.token,
                'path': file['file_path'],
            }
        return download_url

    async def downloadFile(self, file_id):
        url = await self.getFile(file_id)
        url_parts = url.split('/')
        short_name = url_parts[-1]
        filename = '/tmp/%s_%s' % (file_id, short_name)
        with open(filename, 'wb') as f:
            with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    content = await resp.content.read()
            f.write(content)
        return filename
