import asyncio

from bot import get_commands, TelegramBot, EvernoteBot


def test_get_commands():
    command_list = get_commands()
    assert len(command_list) > 0


def test_create_bot_instance():
    TelegramBot('token', 'test_bot')


def test_cmd_help():
    update = {'message': {'text': '/help', 'message_id': 2656, 'date': 1465333910, 'chat': {'id': 425606, 'username': 'djudman', 'last_name': 'Dorofeev', 'type': 'private', 'first_name': 'Dmitry'}, 'entities': [{'offset': 0, 'length': 5, 'type': 'bot_command'}], 'from': {'id': 425606, 'username': 'djudman', 'last_name': 'Dorofeev', 'first_name': 'Dmitry'}}, 'update_id': 84506393}
    bot = EvernoteBot('evernote_token', 'evernoterobot')
    loop = asyncio.get_event_loop()
    task = loop.create_task(bot.handle_update(update))
    result = loop.run_until_complete(task)
    print(result)


def test_cmd_notebook():
    pass


def test_handle_text():
    update = {
        'message': {
            'chat': {
                'id': 425606,
                'username': 'djudman',
                'last_name': 'Dorofeev',
                'type': 'private',
                'first_name': 'Dmitry'
            },
            'text': 'plain text',
            'from': {
                'id': 425606,
                'username': 'djudman',
                'last_name': 'Dorofeev',
                'first_name': 'Dmitry'
            },
            'date': 1465332956,
            'message_id': 2654
        },
        'update_id': 84506392
    }
    bot = EvernoteBot('evernote_token', 'evernoterobot')
    loop = asyncio.get_event_loop()
    task = loop.create_task(bot.handle_update(update))
    result = loop.run_until_complete(task)
    print(result)
