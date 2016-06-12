from unittest.mock import Mock

import asyncio
from telegram.bot import TelegramBot, TelegramBotCommand


def test_create_bot_instance():
    bot = TelegramBot('token', 'test_bot')
    assert bot.api
    assert bot.logger
    assert bot.url == 'https://telegram.me/test_bot'
    assert bot.name == 'test_bot'
    assert not list(bot.commands)


def test_add_bot_command():

    class CmdFoo(TelegramBotCommand):
        name = 'foo'

    bot = TelegramBot('token', 'bot_name')
    bot.add_command(CmdFoo)
    commands = list(bot.commands)
    assert len(commands) == 1
    assert commands[0] == 'foo'


def test_execute_bot_command():
    mock = Mock()

    class TestHelpCommand(TelegramBotCommand):
        name = 'help'

        async def execute(self, message):
            mock()

    bot = TelegramBot('token', 'bot_name')
    bot.add_command(TestHelpCommand)
    update = {
        'message': {
            'text': '/help',
            'message_id': 2666,
            'date': 1465764948,
            'chat': {
                'id': 425606,
                'username': 'djudman',
                'last_name': 'Dorofeev',
                'type': 'private',
                'first_name': 'Dmitry'
            },
            'entities': [
                {
                    'offset': 0,
                    'length': 5,
                    'type': 'bot_command'
                }
            ],
            'from': {
                'id': 425606,
                'username': 'djudman',
                'last_name': 'Dorofeev',
                'first_name': 'Dmitry'
            }
        },
        'update_id': 84506398
    }
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.handle_update(update))
    mock.assert_called_once_with()
