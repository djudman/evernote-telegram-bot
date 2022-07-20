import copy
import importlib
from typing import Dict, Optional, Generator

import evernotebot.storage.providers as providers


class Storage:
    def __init__(self, name: str, config: dict):
        provider_classpath = config['provider']
        module_name, class_name = provider_classpath.rsplit('.', 1)
        module = importlib.import_module(module_name)
        provider_class = getattr(module, class_name)
        config_copy = copy.deepcopy(config)
        del config_copy['provider']
        config_copy['collection'] = name
        self.provider = provider_class(**config_copy)

    def create(self, data: dict):
        if 'id' in data:
            return self.provider.create(data)
        return self.provider.create(data, auto_generate_id=True)

    def get(self, object_id: int, fail_if_not_exists: bool = False) -> Dict:
        return self.provider.get(object_id, fail_if_not_exists)

    def get_all(self, query: Optional[Dict] = None) -> Generator:
        return self.provider.get_all(query)

    def save(self, data: dict):
        return self.provider.save(data)

    def delete(self, object_id: int, check_deleted_count: bool = True):
        return self.provider.delete(object_id, check_deleted_count)

    def close(self):
        return self.provider.close()
