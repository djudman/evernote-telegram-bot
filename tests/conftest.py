import asyncio
import json
from pathlib import Path

import pytest

from evernotebot.bot import EvernoteBot
from evernotebot.config import load_config


def telegram_update_data(name: str):
    filepath = Path(__file__).parent.joinpath(f'{name}/telegram_update.json').resolve()
    with open(filepath) as f:
        return json.load(f)


@pytest.fixture
def bot():
    config = load_config()
    config['storage']['db_name'] = 'test_evernotebot'
    bot = EvernoteBot(config)
    asyncio.run(bot.init_storage())
    return bot
