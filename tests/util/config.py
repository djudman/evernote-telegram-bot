import logging
from evernotebot.config import load_config


bot_config = load_config()
bot_config["storage"] = {
    "users": {"class": "util.storage.MemoryStorage"},
    "failed_updates": {"class": "util.storage.MemoryStorage"},
}
logging.config.dictConfig({"version": 1})
