from telegram.bot import TelegramBotCommand
from bot.model import User

import json


class NotebookCommand(TelegramBotCommand):

    name = 'notebook'

    async def execute(self, message):
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        # message = await self.bot.api.sendMessage(
        #     chat_id, 'Please wait. Getting list of your notebooks...')
        access_token, guid = await self.bot.get_evernote_access_token(user_id)
        notebooks = await self.bot.list_notebooks(user_id)

        buttons = []
        for notebook in notebooks:
            if notebook['guid'] == guid:
                name = "> %s <" % notebook['name']
            else:
                name = notebook['name']
            buttons.append({'text': name})

        # await self.bot.api.editMessageText(chat_id, message['message_id'],
        #                                    'Please, select notebook')
        markup = json.dumps({
                'keyboard': [[b] for b in buttons],
                'resize_keyboard': True,
                'one_time_keyboard': True,
            })
        await self.bot.api.sendMessage(chat_id, 'Please, select notebook',
                                       reply_markup=markup)
        user = await User().get(user_id)
        user.state = 'select_notebook'
        await user.save()

        await self.bot.update_notebooks_cache(user_id)
