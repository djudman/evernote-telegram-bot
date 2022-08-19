import asyncio
from pathlib import Path

import pytest

from evernotebot.bot import EvernoteBot
from ..conftest import telegram_update_data
from ..mocks.telegram import BotApiMock


@pytest.fixture
def start_command():
    data = telegram_update_data('start')
    assert data
    return data


def test_start_command(bot: EvernoteBot, start_command: dict):
    responses_filepath = Path(__file__).parent.joinpath('bot_api_responses.json').resolve()
    bot.api = BotApiMock(responses_filepath)
    asyncio.run(bot.process_update(start_command))
