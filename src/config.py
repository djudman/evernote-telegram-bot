import json
import logging.config
from os import makedirs
from os.path import dirname
from os.path import join
from os.path import realpath


class ConfigLoader:
    def __init__(self):
        self.project_root = realpath(dirname(__file__))

    def load(self):
        filenames = [
            join(self.project_root, 'local.yaml'),
            join(self.project_root, 'config.yaml'),
        ]
        config = ChainMap()
        config.maps.append({
            'project_root': self.project_root,
            'tmp_root': join(realpath(dirname(self.project_root)), 'tmp'),
            'logs_root': join(realpath(dirname(self.project_root)), 'logs'),
        })
        for name in filenames:
            if not exists(name):
                continue
            with open(name) as f:
                data = yaml.load(f)
                config.maps.append(data)
        logging_config = self.get_logging_config(config['logs_root'])
        logging.config.dictConfig(logging_config)
        return config

    def get_logging_config(self, logs_root):
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
