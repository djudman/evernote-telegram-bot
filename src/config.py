import json
from os.path import dirname
from os.path import join
from os.path import realpath


DEBUG = True
PROJECT_ROOT = lambda x: join(dirname(realpath(__file__)), x)

SETTINGS = {
    'project_root': PROJECT_ROOT(''), # FIXME: too many calls
    'tmp_root': PROJECT_ROOT('../tmp'),
    'logs_root': PROJECT_ROOT('../logs'),
}

with open('config.json', 'r') as f:
    local_config = json.load(f)

HOST = local_config['host']
EVERNOTE = local_config['evernote']
TELEGRAM = local_config['telegram']
