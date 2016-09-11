import json

import asyncio

from bot import User
from ext.botan_async import track
from ext.telegram.bot import TelegramBotCommand
from ext.telegram.models import Message


class NotebookCommand(TelegramBotCommand):

    name = 'notebook'

    async def execute(self, message: Message):
        asyncio.ensure_future(track(message.user.id, message.raw))
        user = User.get({'id': message.user.id})
        notebooks = await self.bot.list_notebooks(user)

        buttons = []
        inline_buttons = []
        for notebook in notebooks:
            if notebook['guid'] == user.current_notebook['guid']:
                name = "> %s <" % notebook['name']
            else:
                name = notebook['name']
            buttons.append({'text': name})
            inline_buttons.append({
                'text': name,
                'callback_data': json.dumps({'cmd': 'set_nb', 'nb': notebook['guid']})
            })

        markup = json.dumps({
                'keyboard': [[b] for b in buttons],
                'resize_keyboard': True,
                'one_time_keyboard': True,
            })
        markup = json.dumps({'inline_keyboard': [[b] for b in inline_buttons]})
        asyncio.ensure_future(
            self.bot.api.sendMessage(user.telegram_chat_id, 'Please, select notebook', reply_markup=markup)
        )
        user.state = 'select_notebook'
        user.save()
        asyncio.ensure_future(self.bot.update_notebooks_cache(user))
