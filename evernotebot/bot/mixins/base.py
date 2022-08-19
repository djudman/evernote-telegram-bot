import os
from os.path import exists

from evernotebot.storage import SqliteStorage
from evernotebot.storage.models import Base


class BaseMixin:
    def __init__(self, config: dict):
        self.config = config
        bot_name = config['telegram']['bot_name']
        self.url = f'https://t.me/{bot_name}'
        self.name = bot_name
        self.storage = SqliteStorage(config['storage'])

    async def init_storage(self):
        filepath = self.storage.filepath
        if exists(filepath):
            os.unlink(filepath)
        engine = self.storage.engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def exec_all_mixins(self, callback_name: str, *args):
        for _class in self.__class__.__bases__:
            if not hasattr(_class, callback_name):
                continue
            method = getattr(_class, callback_name)
            out = await method(self, *args)
            if out is False:
                break
