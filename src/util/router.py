import importlib
import os
import re
from os.path import join


class UrlRouter:
    def __init__(self, config):
        url_files = []
        webapps_root = join(config['src_root'], 'web')
        for dirpath, dirnames, files in os.walk(webapps_root):
            paths = [join(dirpath, filename) for filename in files if filename == 'urls.py']
            url_files.extend(paths)
        url_files.sort()
        self.handlers = []
        for filename in url_files:
            spec = importlib.util.spec_from_file_location('urls', filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            urls = module.urls(config)
            for method, regex, handler in urls:
                handler_info = (method, re.compile(regex), handler)
                self.handlers.append(handler_info)

    def get_handler(self, url_path, http_method):
        for method, regex_object, handler in self.handlers:
            if method != http_method:
                continue
            if not regex_object.search(url_path):
                continue
            return handler
