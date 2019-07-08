from copy import deepcopy
from contextlib import suppress

from pymongo import MongoClient
from pymongo.errors import ConfigurationError


class MongoStorageException(Exception):
    pass


class Mongo:
    def __init__(self, connection_string, *, collection=None, db_name=None):
        if collection is None:
            raise MongoStorageException("`collection` is required")
        self._driver = MongoClient(connection_string)
        db = None
        with suppress(ConfigurationError):
            db = self._driver.get_database(db_name)
        if db is None:
            raise MongoStorageException(
                "You have to specify database name "
                "either in connection string or as `db_name` parameter")
        self._collection = db.get_collection(collection)

    def create(self, data: dict):
        if "id" not in data:
            raise MongoStorageException("`id` required")
        data = deepcopy(data)
        data["_id"] = data["id"]
        del data["id"]
        return self._collection.insert_one(data).inserted_id

    def get(self, object_id, fail_if_not_exists=False):
        query = object_id if isinstance(object_id, dict) else {"_id": object_id}
        data = self._collection.find_one(query)
        if fail_if_not_exists and not data:
            raise MongoStorageException(f"Object not found. Query: {query}")
        if data:
            data["id"] = data["_id"]
            del data["_id"]
            return data

    def get_all(self, query):
        for document in self._collection.find(query):
            document["id"] = document["_id"]
            del document["_id"]
            yield document

    def save(self, data: dict):
        object_id = data.get("id")
        if object_id:
            data["_id"] = object_id
            del data["id"]
            query = {"_id": object_id}
            result = self._collection.update_one(query, {"$set": data})
            if result.matched_count == 0:
                raise MongoStorageException(f"Object `{object_id}` not found")
            data["id"] = object_id
        else:
            object_id = self._collection.insert_one(data).inserted_id
            data["id"] = object_id
        return object_id

    def delete(self, object_id, check_deleted_count=True):
        result = self._collection.delete_one({"_id": object_id})
        if check_deleted_count and result.deleted_count != 1:
            raise MongoStorageException(f"Object `{object_id}` not found")
