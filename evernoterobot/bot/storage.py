import uuid
from abc import abstractmethod
from numbers import Number
from typing import List, Tuple

from pymongo import MongoClient
from pymongo.collection import Collection

from bot.model import Model
from bot.util import dict_get, dict_set


class Storage:

    def __init__(self, config, **kwargs):
        self.config = config
        self.collection = kwargs['collection']

    @abstractmethod
    def get(self, query: dict):
        '''
        Args:
            query:

        Returns: one model object that matched query
        '''
        pass

    @abstractmethod
    def save(self, model: Model):
        pass

    @abstractmethod
    def update(self, query: dict, new_values: dict):
        '''

        Args:
            query:
            new_values: float dict. For nested fields use dots, example: 'field1.field2.field3'
        '''
        pass

    @abstractmethod
    def delete(self, model: Model):
        pass

    @abstractmethod
    def find(self, query: dict, sort: List[Tuple]):
        pass


class MemoryStorage(Storage):

    def __init__(self, config, **kwargs):
        super().__init__(config, **kwargs)
        self._items = {}

    def _check_query(self, entry: dict, query: dict):
        matched = True
        for k, query_value in query.items():
            if k[0] == '$':
                matched = self._check_operator(k, query_value, entry)
            else:
                key_path = k.split('.')
                key_value = dict_get(entry, key_path)
                if isinstance(query_value, dict):
                    matched = self._check_query(key_value, query_value)
                elif isinstance(key_value, Number) and isinstance(query_value, Number):
                    matched = abs(key_value - query_value) < 0.00000001
                else:
                    matched = key_value == query_value
            if not matched:
                return False
        return matched

    def _check_operator(self, operator, query_value, entry):
        if operator == '$exists':
            return (entry is not None) == query_value
        raise Exception('Unsupported operator {0}'.format(operator))

    def get(self, query: dict):
        for k, obj in self._items.get(self.collection, {}).items():
            if self._check_query(obj, query):
                return obj

    def find(self, query: dict, sort: List[Tuple]):
        objects = []
        for k, obj in self._items.get(self.collection, {}).items():
            if self._check_query(obj, query):
                objects.append(obj)
        sorted(objects, key=lambda x: [x[k] for k, direction in sort])
        return objects

    def save(self, model: Model):
        if not model.id:
            model.id = str(uuid.uuid4())
        classname = self.collection
        if classname not in self._items:
            self._items[classname] = {}
        self._items[classname][model.id] = model.save_data()

    def update(self, query: dict, new_values: dict):
        for k, obj in self._items.get(self.collection, {}).items():
            if self._check_query(obj, query):
                for k, v in new_values.items():
                    path = k.split('.')
                    dict_set(obj, v, path)
                    return obj

    def delete(self, model: Model):
        classname = self.collection
        del self._items[classname][model.id]
        if not self._items[classname]:
            del self._items[classname]


class MongoStorage(Storage):

    def __init__(self, config: dict, **kwargs):
        super().__init__(config, **kwargs)

    def __get_collection(self) -> Collection:
        if not self.__collection:
            uri = 'mongodb://{0}:{1}/{2}'.format(self.config['host'],
                                                 self.config['port'],
                                                 self.config['db'])
            client = MongoClient(uri)
            self.__collection = client[self.collection]
        return self.__collection

    def __prepare_query(self, query: dict):
        if not query:
            return {}
        valid_query = {}
        for k, v in query.items():
            if k == 'id':
                valid_query['_id'] = v
            else:
                valid_query[k] = v
        return valid_query

    def get(self, query: dict):
        collection = self.__get_collection()
        return collection.find_one(self.__prepare_query(query))

    def find(self, query: dict, sort: List[Tuple]):
        collection = self.__get_collection()
        cursor = collection.find(self.__prepare_query(query), sort=sort)
        return cursor

    def save(self, model: Model):
        data = model.save_data()
        if 'id' in data:
            data['_id'] = data['id']
            del data['id']
        collection = self.__get_collection()
        collection.save(data)

    def update(self, query: dict, new_values: dict):
        collection = self.__get_collection()
        return collection.find_and_modify(self.__prepare_query(query), {'$set': new_values})

    def delete(self, model: Model):
        collection = self.__get_collection()
        collection.remove(model.id)