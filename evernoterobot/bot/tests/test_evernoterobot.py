import pytest
from bot import get_commands


def test_get_commands():
    commands = get_commands()
    assert len(commands) == 4
    names = [cmd.name for cmd in commands]
    assert 'help' in names
    assert 'start' in names
    assert 'notebook' in names
    assert 'switch_mode' in names
