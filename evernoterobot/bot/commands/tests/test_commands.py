import json

import pytest

from bot import User
from bot import get_commands, EvernoteBot
from bot.commands.help import HelpCommand
from bot.commands.notebook import NotebookCommand
from bot.commands.start import StartCommand
from bot.commands.switch_mode import SwitchModeCommand
from bot.model import StartSession
from ext.telegram.models import Message, TelegramUpdate
from ext.telegram.conftest import text_update


@pytest.mark.async_test
async def test_help_command(testbot: EvernoteBot, text_update: str):
    update = TelegramUpdate(json.loads(text_update))
    help_cmd = HelpCommand(testbot)
    user = User.create(user_id=1, telegram_chat_id=update.message.chat.id)
    await help_cmd.execute(update.message)

    assert testbot.api.sendMessage.call_count == 1
    args = testbot.api.sendMessage.call_args[0]
    assert len(args) == 2
    assert args[0] == user.telegram_chat_id
    assert 'This is bot for Evernote' in args[1]


@pytest.mark.async_test
async def test_notebook_command(testbot: EvernoteBot, text_update: str):
    update = TelegramUpdate(json.loads(text_update))
    notebook_cmd = NotebookCommand(testbot)
    user = User.create(id=update.message.user.id,
                       telegram_chat_id=update.message.chat.id,
                       evernote_access_token='',
                       current_notebook={ 'guid': 1 })
    await notebook_cmd.execute(update.message)

    user = User.get({'id': user.id})
    assert user.state == 'select_notebook'
    assert testbot.api.sendMessage.call_count == 1
    assert testbot.update_notebooks_cache.call_count == 1


@pytest.mark.async_test
async def test_start_command(testbot: EvernoteBot, text_update: str):
    update = TelegramUpdate(json.loads(text_update))
    User.get({'id': update.message.user.id}).delete()
    start_cmd = StartCommand(testbot)
    await start_cmd.execute(update.message)
    sessions = StartSession.find()
    assert len(sessions) == 1
    assert sessions[0].user_id == update.message.user.id
    assert sessions[0].oauth_data['oauth_url'] == 'test_oauth_url'
    new_user = User.get({'id': update.message.user.id})
    assert new_user.telegram_chat_id == update.message.chat.id
    # TODO:
    # assert new_user.username == 'testuser'
    # assert new_user.first_name == 'test_first'
    # assert new_user.last_name == 'test_last'
    assert new_user.mode == 'one_note'
    assert testbot.api.sendMessage.call_count == 1
    args = testbot.api.sendMessage.call_args[0]
    assert len(args) == 3
    assert args[0] == new_user.telegram_chat_id
    assert 'Welcome' in args[1]
    assert testbot.api.editMessageReplyMarkup.call_count == 1


@pytest.mark.async_test
async def test_switch_mode_command(testbot: EvernoteBot, text_update: str):
    update = TelegramUpdate(json.loads(text_update))
    switch_mode_cmd = SwitchModeCommand(testbot)
    user = User.create(id=update.message.user.id,
                       telegram_chat_id=update.message.chat.id,
                       mode='one_note')
    await switch_mode_cmd.execute(update.message)
    user = User.get({'id': user.id})
    assert user.state == 'switch_mode'
    assert testbot.api.sendMessage.call_count == 1
    args = testbot.api.sendMessage.call_args[0]
    kwargs = testbot.api.sendMessage.call_args[1]
    assert len(args) == 2
    assert args[0] == user.telegram_chat_id
    assert 'Please, select mode' == args[1]
    assert 'reply_markup' in kwargs
