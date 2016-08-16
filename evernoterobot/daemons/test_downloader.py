import asyncio
import os
from os.path import dirname, join, realpath, exists
import shutil
import string
import random
import logging
import logging.config
import pytest
from daemons.downloader import TelegramDownloader
from bot.model import DownloadTask
import settings


tmp_dir = join(realpath(dirname(__file__)), 'tmp')
download_dir = join(tmp_dir, "".join([random.choice(string.ascii_letters) for i in range(10)]))


def setup_module(module):
    logging.config.dictConfig(settings.LOG_SETTINGS)
    if not exists(download_dir):
        os.makedirs(download_dir)


def teardown_module(module):
    shutil.rmtree(tmp_dir)


@pytest.mark.skip(reason='Broken')
@pytest.mark.async_test
async def test_download_file():

    def get_file_id():
        return "".join([random.choice(string.ascii_letters) for i in range(10)])

    task = await DownloadTask.create(file_id=get_file_id(), completed=False)
    task2 = await DownloadTask.create(file_id=get_file_id(), completed=False)
    downloader = TelegramDownloader(download_dir)

    async def url(file_id):
        return 'http://yandex.ru/robots.txt'

    downloader.get_download_url = url
    futures = await downloader.download_all()
    await asyncio.wait(futures)
    await task.delete()
    await task2.delete()