import copy
import logging.config
import yaml
from os import makedirs
from os.path import dirname
from os.path import exists
from os.path import join
from os.path import realpath


def load_config():
    src_root = realpath(dirname(__file__))
    project_root = realpath(dirname(src_root))
    filenames = [join(src_root, filename) for filename in ('config.yaml', 'local.yaml')]
    config = {}
    for name in filenames:
        if not exists(name):
            continue
        with open(name) as f:
            data = yaml.load(f)
            config = merge_dicts(config, data)
    config.update({
        'src_root': src_root,
        'tmp_root': join(project_root, 'tmp/'),
        'logs_root': join(project_root, 'logs/'),
    })
    hostname = config['host']
    token = config['telegram']['token']
    config['webhook_url'] = f'https://{hostname}/{token}'
    oauth_url_path = config['evernote']['oauth_path']
    config['evernote']['oauth_callback_url'] = f'https://{hostname}{oauth_url_path}'
    makedirs(config['logs_root'], exist_ok=True)
    makedirs(config['tmp_root'], exist_ok=True)
    logging_config = get_logging_config(config['logs_root'])
    logging.config.dictConfig(logging_config)
    return config


def merge_dicts(dict1, dict2):
    result = copy.deepcopy(dict1)
    for k2, v2 in dict2.items():
        v1 = dict1.get(k2)
        if type(v1) == type(v2) and isinstance(v1, dict):
            result[k2] = merge_dicts(v1, v2)
        elif type(v1) == type(v2) and isinstance(v1, list):
            result[k2] = list(set(v1).union(set(v2)))
        else:
            result[k2] = v2
    return result


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
