import socket
from .base import *
from .logging import LOG_SETTINGS


if socket.gethostname() == 'monika.local':
    DEBUG = True
