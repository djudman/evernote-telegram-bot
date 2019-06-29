class MemoryStorageException(Exception):
    pass


class MemoryStorage:
    def __init__(self):
        self._objects = {}

    def create(self, data):
        if "id" not in data:
            raise MemoryStorageException("`id` required")
        object_id = data["id"]
        self._objects[object_id] = data
        return object_id

    def get(self, object_id):
        return self._objects.get(object_id)

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
