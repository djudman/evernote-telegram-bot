import json
import string
import random

from utelegram.bot import TelegramBotError
from requests_oauthlib.oauth1_session import TokenRequestDenied

from evernotebot.bot.models import BotUser, EvernoteOauthData, EvernoteNotebook


def evernote_oauth_callback(bot, callback_key, oauth_verifier,
                            access_type="basic"):
    users = list(bot.storage.get_all({"evernote.oauth.callback_key": callback_key}))
    if not users:
        raise Exception(f"User not found. callback_key = {callback_key}")
    user_data = next(iter(users))
    user = BotUser(**user_data)
    chat_id = user.telegram.chat_id
    if not oauth_verifier:
        bot.api.sendMessage(chat_id, "We are sorry, but you have declined authorization.")
        return
    evernote_config = bot.config["evernote"]["access"][access_type]
    oauth = user.evernote.oauth
    try:
        user.evernote.access.token = bot.evernote().get_access_token(
            evernote_config["key"],
            evernote_config["secret"],
            oauth.token,
            oauth.secret,
            oauth_verifier,
            bot.config.get("debug", True))
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
    bot.storage.save(user.asdict())
    if access_type == "basic":
        text = "Evernote account is connected.\nFrom now you can just send a message and a note will be created."
        bot.api.sendMessage(chat_id, text)
        default_notebook = bot.evernote(user).get_default_notebook()
        user.evernote.notebook = EvernoteNotebook(**default_notebook)
        bot.storage.save(user.asdict())
        mode = user.bot_mode.replace("_", " ").capitalize()
        bot.api.sendMessage(chat_id, f"Current notebook: {user.evernote.notebook.name}\nCurrent mode: {mode}")
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
