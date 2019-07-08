import hashlib
from time import time


class MemoryStorageException(Exception):
    pass


class MemoryStorage:
    def __init__(self):
        self._objects = {}

    def create(self, data, auto_generate_id=False):
        if "id" in data:
            object_id = data["id"]
        elif not auto_generate_id:
            raise MemoryStorageException("`id` required")
        else:
            key = "{0}{1}".format(time(), data).encode()
            object_id = hashlib.sha256(key).hexdigest()
        self._objects[object_id] = data
        return object_id

    def get(self, object_id, fail_if_not_exists=False):
        query = object_id if isinstance(object_id, dict) else {"id": object_id}
        objects = self.get_all(query)
        result = list(objects)
        if fail_if_not_exists and not result:
            raise MemoryStorageException(f"Object not found. Query: {query}")
        return result and result[0]

    def get_all(self, query=None):
        if query is None:
            query = {}
        return (x for x in self._objects.values() if self._check_query(x, query))

    def _check_query(self, document: dict, query: dict):
        matched = True
        for k, query_value in query.items():
            key_value = document
            for name in k.split("."):
                key_value = key_value.get(name) if isinstance(key_value, dict) else None
                if key_value is None:
                    break
            if isinstance(query_value, dict):
                matched = self._check_query(key_value, query_value)
            else:
                matched = key_value == query_value
            if not matched:
                return False
        return matched

    def save(self, data):
        return self.create(data)
