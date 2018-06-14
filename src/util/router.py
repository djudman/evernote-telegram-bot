import importlib
import os
import re
from os.path import join


class UrlRouter:
    def __init__(self, project_root):
        if not os.path.exists(project_root):
            raise FileNotFoundError(project_root)
        url_files = []
        for dirpath, dirnames, files in os.walk(project_root):
            paths = [join(dirpath, filename) for filename in files if filename == 'urls.py']
            url_files.extend(paths)
        url_files.sort()
        self.handlers = []
        for filename in url_files:
            spec = importlib.util.spec_from_file_location('urls', filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for method, regex, handler in module.urls:
                handler_info = (method, re.compile(regex), handler)
                self.handlers.append(handler_info)

    def get_handler(self, url_path, http_method):
        for method, regex_object, handler in self.handlers:
            if method != http_method:
                continue
            if not regex_object.search(url_path):
                continue
            return handler
