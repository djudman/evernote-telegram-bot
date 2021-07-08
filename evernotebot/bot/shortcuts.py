import json
import random
import re
import string
from os.path import basename, join
from time import time
from typing import Callable
from urllib.parse import urlparse

from requests_oauthlib.oauth1_session import TokenRequestDenied

from evernotebot.bot.models import BotUser, EvernoteOauthData, EvernoteNotebook
from evernotebot.util.http import make_request


class OauthParams:
    def __init__(self, callback_key: str, verifier: str, access_type: str):
        if not re.match(r'^[a-zA-Z0-9]{40}$', callback_key):
            raise Exception('Invalid callback key')  # TODO: raise custom exception
        if access_type not in ('basic', 'full'):
            raise Exception('Invalid access')
        self.callback_key = callback_key
        self.verifier = verifier
        self.access_type = access_type


def evernote_oauth_callback(bot, params: OauthParams):
    query = {'evernote.oauth.callback_key': params.callback_key}
    user_data = bot.users.get(query, fail_if_not_exists=True)
    user = BotUser(**user_data)
    chat_id = user.telegram.chat_id
    if not params.verifier:
        bot.api.sendMessage(chat_id, 'We are sorry, but you have declined '
                                     'authorization.')
        return
    evernote_config = bot.config['evernote']['access'][params.access_type]
    oauth = user.evernote.oauth
    try:
        oauth_params = {
            'token': oauth.token,
            'secret': oauth.secret,
            'verifier': params.verifier,
        }
        user.evernote.access.token = bot.evernote().get_access_token(
            evernote_config['key'], evernote_config['secret'],
            sandbox=bot.config.get('debug', bot.config['debug']), **oauth_params)
    except TokenRequestDenied as e:
        bot.api.sendMessage(chat_id, 'We are sorry, but we have some problems '
                                     'with Evernote connection. '
                                     'Please try again later.')
        raise e
    except Exception as e:
        bot.api.sendMessage(chat_id, "Unknown error. Please, try again later.")
        raise e
    user.evernote.access.permission = params.access_type
    user.evernote.oauth = None
    if params.access_type == "basic":
        bot.api.sendMessage(chat_id, "Evernote account is connected.\nFrom now "
            "you can just send a message and a note will be created.")
        default_notebook = bot.evernote(user).get_default_notebook()
        user.evernote.notebook = EvernoteNotebook(**default_notebook)
        mode = user.bot_mode.replace("_", " ").capitalize()
        bot.api.sendMessage(chat_id, "Current notebook: "
            f"{user.evernote.notebook.name}\nCurrent mode: {mode}")
    else:
        bot.switch_mode(user, "one_note")
    bot.users.save(user.asdict())


def get_evernote_oauth_data(bot, bot_user: BotUser, message_text: str,
                            access='basic') -> EvernoteOauthData:
    chat_id = bot_user.telegram.chat_id
    auth_button = {'text': 'Waiting for Evernote...', 'url': bot.url}
    inline_keyboard = json.dumps({'inline_keyboard': [[auth_button]]})
    status_message = bot.api.sendMessage(chat_id, message_text, inline_keyboard)
    symbols = string.ascii_letters + string.digits
    session_key = ''.join([random.choice(symbols) for _ in range(32)])
    oauth_data = bot.evernote().get_oauth_data(bot_user.id, session_key,
        bot.config, access, bot.config.get('debug'))
    auth_button['text'] = 'Sign in with Evernote'
    auth_button['url'] = oauth_data['oauth_url']
    inline_keyboard = json.dumps({'inline_keyboard': [[auth_button]]})
    bot.api.editMessageReplyMarkup(chat_id, status_message['message_id'], inline_keyboard)
    return EvernoteOauthData(token=oauth_data['oauth_token'],
        secret=oauth_data['oauth_token_secret'],
        callback_key=oauth_data['callback_key'])


def get_cached_object(cache: dict, key: object, *, constructor: Callable=None):
    key = key or "default"
    if key in cache:
        return cache[key]["object"]
    if constructor is None:
        raise KeyError(f"Object with key `{key}` not found")
    new_object = constructor()
    cache[key] = {
        "created": time(),
        "object": new_object,
    }
    max_entries = 100
    if len(cache) > max_entries:
        oldest_key, _ = min(cache.items(), key=lambda entry: entry[1]["created"])
        del cache[oldest_key]
    return new_object


def download_telegram_file(telegram_api, file_id, dirpath="/tmp"):
    download_url = telegram_api.getFile(file_id)
    data = make_request(download_url)
    short_name = basename(urlparse(download_url).path)
    filename = join(dirpath, f"{file_id}_{short_name}")
    with open(filename, "wb") as f:
        f.write(data)
    return filename, short_name
