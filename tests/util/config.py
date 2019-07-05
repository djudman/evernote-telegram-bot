import logging
from evernotebot.config import load_config
bot_config = load_config()
logging.config.dictConfig({"version": 1})
