import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient

import settings
from bot import DownloadTask
from telegram.api import BotApi


class TelegramDownloader:
    '''
    This class can take task from queue (in mongodb) and asynchronously \
    download file from Telegram servers to local directory.
    '''

    def __init__(self, download_dir=None, *, loop=None):
        self._db_client = AsyncIOMotorClient(settings.MONGODB_URI)
        self._db = self._db_client.get_default_database()
        self._telegram_api = BotApi(settings.TELEGRAM['token'])
        self._loop = loop or asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self.download_dir = download_dir or '/tmp/'
        if not os.path.exists(download_dir):
            raise FileNotFoundError('Directory {0} not found'.format(self.download_dir))

    def run(self):
        asyncio.ensure_future(self.download_all(), loop=self._loop)
        self._loop.run_forever()

    def write_file(self, task, path, data):
        with open(path, 'wb') as f:
            f.write(data)
        task.completed = True
        task.file = path

    async def download_all(self):
        try:
            last_created = None
            for task in await DownloadTask.get_sorted(100, condition={ '$gt': { 'created': last_created } }):
                download_url = await self._telegram_api.getFile(task['file_id'])
                with aiohttp.ClientSession() as session:
                    async with session.get(download_url) as response:
                        if response.status == 200:
                            data = await response.read()
                            file_name = task['file_id']
                            asyncio.ensure_future(
                                self._loop.run_in_executor(
                                    self._executor, self.write_file,
                                    task,
                                    os.path.join(self.download_dir, file_name),
                                    data),
                                loop=self._loop
                            )
                        else:
                            pass
                last_created = task.created
        except Exception:
            pass
