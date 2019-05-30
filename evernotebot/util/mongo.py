from bson.objectid import ObjectId
from pymongo import MongoClient


class MongoConnection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.client = MongoClient(connection_string)
        self._lock = False

    def generate_id(self):
        if self._lock:
            raise Exception('Deadlock')
        self._lock = True
        object_id = str(ObjectId())
        self._lock = False
        return object_id

    def insert(self, db, collection, document):
        result = self.client[db][collection].insert_one(document)
        return result.inserted_id

    def update(self, db, collection, query, updated_fields, unset_fields):
        update = {'$set': updated_fields}
        if unset_fields:
            update['$unset'] = unset_fields
        result = self.client[db][collection].update_many(query, update)
        return {
            'matched': result.matched_count,
            'modified': result.modified_count,
        }

    def count(self, db, collection, query):
        return self.client[db][collection].count_documents(query)

    def delete(self, db, collection, query):
        result = self.client[db][collection].delete_many(query)
        return result.deleted_count

    def find_one(self, db, collection, query):
        return self.client[db][collection].find_one(query)

    def find_many(self, db, collection, query, *, skip=0, limit=0, sort=None):
        return self.client[db][collection].find(query)

    def exec_command(self, db, command_name, *args, **kwargs):
        return self.client[db].command(command_name, *args, **kwargs)
