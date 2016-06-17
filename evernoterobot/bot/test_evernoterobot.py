from bot import get_commands


def test_get_commands():
    commands = get_commands()
    assert len(commands) == 2
    names = [cmd.name for cmd in commands]
    assert 'help' in names
    assert 'start' in names
