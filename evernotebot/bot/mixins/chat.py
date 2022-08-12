import json
from typing import Dict, List, Optional

from evernotebot.bot.mixins.bot_api import BotApiMixin
from evernotebot.bot.mixins.user import UserMixin


class ChatMixin(UserMixin, BotApiMixin):
    def __init__(self, config: dict):
        super(ChatMixin, self).__init__(config)

    async def send_message(
            self,
            text: str,
            buttons: List[Dict] = None,
            keyboard_data: Optional[Dict] = None,
            parse_mode=None
    ) -> Optional[Dict]:

        keyboard = None
        if keyboard_data is not None:
            keyboard = json.dumps(keyboard_data)
        elif buttons is not None:
            keyboard = json.dumps({'inline_keyboard': [buttons]})
        chat_id = self.user['chat_id']
        message = await self.api.sendMessage(chat_id, text, keyboard, parse_mode)
        return message

    async def edit_message(self, message_id: int, text: str = None, buttons: List[Dict] = None):
        inline_keyboard = json.dumps({'inline_keyboard': []})
        if buttons is not None:
            inline_keyboard = json.dumps({'inline_keyboard': [buttons]})
        chat_id = self.user['chat_id']
        if text is not None:
            await self.api.editMessageText(chat_id, message_id, text, inline_keyboard)
        else:
            await self.api.editMessageReplyMarkup(chat_id, message_id, inline_keyboard)
