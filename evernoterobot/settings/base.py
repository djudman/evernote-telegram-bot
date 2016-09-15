import os
from os.path import dirname, join, realpath, basename
import json


DEBUG = False

PROJECT_DIR = realpath(dirname(dirname(__file__)))
ROOT_DIR = realpath(dirname(PROJECT_DIR))
PROJECT_NAME = basename(PROJECT_DIR.lower())
LOGS_DIR = join(realpath(ROOT_DIR), 'logs')
DOWNLOADS_DIR = join(realpath(ROOT_DIR), 'downloads')

secret_file = join(PROJECT_DIR, 'settings/secret.json')
if not os.path.exists(secret_file):
    secret_file = join(PROJECT_DIR, 'settings/secret.json.example')
with open(join(PROJECT_DIR, secret_file)) as f:
    SECRET = json.load(f)

SMTP = SECRET['smtp']
TELEGRAM = SECRET['telegram']
EVERNOTE = SECRET['evernote']

STORAGE = {
    'class': 'bot.storage.MongoStorage',
    'host': 'localhost',
    'port': 27017,
    'db': 'evernoterobot',
}

MEMCACHED = {
    'host': '127.0.0.1',
    'port': 11211,
}
