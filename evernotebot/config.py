import json
import os
import logging
import sys
from logging import config, Formatter
from os import makedirs
from os.path import dirname, exists, join, realpath


class JsonFormatter(Formatter):
    def format(self, record):
        return json.dumps({
            "logger": record.name,
            "file": record.pathname,
            "line": record.lineno,
            "data": record.msg,
        })


def base_config():
    return {
        "debug": os.environ.get("EVERNOTEBOT_DEBUG", False),
        "host": "evernotebot.djudman.info",
        "telegram": {
            "bot_url": "http://telegram.me/evernoterobot",
            "token": os.environ["TELEGRAM_API_TOKEN"],
        },
        "evernote": {
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
            "connection_string": f"mongodb://{os.environ.get('MONGO_HOST', '127.0.0.1')}:27017/",
            "db": "evernotebot",
            "collection": "users",
        }
    }


def load_config():
    src_root = realpath(dirname(__file__))
    config = base_config()
    project_root = realpath(dirname(src_root))
    logs_root = join(project_root, "logs/")
    config.update({
        "src_root": src_root,
        "tmp_root": join(project_root, "tmp/"),
        "logs_root": logs_root,
    })
    hostname = config["host"]
    token = config["telegram"]["token"]
    config["webhook_url"] = f"https://{hostname}/{token}"
    config["evernote"]["oauth_callback_url"] = f"https://{hostname}/evernote/oauth"
    logging_config = get_logging_config(logs_root)
    makedirs(logs_root, exist_ok=True)
    makedirs(config["tmp_root"], exist_ok=True)
    logging.config.dictConfig(logging_config)
    return config


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
