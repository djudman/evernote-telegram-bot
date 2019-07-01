import json
import string
import random
from time import time
from typing import Callable

from requests_oauthlib.oauth1_session import TokenRequestDenied

from evernotebot.bot.models import BotUser, EvernoteOauthData, EvernoteNotebook


def evernote_oauth_callback(bot, callback_key, oauth_verifier,
                            access_type="basic"):
    query = {"evernote.oauth.callback_key": callback_key}
    user_data = bot.storage.get(query, fail_if_not_exists=True)
    user = BotUser(**user_data)
    chat_id = user.telegram.chat_id
    if not oauth_verifier:
        bot.api.sendMessage(chat_id, "We are sorry, but you have declined "
                                     "authorization.")
        return
    evernote_config = bot.config["evernote"]["access"][access_type]
    oauth = user.evernote.oauth
    try:
        oauth_params = {
            "token": oauth.token,
            "secret": oauth.secret,
            "verifier": oauth_verifier,
        }
        user.evernote.access.token = bot.evernote().get_access_token(
            evernote_config["key"], evernote_config["secret"],
            sandbox=bot.config.get("debug", True), **oauth_params)
    except TokenRequestDenied as e:
        bot.api.sendMessage(chat_id, "We are sorry, but we have some problems "
                                     "with Evernote connection. "
                                     "Please try again later.")
        raise e
    except Exception as e:
        bot.api.sendMessage(chat_id, "Unknown error. Please, try again later.")
        raise e
    user.evernote.access.permission = access_type
    user.evernote.oauth = None
    if access_type == "basic":
        bot.api.sendMessage(chat_id, "Evernote account is connected.\nFrom now "
            "you can just send a message and a note will be created.")
        default_notebook = bot.evernote(user).get_default_notebook()
        user.evernote.notebook = EvernoteNotebook(**default_notebook)
        mode = user.bot_mode.replace("_", " ").capitalize()
        bot.api.sendMessage(chat_id, "Current notebook: "
            f"{user.evernote.notebook.name}\nCurrent mode: {mode}")
    else:
        bot.switch_mode(user, "one_note")
    bot.storage.save(user.asdict())


def get_evernote_oauth_data(bot, user_id: int, chat_id: int, message_text: str,
                            button_text: str, access="basic") -> EvernoteOauthData:
    auth_button = {"text": "Waiting for Evernote...", "url": bot.url}
    inline_keyboard = json.dumps({"inline_keyboard": [[auth_button]]})
    status_message = bot.api.sendMessage(chat_id, message_text, inline_keyboard)
    symbols = string.ascii_letters + string.digits
    session_key = "".join([random.choice(symbols) for _ in range(32)])
    oauth_data = bot.evernote().get_oauth_data(user_id, session_key,
        bot.config["evernote"], access, bot.config.get("debug"))
    auth_button["text"] = button_text
    auth_button["url"] = oauth_data["oauth_url"]
    inline_keyboard = json.dumps({"inline_keyboard": [[auth_button]]})
    bot.api.editMessageReplyMarkup(chat_id, status_message["message_id"], inline_keyboard)
    return EvernoteOauthData(token=oauth_data["oauth_token"],
        secret=oauth_data["oauth_token_secret"],
        callback_key=oauth_data["callback_key"])


def get_cached_object(cache: dict, key: object, *, constructor: Callable=None):
    def create_object():
        if constructor is None:
            raise KeyError(f"Object with key `{key}` not found")
        return constructor()

    if key is None:
        default = cache.get("default")
        if default is None:
            default = create_object()
            cache["default"] = default
        return default
    entry = cache.get(key)
    if entry:
        return entry["object"]
    max_entries = 100
    current_time = time()
    if len(cache) >= max_entries:
        oldest_key = None
        min_time = current_time
        for k, v in cache.items():
            if v["created"] < min_time:
                oldest_key = k
        del cache[oldest_key]
    new_entry = {
        "created": current_time,
        "object": create_object(),
    }
    cache[key] = new_entry
    return new_entry["object"]
