import unittest
from unittest.mock import Mock

from utelegram import Message, User

from evernotebot.bot.core import EvernoteBot
from evernotebot.bot.commands import switch_notebook_command, help_command
from util.config import bot_config


class TestCommands(unittest.TestCase):
    def test_switch_notebook(self):
        message = Message(message_id=1, date=1, from_user={
            "id": 2, "is_bot": False, "first_name": "John"
        })
        bot = EvernoteBot(bot_config)
        user_data = {
            "id": 2,
            "created": 123,
            "last_request_ts": 123,
            "bot_mode": "multiple_notes",
            "telegram": {
                "first_name": "Bob",
                "last_name": None,
                "username": None,
                "chat_id": 1,
            },
            "evernote": {
                "access": {"token": "access_token", "permission": "basic"},
                "notebook": {"name": "xxx", "guid": "xxx"}
            },
        }
        bot.users = Mock()
        bot.users.get = Mock(return_value=user_data)
        bot.evernote = Mock()
        bot.evernote().get_all_notebooks = Mock(return_value=[{"name": "xxx", "guid": "xxx"}])
        bot.api = Mock()
        bot.api.sendMessage = Mock()
        bot.users.save = Mock()
        switch_notebook_command(bot, message)
        bot.users.get.assert_called_once_with(2)
        bot.evernote().get_all_notebooks.assert_called_once()
        bot.api.sendMessage.assert_called_once_with(1, "Please, select notebook",
            '{"keyboard": [[{"text": "> xxx <"}]], "resize_keyboard": true, "one_time_keyboard": true}')
        bot.users.save.assert_called_once()
        save_data = bot.users.save.call_args[0][0]
        self.assertEqual(save_data["state"], "switch_notebook")

    def test_help(self):
        bot = EvernoteBot(bot_config)
        bot.api = Mock()
        bot.api.sendMessage = Mock()
        message = Message(message_id=1, date=1, chat={"id": 1, "type": "private"})
        help_command(bot, message)
        bot.api.sendMessage.assert_called_once()
