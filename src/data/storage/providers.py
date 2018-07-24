import copy
import uuid
import re
from abc import ABC
from abc import abstractmethod
from util.mongo import MongoConnection


class Base(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def insert(self, data):
        pass

    @abstractmethod
    def update(self, query, update):
        pass

    @abstractmethod
    def delete(self, query):
        pass

    @abstractmethod
    def count(self, query):
        pass

    @abstractmethod
    def get(self, query):
        pass

    @abstractmethod
    def get_all(self, query, **kwargs):
        pass


class MemoryProvider(Base):
    def __init__(self, config):
        super().__init__(config)
        self.data = {}

    def _generate_id(self):
        return uuid.uuid4().hex

    def insert(self, data):
        document_id = self._generate_id()
        data['id'] = document_id
        self.data[document_id] = data
        return document_id

    def update(self, query, update):
        for document_id, document in self.data.items():
            if self._check_query(document, query):
                document.update(update)
        return document

    def delete(self, query):
        ids_to_delete = []
        for document_id, document in self.data.items():
            if self._check_query(document, query):
                ids_to_delete.append(document_id)
        for document_id in ids_to_delete:
            del self.data[document_id]

    def get_all(self, query, **kwargs):
        objects = [x for x in self.data.values() if self._check_query(x, query)]
        sort = kwargs.get('sort')
        if sort:
            objects = sorted(objects, key=lambda x: [x[k] for k, direction in sort]) # TODO: что-то странная сортировка
        skip = kwargs.get('skip')
        if skip is not None:
            objects = objects[skip:]
        limit = kwargs.get('limit')
        if limit is not None:
            objects = objects[:limit]
        return objects

    def get(self, query):
        if not isinstance(query, dict):
            query = { 'id': query }
        for obj in self.data.values():
            if self._check_query(obj, query):
                return obj

    def count(self, query=None):
        if query is None:
            return len(self.data.keys())
        return len(self.get_all(query))

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


class MongoProvider(Base):
    def __init__(self, config):
        super().__init__(config)
        connection_string = config['connection_string']
        self.db = config['db']
        self.collection = config['collection']
        self.connection = MongoConnection(connection_string)

    def insert(self, data):
        if 'id' in data:
            data['_id'] = data['id']
            del data['id']
        else:
            data['_id'] = self.connection.generate_id()
        inserted_id = self.connection.insert(self.db, self.collection, data)
        return inserted_id

    def _prepare_query(self, query):
        if 'id' in query:
            query['_id'] = query['id']
            del query['id']
        for field, value in copy.deepcopy(query).items():
            if re.search(r'^id\.', field): # TODO: check this
                query['_{}'.format(field)] = value
                del query[field]
        return query

    def update(self, query, update):
        query = self._prepare_query(query)
        return self.connection.update(self.db, self.collection, query, update)

    def count(self, query):
        query = self._prepare_query(query)
        return self.connection.count(self.db, self.collection, query)

    def delete(self, query):
        query = self._prepare_query(query)
        return self.connection.delete(self.db, self.collection, query)

    def get(self, query):
        if isinstance(query, dict):
            query = self._prepare_query(query)
        document = self.connection.find_one(self.db, self.collection, query)
        if document:
            document['id'] = document['_id']
            del document['_id']
            return document

    def get_all(self, query, **kwargs):
        query = self._prepare_query(query)
        cursor = self.connection.find_many(self.db, self.collection, query, **kwargs)
        results = []
        for document in cursor:
            document['id'] = document['_id']
            del document['_id']
            results.append(document)
        return results
