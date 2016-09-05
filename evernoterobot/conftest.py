import sys
from os.path import dirname, realpath
import contextlib
import asyncio
import gc
import logging.config
from unittest.mock import Mock
import pytest
from pymongo import MongoClient

from bot import EvernoteBot
from bot.model import Model

sys.path.insert(0, realpath(dirname(__file__)))

import settings

logging.config.dictConfig(settings.LOG_SETTINGS)


def setup_test_loop():
    """create and return an asyncio.BaseEventLoop
    instance. The caller should also call teardown_test_loop,
    once they are done with the loop.
    """
    loop = asyncio.get_event_loop()
    # asyncio.set_event_loop(None)
    return loop


# def teardown_test_loop(loop):
#     """teardown and cleanup an event_loop created
#     by setup_test_loop.
#     :param loop: the loop to teardown
#     :type loop: asyncio.BaseEventLoop
#     """
#     is_closed = getattr(loop, 'is_closed')
#     if is_closed is not None:
#         closed = is_closed()
#     else:
#         closed = loop._closed
#     if not closed:
#         loop.call_soon(loop.stop)
#         loop.run_forever()
#         loop.close()
#     gc.collect()
    # asyncio.set_event_loop(None)


@contextlib.contextmanager
def loop_context():
    """a contextmanager that creates an event_loop, for test purposes.
    handles the creation and cleanup of a test loop.
    """
    loop = setup_test_loop()
    yield loop
    # teardown_test_loop(loop)


@pytest.yield_fixture
def loop():
    with loop_context() as loop:
        yield loop


def pytest_runtest_setup(item):
    if 'async_test' in item.keywords and 'loop' not in item.fixturenames:
        # inject an event loop fixture for all async tests
        item.fixturenames.append('loop')



@pytest.mark.tryfirst
def pytest_pyfunc_call(pyfuncitem):
    """
    Run asyncio marked test functions in an event loop instead of a normal
    function call.
    """
    if 'use_mongo' in pyfuncitem.keywords:
        settings.STORAGE = {
            'class': 'bot.storage.MongoStorage',
            'host': 'localhost',
            'port': 27017,
            'db': 'test',
        }
    if 'async_test' in pyfuncitem.keywords:
        funcargs = pyfuncitem.funcargs
        loop = funcargs['loop']
        testargs = {arg: funcargs[arg]
                    for arg in pyfuncitem._fixtureinfo.argnames}
        loop.run_until_complete(pyfuncitem.obj(**testargs))
        return True


@pytest.mark.tryfirst
def pytest_pycollect_makeitem(collector, name, obj):
    if collector.funcnamefilter(name):
        if not callable(obj):
            return
        item = pytest.Function(name, parent=collector)
        if 'async_test' in item.keywords:
            return list(collector._genfunctions(name, obj))


class AsyncMock(Mock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@pytest.fixture
def testbot():
    bot = EvernoteBot(settings.TELEGRAM['token'], 'test_bot')
    bot.api = AsyncMock()
    bot.api.sendMessage = AsyncMock(return_value={'message_id': 1})
    bot.evernote = AsyncMock()
    bot.evernote.get_oauth_data = Mock(return_value={'oauth_url': 'test_oauth_url'})
    bot.evernote.list_notebooks = Mock(
        return_value=[Model(guid='1', name='test_notebook')]
    )
    bot.cache.get = AsyncMock(return_value=None)
    bot.cache.set = AsyncMock()
    bot.update_notebooks_cache = AsyncMock()
    return bot
