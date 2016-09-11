import asyncio

from ext.botan_async import track
from ext.telegram.bot import TelegramBotCommand
from ext.telegram.models import Message


class HelpCommand(TelegramBotCommand):

    name = 'help'

    async def execute(self, message: Message):
        asyncio.ensure_future(track(message.user.id, message.raw))
        text = '''This is bot for Evernote (https://evernote.com).

Just send message to bot and it creates note in your Evernote notebook. You can send to bot:

* text
* photo (size < 12 Mb) - Telegram restriction
* file (size < 12 Mb) - Telegram restriction
* voice message (size < 12 Mb) - Telegram restriction
* location

Bot can works in two modes
1) "One note" mode.
In this mode there are in evernote notebook will be created just one note. All messages \
you sent will be saved in this note.

2) "Multiple notes" mode.
In this mode for every message you sent there are in evernote notebook separate note will be created .

You can switch bot mode with command /switch_mode
Note that every time you select "One note" mode, new note will be created and set as current note for this bot.

Also, you can switch your current notebook with command /notebook
Note that every time you switch notebook in mode "One note", new note will be created in selected notebook.

We are sorry for low speed, but Evernote API are slow (about 1-2 sec per request).

Contacts: djudman@gmail.com
'''
        asyncio.ensure_future(self.bot.api.sendMessage(message.chat.id, text))
