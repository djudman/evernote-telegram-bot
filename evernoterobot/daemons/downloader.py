import asyncio
import logging
import os
import traceback
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient

import settings
from bot import DownloadTask
from ext.telegram.api import BotApi


class DownloadError(Exception):
    def __init__(self, http_status, response_text, download_url):
        super(DownloadError, self).__init__()
        self.status = http_status
        self.response = response_text
        self.url = download_url


class TelegramDownloader:
    '''
    This class can take task from queue (in mongodb) and asynchronously \
    download file from Telegram servers to local directory.
    '''

    def __init__(self, download_dir=None, *, loop=None):
        self.logger = logging.getLogger('downloader')
        self._db_client = AsyncIOMotorClient(settings.MONGODB_URI)
        self._db = self._db_client.get_default_database()
        self._telegram_api = BotApi(settings.TELEGRAM['token'])
        self._loop = loop or asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self.tasks = []
        if download_dir is None:
            download_dir = '/tmp/'
            self.logger.warn('Download directory not specified. Uses "{0}"'
                             .format(download_dir))
        self.download_dir = download_dir
        if not os.path.exists(self.download_dir):
            raise FileNotFoundError('Directory "{0}" not found'
                                    .format(self.download_dir))

    def run(self):
        in_progress_tasks = []
        while True:
            futures = self._loop.run_until_complete(asyncio.ensure_future(self.download_all()))
            in_progress_tasks.extend(futures)
            in_progress_tasks = filter(lambda t: not t.completed, in_progress_tasks)

    def write_file(self, path, data):
        with open(path, 'wb') as f:
            f.write(data)
        self.logger.debug('File {0} saved'.format(path))

    async def get_download_url(self, file_id):
        return await self._telegram_api.getFile(file_id)

    async def download_file(self, url, destination_file):
        self.logger.debug('Start downloading {0}'.format(url))
        with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    return self._loop.run_in_executor(
                        self._executor, self.write_file,
                        destination_file, data),
                else:
                    response_text = await response.text()
                    raise DownloadError(response.status, response_text, url)

    async def handle_download_task(self, task):
        task.in_progress = True
        await task.save()
        file_id = task.file_id
        download_url = await self.get_download_url(file_id)
        destination_file = os.path.join(self.download_dir, file_id)
        await self.download_file(download_url, destination_file)
        task.completed = True
        task.file = destination_file
        await task.save()

    async def download_all(self):
        try:
            tasks = await DownloadTask.get_sorted(100, condition={'in_progress': {'$exists': False}})
            return [asyncio.ensure_future(self.handle_download_task(task)) for task in tasks]
        except DownloadError as e:
            self.logger.error('Downloading {0} failed. HTTP status = {1}, response: {2}'.format(e.url, e.status, e.response))
        except Exception as e:
            self.logger.error(traceback.format_exc())
