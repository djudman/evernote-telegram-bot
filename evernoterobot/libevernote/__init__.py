import sys
from os.path import dirname, realpath, join

sys.path.insert(0, join(realpath(dirname(__file__)), 'evernote-sdk-python3/lib'))

from evernote.api.client import EvernoteClient as EvernoteSdk
