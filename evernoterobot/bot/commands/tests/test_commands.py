import pytest

from bot import User
from bot import get_commands, EvernoteBot
from bot.commands.help import HelpCommand


def test_get_commands():
    commands = get_commands()
    assert len(commands) == 4
    names = [cmd.name for cmd in commands]
    assert 'help' in names
    assert 'start' in names
    assert 'notebook' in names
    assert 'switch_mode' in names


@pytest.mark.async_test
async def test_help_command(testbot: EvernoteBot):
    help_cmd = HelpCommand(testbot)
    user = User.create(user_id=1, telegram_chat_id=2)
    await help_cmd.execute(user, None)

    assert testbot.api.sendMessage.call_count == 1
    args = testbot.api.sendMessage.call_args[0]
    assert len(args) == 2
    assert args[0] == user.telegram_chat_id
    assert 'This is bot for Evernote' in args[1]