from pymongo import MongoClient


class MongoException(Exception):
    pass


class Mongo:
    def __init__(self, connection_string, db=None, collection=None):
        self._driver = MongoClient(connection_string)
        self._db = getattr(self._driver, db)
        self._collection = getattr(self._db, collection)

    def get(self, object_id):
        query = {'_id': object_id}
        obj = self._collection.find_one(query)
        if obj is None:
            raise MongoException(f"Object `{object_id}` not found")
        return obj

    def get_all(self, query):
        return self._collection.find(query)

    def save(self, data: dict):
        object_id = data.get('id')
        if object_id:
            del data['id']
            query = {'_id': object_id}
            result = self._collection.update_one(query, data)
            if result.modified_count != 1:
                raise MongoException(f"Object `{object_id}` not found")
        else:
            object_id = self._collection.insert_one(data).inserted_id
            data['id'] = object_id
        return object_id
