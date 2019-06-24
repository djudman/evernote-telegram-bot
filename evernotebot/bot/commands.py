import json
import logging
import random
import string
from utelegram.models import Message
from evernotebot.bot.models import BotUser, EvernoteOauthData


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


def start_command(bot, message: Message):
    user_id = message.from_user.id
    user_data = bot.storage.get(user_id)
    if not user_data:
        user_data = register_user(bot, message)
    user = BotUser(**user_data)
    message_text = '''Welcome! It's bot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with bot.'''
    button_text = 'Sign in to Evernote'
    oauth(bot, user, message_text, button_text)
    bot.storage.save(user.asdict())


def register_user(bot, telegram_message: Message) -> BotUser:
    telegram_user = telegram_message.from_user
    user_data = {
        'id': telegram_user.id,
        'bot_mode': 'multiple_notes', # TODO: take from config
        'telegram': {
            'first_name': telegram_user.first_name,
            'last_name': telegram_user.last_name,
            'username': telegram_user.username,
            'chat_id': telegram_message.chat.id,
        },
        'evernote': {
            'access': {'permission': 'basic'},
        },
    }
    bot.storage.create(user_data)
    return user_data


def oauth(bot, user: BotUser, message_text: str, button_text: str, access='basic'):  # TODO: move somewhere
    chat_id = user.telegram.chat_id
    signin_button = {
        'text': 'Waiting for Evernote...',
        'url': bot.url,
    }
    inline_keyboard = {'inline_keyboard': [[signin_button]]}
    status_message = bot.api.sendMessage(chat_id, message_text, json.dumps(inline_keyboard))
    symbols = string.ascii_letters + string.digits
    session_key = ''.join([random.choice(symbols) for _ in range(32)])
    oauth_data = bot.evernote.get_oauth_data(user.id, session_key, bot.config['evernote'], access)
    user.evernote.oauth = EvernoteOauthData(
        callback_key=oauth_data['callback_key'],
        token=oauth_data['oauth_token'],
        secret=oauth_data['oauth_token_secret']
    )
    signin_button['text'] = button_text
    signin_button['url'] = oauth_data['oauth_url']
    bot.api.editMessageReplyMarkup(chat_id, status_message['message_id'], json.dumps(inline_keyboard))


def switch_mode_command(bot, message: Message):
    mode = message.text
    user_id = message.from_user.id
    user_data = bot.storage.get(user_id)
    user = BotUser(**user_data)
    buttons = []
    for mode in ('one_note', 'multiple_notes'):
        name = mode.capitalize().replace('_', ' ')
        if user.bot_mode == mode:
            name = '> {} <'.format(name)
        buttons.append({'text': name})
    keyboard = {
        'keyboard': [[b] for b in buttons],
        'resize_keyboard': True,
        'one_time_keyboard': True,
    }
    bot.api.sendMessage(user.telegram.chat_id, 'Please, select mode', json.dumps(keyboard))
    user.state = 'switch_mode'
    bot.storage.save(user.asdict())


def switch_notebook_command(bot, message: Message):
    user_id = message.from_user.id
    user_data = bot.storage.get(user_id)
    user = BotUser(**user_data)
    user.state = 'switch_notebook'
    bot.storage.save(user.asdict())
    all_notebooks = bot.evernote.get_all_notebooks(user.evernote.access.token)
    buttons = []
    for notebook in all_notebooks:
        name = notebook['name']
        if name == user.evernote.notebook.name:
            name = '> {} <'.format(name)
        buttons.append({'text': name})
    keyboard = {
        'keyboard': [[b] for b in buttons],
        'resize_keyboard': True,
        'one_time_keyboard': True,
    }
    bot.api.sendMessage(user.telegram.chat_id, 'Please, select notebook', json.dumps(keyboard))
