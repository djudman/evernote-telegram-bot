import socket
from .logging import LOG_SETTINGS


if socket.gethostname() == 'monika.local':
    from .dev import *
else:
    from .base import *
