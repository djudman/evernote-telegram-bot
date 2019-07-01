import copy
import logging.config
import yaml
from os import makedirs
from os.path import dirname, exists, join, realpath


def load_config():
    src_root = realpath(dirname(__file__))
    config = {}
    for name in ("config.yaml", "local.yaml"):
        filepath = join(src_root, name)
        if not exists(filepath):
            continue
        with open(filepath) as f:
            data = yaml.load(f)
            config = copy.deepcopy({**config, **data})
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
    oauth_url_path = config["evernote"]["oauth_path"]
    config["evernote"]["oauth_callback_url"] = f"https://{hostname}{oauth_url_path}"
    logging_config = get_logging_config(logs_root)
    makedirs(logs_root, exist_ok=True)
    makedirs(config["tmp_root"], exist_ok=True)
    logging.config.dictConfig(logging_config)
    return config


def get_logging_config(logs_root):
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - PID:%(process)d - %(levelname)s - %(message)s (%(pathname)s:%(lineno)d)',
            },
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'default',
                'filename': join(logs_root, 'evernoterobot.log')
            },
        },
        'loggers': {
            '': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
