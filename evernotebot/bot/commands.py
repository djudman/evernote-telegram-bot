import json
import random
import string
from time import time

from utelegram import Message

from evernotebot.bot.models import BotUser, EvernoteOauthData
from evernotebot.bot.shortcuts import get_evernote_oauth_data


def start_command(bot, message: Message):
    user_id = message.from_user.id
    user_data = bot.users.get(user_id)
    if not user_data:
        current_time = time()
        telegram_user = message.from_user
        user_data = {
            'id': user_id,
            'created': current_time,
            'last_request_ts': current_time,
            'bot_mode': 'multiple_notes', # TODO: take from config
            'telegram': {
                'first_name': telegram_user.first_name,
                'last_name': telegram_user.last_name,
                'username': telegram_user.username,
                'chat_id': message.chat.id,
            },
            'evernote': {
                'access': {'permission': 'basic'},
            },
        }
        bot.users.create(user_data)

    user = BotUser(**user_data)
    message_text = '''Welcome! It's bot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with bot.'''
    oauth_data = get_evernote_oauth_data(bot, user, message_text)
    user.evernote.oauth = oauth_data
    bot.users.save(user.asdict())


def switch_mode_command(bot, message: Message):
    mode = message.text
    user_id = message.from_user.id
    user_data = bot.users.get(user_id)
    user = BotUser(**user_data)
    buttons = []
    for mode in ('one_note', 'multiple_notes'):
        title = mode.capitalize().replace('_', ' ')
        if user.bot_mode == mode:
            title = f'> {title} <'
        buttons.append({'text': title})
    keyboard = {
        'keyboard': [[b] for b in buttons],
        'resize_keyboard': True,
        'one_time_keyboard': True,
    }
    bot.api.sendMessage(user.telegram.chat_id, 'Please, select mode', json.dumps(keyboard))
    user.state = 'switch_mode'
    bot.users.save(user.asdict())


def switch_notebook_command(bot, message: Message):
    user_id = message.from_user.id
    user_data = bot.users.get(user_id)
    user = BotUser(**user_data)
    all_notebooks = bot.evernote.get_all_notebooks(user.evernote.access.token)
    buttons = []
    for notebook in all_notebooks:
        name = notebook["name"]
        if name == user.evernote.notebook.name:
            name = f"> {name} <"
        buttons.append({"text": name})
    keyboard = {
        "keyboard": [[b] for b in buttons],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }
    bot.api.sendMessage(user.telegram.chat_id, "Please, select notebook", json.dumps(keyboard))
    user.state = "switch_notebook"
    bot.users.save(user.asdict())


def help_command(bot, message: Message):
    help_text = '''This is bot for Evernote (https://evernote.com).

Just send message to bot and it creates note in your Evernote notebook. 

You can send to bot:

* text
* photo (size < 12 Mb) - Telegram restriction
* file (size < 12 Mb) - Telegram restriction
* voice message (size < 12 Mb) - Telegram restriction
* location

There are modes:

1) "One note" mode.
On this mode there are just one note will be created in Evernote notebook. All messages that you will send, will be saved in this note.

2) "Multiple notes" mode.
On this mode for every message you sent there is separate note will be created in Evernote notebook.

You can switch bot mode with command /switch_mode
Note that every time you select "One note" mode, new note will be created and set as current note for this bot.

Also, you can switch your current notebook with command /notebook
Note that every time you switch notebook in mode "One note", new note will be created in selected notebook.

We are sorry for low speed, but Evernote API are slow (about 1 sec per request).

Contacts: djudman@gmail.com
'''
    bot.api.sendMessage(message.chat.id, help_text)
