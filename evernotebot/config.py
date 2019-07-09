import copy
import json
import os
import logging
import sys
from logging import config, Formatter
from os import makedirs
from os.path import dirname, exists, join, realpath


_config_cache = None


def load_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    storage_config = {
        "class": "evernotebot.bot.storage.Mongo",
        "connection_string": "mongodb://{host}:27017/".format(
            host=os.environ.get("MONGO_HOST", "127.0.0.1")),
        "db_name": "evernotebot",
    }
    users_storage = copy.deepcopy(storage_config)
    users_storage["collection"] = "users"
    failed_updates_storage = copy.deepcopy(storage_config)
    failed_updates_storage["collection"] = "failed_updates"

    src_root = realpath(dirname(__file__))
    project_root = realpath(dirname(src_root))
    logs_root = join(project_root, "logs/")
    telegram_token = os.environ["TELEGRAM_API_TOKEN"]
    hostname = "evernotebot.djudman.info"

    config = {
        "debug": os.environ.get("EVERNOTEBOT_DEBUG", False),
        "host": hostname,
        "telegram": {
            "bot_url": "http://telegram.me/evernoterobot",
            "token": telegram_token,
            "webhook_url": f"https://{hostname}/{telegram_token}"
        },
        "evernote": {
            "oauth_callback_url": f"https://{hostname}/evernote/oauth",
            "access": {
                "basic": {
                    "key": os.environ["EVERNOTE_BASIC_ACCESS_KEY"],
                    "secret": os.environ["EVERNOTE_BASIC_ACCESS_SECRET"],
                },
                "full": {
                    "key": os.environ["EVERNOTE_FULL_ACCESS_KEY"],
                    "secret": os.environ["EVERNOTE_FULL_ACCESS_SECRET"],
                },
            },
        },
        "storage": {
            "users": users_storage,
            "failed_updates": failed_updates_storage,
        },
        "src_root": src_root,
        "html_root": join(src_root, "web/html"),
        "tmp_root": join(project_root, "tmp/"),
        "logs_root": logs_root,
        "uhttp": {
            "admins": [line.split(":", 1) for line in os.environ.get("EVERNOTEBOT_ADMINS", "").split(",") if line],
        },
    }
    makedirs(logs_root, exist_ok=True)
    makedirs(config["tmp_root"], exist_ok=True)
    logging_config = get_logging_config(logs_root)
    logging.config.dictConfig(logging_config)
    _config_cache = config
    return config


class JsonFormatter(Formatter):
    def format(self, record):
        return json.dumps({
            "logger": record.name,
            "file": "{0}:{1}".format(record.pathname, record.lineno),
            "data": record.msg,
        })


def get_logging_config(logs_root):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "class": "evernotebot.config.JsonFormatter",
            },
        },
        "handlers": {
            "evernotebot": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json",
            },
        },
        "loggers": {
            "uhttp": {
                "handlers": ["evernotebot"],
                "level": "DEBUG",
                "propagate": False,
            },
            "utelegram": {
                "handlers": ["evernotebot"],
                "level": "DEBUG",
                "propagate": False,
            },
            "evernotebot": {
                "handlers": ["evernotebot"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }
