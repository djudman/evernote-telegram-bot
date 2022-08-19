import json
from typing import Optional


class BotApiMock:
    def __init__(self, responses_filepath: str):
        with open(responses_filepath) as f:
            self._responses = json.load(f)
        self._response_index = 0

    async def __api_request(self, *args, **kwargs) -> dict:
        response = self._responses[self._response_index]
        self._response_index += 1
        return response

    async def setWebhook(self, url: str, certificate=None, max_connections=40, allowed_updates=None):
        return await self.__api_request(url, certificate, max_connections, allowed_updates)

    async def sendMessage(self, chat_id: int, text: str, reply_markup: Optional[str] = None, parse_mode=None) -> dict:
        return await self.__api_request(chat_id, text, reply_markup, parse_mode)

    async def editMessageReplyMarkup(self, chat_id: int, message_id, reply_markup):
        return await self.__api_request(chat_id, message_id, reply_markup)

    async def editMessageText(self, chat_id: int, message_id, text, reply_markup=None):
        return await self.__api_request(chat_id, message_id, text, reply_markup)

    async def getFile(self, file_id: str):
        return await self.__api_request(file_id)
