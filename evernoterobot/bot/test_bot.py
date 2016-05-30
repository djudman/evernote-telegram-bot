from bot import get_commands, TelegramBot


def test_get_commands():
    command_list = get_commands()
    print(command_list)
    assert len(command_list) > 0


def test_create_bot_instance():
    TelegramBot('token', 'test_bot')


def test_cmd_help():
    pass


def test_cmd_notebook():
    pass


def test_handle_text():
    pass
