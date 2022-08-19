import copy
import importlib
from typing import Dict, Generator, Optional

import evernotebot.storage.providers as providers

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


class Storage:
    def __init__(self, name: str, config: dict):
        provider_classpath = config['provider']
        module_name, class_name = provider_classpath.rsplit('.', 1)
        module = importlib.import_module(module_name)
        provider_class = getattr(module, class_name)
        config_copy = copy.deepcopy(config)
        del config_copy['provider']
        config_copy['collection'] = name
        self.provider = provider_class(**config_copy)

    def create(self, data: dict):
        if 'id' in data:
            return self.provider.create(data)
        return self.provider.create(data, auto_generate_id=True)

    def get(self, object_id: int, fail_if_not_exists: bool = False) -> Dict:
        return self.provider.get(object_id, fail_if_not_exists)

    def get_all(self, query: Optional[Dict] = None) -> Generator:
        return self.provider.get_all(query)

    def save(self, data: dict):
        return self.provider.save(data)

    def delete(self, object_id: int, check_deleted_count: bool = True):
        return self.provider.delete(object_id, check_deleted_count)

    def close(self):
        return self.provider.close()


class SqliteStorage:
    def __init__(self, config: dict) -> None:
        dirpath = config['dirpath']
        db_name = config['db_name']
        self.filepath = f'{dirpath}/{db_name}.sqlite'
        self.engine = create_async_engine(f'sqlite+aiosqlite:///{self.filepath}', future=True)

    async def save(self, models):
        async_session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        async with async_session() as session:
            async with session.begin():
                session.add_all(models)
                await session.commit()

    async def get(self, model_class, pk: int):
        async_session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        async with async_session() as session:
            async with session.begin():
                stmt = select(model_class).where(model_class.id == pk)
                result = await session.execute(stmt)
                return result.scalars().first()
