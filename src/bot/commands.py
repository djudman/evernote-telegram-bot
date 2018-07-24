import random
import string
from bot.models import User


def help_command(bot, chat_id):
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
    bot.api.sendMessage(chat_id, help_text)


def start_command(bot, telegram_message):
    telegram_user = telegram_message.from_user
    user = bot.get_storage(User).get(telegram_user.id)
    if not user:
        user = register_user(bot, telegram_message)
    welcome_text = '''Welcome! It's bot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with bot.'''
    signin_button = {
        'text': 'Waiting for Evernote...',
        'url': bot.url,
    }
    inline_keyboard = {'inline_keyboard': [[signin_button]]}
    bot.api.sendMessage(telegram_message.chat.id, welcome_text, inline_keyboard)
    evernote_config = bot.config['evernote']['access']['basic']
    symbols = string.ascii_letters + string.digits
    session_key = ''.join([random.choice(symbols) for i in range(32)])
    oauth_data = bot.evernote.get_oauth_data(user.id, evernote_config, session_key)
    user.telegram.from_dict({
        'first_name': telegram_user.first_name,
        'last_name': telegram_user.last_name,
        'username': telegram_user.username,
        'chat_id': telegram_message.chat.id,
    })
    user.evernote.oauth.from_dict({}) # TODO:


def register_user(bot, telegram_message):
    telegram_user = telegram_message.from_user
    user_data = {
        'id': telegram_user.id,
        'bot_mode': 'multiple_notes', # TODO: take from config
        'telegram': {
            'first_name': telegram_user.first_name,
            'last_name': telegram_user.last_name,
            'username': telegram_user.username,
            'chat_id': telegram_message.chat.id,
        }
    }
    user = bot.get_storage(User).create_model(user_data)
    user.save()
    return user
