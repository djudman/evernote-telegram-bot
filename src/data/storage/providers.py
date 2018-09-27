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
        document_id = data.get('id') or self._generate_id()
        data['id'] = document_id
        self.data[document_id] = data
        return document_id

    def update(self, query, new_document):
        keys_to_update = [key for key, document in self.data.items() if self._check_query(document, query)]
        num_updated = len(keys_to_update)
        for k in keys_to_update:
            self.data[k] = new_document
        return {
            'matched': num_updated,
            'updated': num_updated,
        }

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
            query = {'id': query}
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
        data = copy.deepcopy(query)
        if 'id' in data:
            data['_id'] = data['id']
            del data['id']
        for field, value in copy.deepcopy(data).items():
            if re.search(r'^id\.', field): # TODO: check this
                data['_{}'.format(field)] = value
                del data[field]
            else:
                data[field] = value
        return data

    def update(self, query, update):
        def get_none_fields(document):
             none_fields = []
             for k, v in document.items():
                 if v is None:
                     none_fields.append(k)
                     continue
                 if isinstance(v, dict):
                     names = get_none_fields(v)
                     for name in names:
                         none_fields.append('{0}.{1}'.format(k, name))
             return none_fields

        query = self._prepare_query(query)
        updated_fields = self._prepare_query(update)
        unset_fields = {}
        for name in get_none_fields(updated_fields):
            unset_fields[name] = ''
        return self.connection.update(self.db, self.collection, query, updated_fields, unset_fields)

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
