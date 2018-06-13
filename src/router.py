import os
from os.path import basename
from os.path import join


class UrlRouter:
    def __init__(self, project_root):
        self.handlers = []
        url_files = []
        for dirname, files in os.walk(project_root):
            url_files = [join(dirname, filename) for filename in files if 'urls.py' in basename(filename)]
        # TODO: sort files
        # TODO: import url from filename
        # TODO: fill self.handlers

    def get_handler(self, url_path):
        # FIXME:
        from api.handlers import telegram_hook
        return telegram_hook
