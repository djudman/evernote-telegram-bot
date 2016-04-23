from os.path import dirname, join, realpath, basename
import json

DEBUG = False

PROJECT_DIR = realpath(dirname(dirname(__file__)))
ROOT_DIR = realpath(dirname(PROJECT_DIR))
PROJECT_NAME = basename(PROJECT_DIR.lower())
LOGS_DIR = join(realpath(ROOT_DIR), 'logs')

with open(join(PROJECT_DIR, 'settings/secret.json')) as f:
    SECRET = json.load(f)

SMTP = SECRET['smtp']
WEBHOOK_URL = "https://evernoterobot.djudman.info/%s" % SECRET['token']
