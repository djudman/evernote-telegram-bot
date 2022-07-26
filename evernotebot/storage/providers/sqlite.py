import json
import os
import sqlite3
import typing
from typing import Optional, Dict
from os.path import exists

from evernotebot.storage.providers import BaseProvider


class Sqlite(BaseProvider):
    def __init__(self, dirpath: str, *, collection: str = None, db_name: str = None) -> None:
        if not exists(dirpath):
            os.makedirs(dirpath)
        self.db_filepath = f'{dirpath}/{db_name}.sqlite'
        self._table_name = collection
        self._connection = None

    def _connect(self):
        self._connection = sqlite3.connect(self.db_filepath)
        self.__execute_sql(
            f'CREATE TABLE IF NOT EXISTS {self._table_name}'
            '(id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT)'
        )

    @property
    def connection(self):
        if not self._connection:
            self._connect()
        return self._connection

    def __execute_sql(self, sql: str, *args) -> sqlite3.Cursor:
        sql = sql.strip().upper()
        cursor = self.connection.execute(sql, args)
        if not sql.startswith('SELECT'):
            self.connection.commit()
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
            self.connection.commit()
        except Exception:
            pass
        finally:
            self.connection.close()
