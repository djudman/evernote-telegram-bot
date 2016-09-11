import json

import asyncio

from bot import User
from ext.botan_async import track
from ext.telegram.bot import TelegramBotCommand
from ext.telegram.models import Message


class SwitchModeCommand(TelegramBotCommand):

    name = 'switch_mode'

    async def execute(self, message: Message):
        asyncio.ensure_future(track(message.user.id, message.raw))
        user = User.get({'id': message.user.id})
        buttons = []
        for mode in ['one_note', 'multiple_notes']:
            if user.mode == mode:
                name = "> %s <" % mode.capitalize().replace('_', ' ')
            else:
                name = mode.capitalize().replace('_', ' ')
            buttons.append({'text': name})

        markup = json.dumps({
                'keyboard': [[b] for b in buttons],
                'resize_keyboard': True,
                'one_time_keyboard': True,
            })
        asyncio.ensure_future(
            self.bot.api.sendMessage(user.telegram_chat_id, 'Please, select mode', reply_markup=markup)
        )
        user.state = 'switch_mode'
        user.save()
