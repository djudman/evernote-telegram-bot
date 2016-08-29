import socket
from .logging import LOG_SETTINGS

DEV_HOSTS = ['monika.local', 'road404-dorofeev.local']
if socket.gethostname() in DEV_HOSTS:
    from .dev import *
else:
    from .base import *
