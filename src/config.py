from os.path import dirname
from os.path import join
from os.path import realpath


DEBUG = True
PROJECT_ROOT = lambda x: join(dirname(realpath(__file__)), x)

SETTINGS = {
    'project_root': PROJECT_ROOT(''),
    'tmp_root': PROJECT_ROOT('../tmp'),
    'logs_root': PROJECT_ROOT('../logs'),
}

EVERNOTE = {
    'access': {
        'token': '',
        'basic': {
            'key': '',
            'secret': '',
            'oauth_callback': '',
        },
        'full': {
            'key': '',
            'secret': '',
            'oauth_callback': '',
        },
    },
}

TELEGRAM = {
    'token': 'secret',
    'webhook_url': '',
}
