from telegram.bot import TelegramBotCommand

import json


class NotebookCommand(TelegramBotCommand):

    name = 'notebook'

    async def execute(self, message):
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        # message = await self.bot.api.sendMessage(
        #     chat_id, 'Please wait. Getting list of your notebooks...')
        access_token, guid = await self.bot.get_evernote_access_token(user_id)
        notebooks = self.bot.evernote.list_notebooks(access_token)

        buttons = []
        for notebook in notebooks:
            if notebook.guid == guid:
                name = ">>> %s (current)" % notebook.name
            else:
                name = notebook.name
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
