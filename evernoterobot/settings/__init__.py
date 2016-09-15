import socket
from .logging import LOG_SETTINGS

LIVE_HOSTS = ['hamster']
if socket.gethostname() in LIVE_HOSTS:
    from .base import *
else:
    from .dev import *
