import json
import os
import re
from logging import Formatter


def load_config():
    filename = 'evernotebot.config.json'
    with open(filename, 'r') as f:
        config_str_data = f.read()
    matches = re.findall(r'\$\{([0-9a-zA-Z_]+)\}', config_str_data)
    defaults = {
        'MONGO_HOST': '127.0.0.1',
        'EVERNOTEBOT_DEBUG': False,
    }
    for name in matches:
        value = os.getenv(name, defaults.get(name))
        if value is None:
            raise Exception(f"Environment variable `{name}` isn't set")
        if not isinstance(value, str):
            value = str(value).lower()
        config_str_data = config_str_data.replace(f'${{{name}}}', value)
    return json.loads(config_str_data)


class JsonFormatter(Formatter):
    def format(self, record):
        return json.dumps({
            'logger': record.name,
            'file': '{0}:{1}'.format(record.pathname, record.lineno),
            'data': record.msg,
        })
