import asyncio
import logging
import logging.config
import os
import random
import shutil
import string
from os.path import dirname, join, realpath, exists

import pytest

import settings
from bot.downloader import TelegramDownloader
from bot.model import DownloadTask

tmp_dir = join(realpath(dirname(__file__)), 'tmp')
download_dir = join(tmp_dir, "".join([random.choice(string.ascii_letters) for i in range(10)]))


def setup_module(module):
    logging.config.dictConfig(settings.LOG_SETTINGS)
    if not exists(download_dir):
        os.makedirs(download_dir)


def teardown_module(module):
    shutil.rmtree(tmp_dir)


# @pytest.mark.skip(reason='Broken')
@pytest.mark.async_test
async def test_download_file():

    def get_file_id():
        return "".join([random.choice(string.ascii_letters) for i in range(10)])

    def get_file_id1():
        return 'robots'

    def get_file_id2():
        return 'rpm'

    task = DownloadTask.create(file_id=get_file_id2(), completed=False)
    task2 = DownloadTask.create(file_id=get_file_id1(), completed=False)
    downloader = TelegramDownloader(download_dir)

    async def url(file_id):
        if file_id == 'robots':
            return 'http://yandex.ru/robots.txt'
        else:
            return 'http://mirror.yandex.ru/altlinux/4.0/Desktop/4.0.0/files/i586/GConf-2.16.1-alt1.i586.rpm'

    downloader.get_download_url = url
    futures = downloader.download_all()
    await asyncio.wait(futures)
    task.delete()
    task2.delete()