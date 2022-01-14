import os
from pathlib import Path

import re
import yaml

from evernotebot.util.logs import init_logging


env_matcher = re.compile(r'\$\{([^{}]+)\}(:(.+))?')

def env_constructor(loader, node):
    value = node.value
    match = env_matcher.match(value)
    var_name, _, default = match.groups()
    env_value = os.environ.get(var_name, default)
    if env_value is not None:
        return yaml.safe_load(env_value)

class EnvVarLoader(yaml.SafeLoader):
    pass

EnvVarLoader.add_implicit_resolver('!env', env_matcher, None)
EnvVarLoader.add_constructor('!env', env_constructor)


def load_config():
    filename = Path(__file__).parent.parent.joinpath('config.yaml').absolute()
    with open(filename, 'r') as f:
        config = yaml.load(f, Loader=EnvVarLoader)
    init_logging(debug=config['debug'])
    return config