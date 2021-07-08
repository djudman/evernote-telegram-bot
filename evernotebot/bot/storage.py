import json
import os
import sqlite3
import typing
from typing import Optional, Dict
from copy import deepcopy
from contextlib import suppress

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

from os.path import exists


class MongoStorageException(Exception):
    pass


class Mongo:
    def __init__(self, connection_string, *, collection=None, db_name=None):
        if collection is None:
            raise MongoStorageException('`collection` is required')
        self._driver = MongoClient(connection_string)
        with suppress(ConfigurationError):
            db = self._driver.get_database(db_name)
        if db is None:
            raise MongoStorageException(
                'You have to specify database name '
                'either in connection string or as `db_name` parameter')
        self._collection = db.get_collection(collection)

    def create(self, data: dict, auto_generate_id=False):
        data = deepcopy(data)
        if "id" in data:
            data["_id"] = data["id"]
            del data["id"]
        elif not auto_generate_id:
            raise MongoStorageException("`id` required")
        object_id = self._collection.insert_one(data).inserted_id
        if isinstance(object_id, ObjectId):
            object_id = str(object_id)
        return object_id

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
            object_id = str(self._collection.insert_one(data).inserted_id)
            if isinstance(object_id, ObjectId):
                object_id = str(object_id)
            data["id"] = object_id
        return object_id

    def delete(self, object_id, check_deleted_count=True):
        result = self._collection.delete_one({"_id": object_id})
        if check_deleted_count and result.deleted_count != 1:
            raise MongoStorageException(f"Object `{object_id}` not found")

    def close(self):
        self._driver.close()


class Sqlite:
    def __init__(self, dirpath: str, *, collection: str = None, db_name: str = None) -> None:
        if not exists(dirpath):
            os.makedirs(dirpath)
        db_filepath = f'{dirpath}/{db_name}'
        self._connection = sqlite3.connect(db_filepath)
        self._table_name = collection
        self.__execute_sql(
            f'CREATE TABLE IF NOT EXISTS {collection}'
            '(id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT)'
        )

    def __execute_sql(self, sql: str, *args) -> sqlite3.Cursor:
        sql = sql.strip().upper()
        cursor = self._connection.execute(sql, args)
        if not sql.startswith('SELECT'):
            self._connection.commit()
        return cursor

    def create(self, data: dict, auto_generate_id: bool = False) -> int:
        table = self._table_name
        if auto_generate_id:
            if 'id' in data:
                del data['id']
            sql = f'INSERT INTO {table}(data) VALUES(?)'
            cursor = self.__execute_sql(sql, json.dumps(data))
        else:
            object_id = data['id']
            if object_id <= 0:
                raise Exception(f'Invalid id `{object_id}`. Id must be >= 0')
            cursor = self.__execute_sql(f'INSERT INTO {table}(id, data) VALUES(?, ?)',
                                        object_id, json.dumps(data))
        return cursor.lastrowid

    def get(self, object_id: int, fail_if_not_exists: bool = False) -> Dict:
        query = object_id if isinstance(object_id, dict) else {'id': object_id}
        objects = self.get_all(query)
        result = list(objects)
        if fail_if_not_exists and not result:
            raise Exception(f'Object not found. Query: {query}')
        return result and result[0]

    def get_all(self, query: Optional[Dict] = None) -> typing.Generator:
        if query is None:
            query = {}
        table = self._table_name
        args = tuple()
        if 'id' in query:
            sql = f'SELECT id, data FROM {table} WHERE id=?'
            args = (query['id'],)
        else:
            sql = f'SELECT id, data FROM {table}'
        cursor = self.__execute_sql(sql, *args)
        objects = cursor.fetchall()
        if not objects:
            return tuple()
        for object_id, json_data in objects:
            data = json.loads(json_data)
            data['id'] = object_id
            if self._check_query(data, query):
                yield data

    def _check_query(self, document: dict, query: dict) -> bool:
        matched = True
        for k, query_value in query.items():
            key_value = document
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

    def save(self, data: dict) -> int:
        object_id = data['id']
        if not object_id:
            object_id = self.create(data, auto_generate_id=True)
        else:
            table = self._table_name
            sql = f'UPDATE {table} SET data=? WHERE id=?'
            cursor = self.__execute_sql(sql, json.dumps(data), object_id)
            if cursor.rowcount == 0:
                raise Exception(f'Object `{object_id}` not found')
        return object_id

    def delete(self, object_id: int, check_deleted_count: bool = True) -> None:
        table = self._table_name
        sql = f'DELETE FROM {table} WHERE id=?'
        cursor = self.__execute_sql(sql, object_id)
        if check_deleted_count and cursor.rowcount != 1:
            raise Exception(f'Object `{object_id}` not found')

    def close(self) -> None:
        try:
            self._connection.commit()
        except Exception:
            pass
        finally:
            self._connection.close()
