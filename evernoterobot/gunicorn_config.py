import multiprocessing
import os
from os.path import join, dirname, realpath

current_dir = realpath(dirname(dirname(__file__)))

os.makedirs(join(current_dir, 'logs'), mode=0o700, exist_ok=True)

bind = '127.0.0.1:9001'
backlog = 128
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'aiohttp.worker.GunicornWebWorker'
pidfile = join(current_dir, 'evernoterobot.pid')
accesslog = join(current_dir, 'logs/gunicorn.log')
errorlog = join(current_dir, 'logs/gunicorn.log')
loglevel = 'info'
app_name = 'webapp:app'
access_log_format = '%a %l %u %t "%r" %s %b "%{Referrer}i" "%{User-Agent}i"'
daemon = True

# Run this command to start gunicorn
# $ gunicorn --config gunicorn_config.py webapp:app
