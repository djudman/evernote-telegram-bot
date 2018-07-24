import json
import logging.config
import yaml
from collections import ChainMap
from os import makedirs
from os.path import dirname
from os.path import exists
from os.path import join
from os.path import realpath


def load_config():
    project_root = realpath(dirname(__file__))
    filenames = [
        join(project_root, 'local.yaml'),
        join(project_root, 'config.yaml'),
    ]
    config = ChainMap()
    config.maps.append({
        'project_root': project_root,
        'tmp_root': join(realpath(dirname(project_root)), 'tmp'),
        'logs_root': join(realpath(dirname(project_root)), 'logs'),
    })
    for name in filenames:
        if not exists(name):
            continue
        with open(name) as f:
            data = yaml.load(f)
            config.maps.append(data)
    logging_config = get_logging_config(config['logs_root'])
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
                'class': 'logging.FileHandler',
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
