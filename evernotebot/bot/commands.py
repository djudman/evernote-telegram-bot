import json
from time import time

from evernotebot.telegram import Message, TelegramBotError

from evernotebot.bot.models import BotUser, EvernoteOauthData
import evernotebot.util.evernote.client as evernote


def start_command(bot, message: dict):
    user_id = message['from']['id']
    user_data = bot.users.get(user_id)
    if not user_data:
        current_time = time()
        telegram_user = message['from']
        user_data = {
            'id': user_id,
            'created': current_time,
            'last_request_ts': current_time,
            'bot_mode': 'multiple_notes',
            'telegram': {
                'first_name': telegram_user['first_name'],
                'last_name': telegram_user['last_name'],
                'username': telegram_user['username'],
                'chat_id': message['chat']['id'],
            },
            'evernote': {
                'access': {'permission': 'basic'},
            },
        }
        bot.users.create(user_data)

    user = BotUser(**user_data)
    message_text = '''Welcome! It's bot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with bot.'''

    chat_id = user.telegram.chat_id
    auth_button = {'text': 'Waiting for Evernote...', 'url': bot.url}
    inline_keyboard = json.dumps({'inline_keyboard': [[auth_button]]})
    status_message = bot.api.sendMessage(chat_id, message_text, inline_keyboard)
    key = bot.config['evernote']['access']['basic']['key']
    secret = bot.config['evernote']['access']['basic']['secret']
    oauth_callback = bot.config['oauth_callback']
    oauth_data = evernote.get_oauth_data(user.id, key, secret, oauth_callback, sandbox=bot.config.get('debug'))
    auth_button['text'] = 'Sign in with Evernote'
    auth_button['url'] = oauth_data['oauth_url']
    inline_keyboard = json.dumps({'inline_keyboard': [[auth_button]]})
    bot.api.editMessageReplyMarkup(chat_id, status_message['message_id'], inline_keyboard)
    user.evernote.oauth = EvernoteOauthData(
        token=oauth_data['oauth_token'],
        secret=oauth_data['oauth_token_secret'],
        callback_key=oauth_data['callback_key']
    )
    bot.users.save(user.asdict())


def switch_mode_command(bot, message: dict):
    user_id = message['from']['id']
    user_data = bot.users.get(user_id)
    if not user_data:
        raise TelegramBotError("Unregistered user {0}. You've to send /start to register.")
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


def switch_notebook_command(bot, message: dict):
    user_id = message['from']['id']
    user_data = bot.users.get(user_id)
    if not user_data:
        raise TelegramBotError("Unregistered user {0}. You've to send /start to register.")
    user = BotUser(**user_data)
    evernote_api = bot.get_evernote_api(user_id)
    all_notebooks = evernote_api.get_all_notebooks()
    buttons = []
    for notebook in all_notebooks:
        name = notebook['name']
        if name == user.evernote.notebook.name:
            name = f'> {name} <'
        buttons.append({'text': name})
    keyboard = {
        'keyboard': [[b] for b in buttons],
        'resize_keyboard': True,
        'one_time_keyboard': True,
    }
    bot.api.sendMessage(user.telegram.chat_id, 'Please, select notebook', json.dumps(keyboard))
    user.state = 'switch_notebook'
    bot.users.save(user.asdict())


def help_command(bot, message: dict):
    bot.send_message('''This is bot for Evernote (https://evernote.com).

Just send message to bot and it will create note in your Evernote notebook. 

You can send to bot:

* text
* photo (size < 12 Mb, telegram restriction)
* file (size < 12 Mb, telegram restriction)
* voice message (size < 12 Mb, telegram restriction)
* location

There are modes:

1) "One note" mode.
On this mode there is one note will be created in Evernote notebook. All messages you will send, be saved in this note.

2) "Multiple notes" mode (default).
On this mode for every message you sent, there will separate note be created in Evernote notebook.

You can switch bot mode with command /switch_mode
Note, every time you select "One note" mode, new note will create and set as current note for this bot.

Also, you can switch your current notebook with command /notebook
Note, if your bot is in "One note" mode and you are switching notebook, new note will create in newly selected notebook.

Contacts: djudman@gmail.com
''')
