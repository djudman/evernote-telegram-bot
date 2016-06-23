import sys
import multiprocessing
import os
from os.path import join, dirname, realpath

sys.path.insert(0, realpath(dirname(__file__)))

import settings


os.makedirs(settings.LOGS_DIR, mode=0o700, exist_ok=True)

bind = '127.0.0.1:9001'
backlog = 128
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'aiohttp.worker.GunicornWebWorker'
pidfile = join(settings.ROOT_DIR, 'evernoterobot.pid')
accesslog = join(settings.LOGS_DIR, 'gunicorn.log')
errorlog = join(settings.LOGS_DIR, 'gunicorn.log')
loglevel = 'info'
app_name = 'web.webapp:app'
access_log_format = '%a %l %u %t "%r" %s %b "%{Referrer}i" "%{User-Agent}i"'
daemon = True

# Run this command to start gunicorn
# $ gunicorn --config gunicorn_config.py webapp:app
