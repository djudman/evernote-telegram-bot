import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import aiohttp

import settings
from bot import DownloadTask
from daemons.daemon import Daemon
from ext.telegram.api import BotApi


class DownloadError(Exception):
    def __init__(self, http_status, response_text, download_url):
        super(DownloadError, self).__init__()
        self.status = http_status
        self.response = response_text
        self.download_url = download_url

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "{0} - Response: {1}, {2}".format(self.download_url, self.status, self.response)

    def __repr__(self):
        return 'DownloadError({0}, "{1}", "{2}")'.format(self.status, self.response, self.download_url)


class TelegramDownloader:
    '''
    This class can take task from queue (in mongodb) and asynchronously \
    download file from Telegram servers to local directory.
    '''

    def __init__(self, download_dir=None, *, loop=None):
        self.logger = logging.getLogger('downloader')
        self._telegram_api = BotApi(settings.TELEGRAM['token'])
        self._loop = loop or asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self.tasks = []
        if download_dir is None:
            download_dir = '/tmp/'
            self.logger.warn('Download directory not specified. Uses "{0}"'.format(download_dir))
        self.download_dir = download_dir
        if not os.path.exists(self.download_dir):
            raise FileNotFoundError('Directory "{0}" not found'.format(self.download_dir))

    def run(self):
        self._loop.run_until_complete(self.async_run())
        self.logger.fatal('Downloader stopped')

    async def async_run(self):
        while True:
            try:
                tasks = self.download_all()
                if not tasks:
                    await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(e, exc_info=1)

    def write_file(self, path, data):
        try:
            with open(path, 'wb') as f:
                f.write(data)
            self.logger.debug('File {0} saved'.format(path))
        except Exception as e:
            self.logger.error(e, exc_info=1)

    async def get_download_url(self, file_id):
        return await self._telegram_api.getFile(file_id)

    async def download_file(self, url, destination_file):
        self.logger.debug('Start downloading {0}'.format(url))
        with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    await self._loop.run_in_executor(self._executor, self.write_file, destination_file, data)
                    return response
                else:
                    response_text = await response.text()
                    raise DownloadError(response.status, response_text, url)

    async def handle_download_task(self, task):
        try:
            file_id = task.file_id
            download_url = await self.get_download_url(file_id)
            destination_file = os.path.join(self.download_dir, file_id)
            response = await self.download_file(download_url, destination_file)
            task.mime_type = response.headers.get('CONTENT-TYPE', 'application/octet-stream')
            task.completed = True
            task.file = destination_file
            task.save()
        except DownloadError as e:
            self.logger.error(e)
        except Exception as e:
            self.logger.error(e, exc_info=1)

    def download_all(self):
        futures = []
        tasks = DownloadTask.get_sorted(100, condition={'in_progress': {'$exists': False}, 'completed': False})
        for task in tasks:
            entry = DownloadTask.find_and_modify(
                query={'_id': task._id, 'in_progress': {'$exists': False}},
                update={'$set': {'in_progress': True}})
            futures.append(asyncio.ensure_future(self.handle_download_task(DownloadTask(**entry))))
        return futures


class TelegramDownloaderDaemon(Daemon):

    def run(self):
        downloader = TelegramDownloader()
        downloader.run()
