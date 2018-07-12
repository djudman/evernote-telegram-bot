class Storage:
    def insert(self, data):
        pass

    def update(self, query, data):
        pass

    def delete(self, query):
        pass

    def find(self, query):
        pass

    def get(self, classObject, query):
        if not isinstance(query, dict):
            query = { 'id': query }
        result = self.find(query)
        return next(iter(result))

    def create_model(self, model_class, data):
        model = model_class(data)
        model.storage = self
        return model

    def _generate_id(self):
        return ''


class MemoryStorage:
    __items = {}

    def insert(self, collection_name, data):
        entry_id = self._generate_id()
        data['id'] = entry_id
        if collection_name not in self.__items:
            self.__items[collection_name] = {}
        self.__items[collection_name][entry_id] = data

    def update(self, collection_name, query, data):
        collection_data = self.__items.get(collection_name)
        if not collection_data:
            raise Exception('Collection {} not found'.format(collection_name))
        for document_id, document in collection_data.items():
            if self._check_query(document, query):
                document.update(data)

    def delete(self, collection_name, query):
        collection_data = self.__items.get(collection_name)
        if not collection_data:
            raise Exception('Collection {} not found'.format(collection_name))
        ids_to_delete = []
        for document_id, document in collection_data.items():
            if self._check_query(document, query):
                ids_to_delete.append(document_id)
        for document_id in ids_to_delete:
            del collection_data[document_id]

    def find(self, collection_name, query, sort, skip=None, limit=None):
        collection_data = self.__items.get(collection_name)
        if not collection_data:
            raise Exception('Collection {} not found'.format(collection_name))
        objects = filter(lambda x: self._check_query(x, query), collection_data.values())
        objects = sorted(objects, key=lambda x: [x[k] for k, direction in sort])
        if skip is not None:
            objects = objects[skip:]
        if limit is not None:
            objects = objects[:limit]
        return objects

    def get(self, query: dict):
        for k, obj in self.__items.get(self.collection, {}).items():
            if self._check_query(obj, query):
                return obj

    def _check_query(self, entry: dict, query: dict):
        matched = True
        for k, query_value in query.items():
            key_value = entry
            for name in k.split('.'):
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
