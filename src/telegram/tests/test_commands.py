import unittest
from telegram.models import TelegramUpdate


class TestModels(unittest.TestCase):
    def test_get_command(self):
        data = {
            'update_id': 729513057,
            'message': {
                'text': '/help',
                'from': {'is_bot': False, 'last_name': 'Dorofeev', 'username': 'djudman', 'id': 425606, 'first_name': 'Dmitrii', 'language_code': 'root'},
                'entities': [
                    {'offset': 0, 'type': 'bot_command', 'length': 5}
                ],
                'message_id': 198884,
                'chat': {'type': 'private', 'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitrii', 'username': 'djudman'},
                'date': 1529232597
            }
        }
        update = TelegramUpdate(data)
        self.assertEqual(update.get_command(), 'help')

        data = {
            'update_id': 729513058,
            'message': {
                'text': 'one /help',
                'from': {'is_bot': False, 'last_name': 'Dorofeev', 'username': 'djudman', 'id': 425606, 'first_name': 'Dmitrii', 'language_code': 'root'},
                'entities': [
                    {'offset': 4, 'type': 'bot_command', 'length': 5}
                ],
                'message_id': 198886,
                'chat': {'type': 'private', 'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitrii', 'username': 'djudman'},
                'date': 1529232615
            }
        }
        update = TelegramUpdate(data)
        self.assertIsNone(update.get_command())

        data = {
            'update_id': 729513060,
            'message': {
                'text': '/one /two /start /help',
                'from': {'is_bot': False, 'last_name': 'Dorofeev', 'username': 'djudman', 'id': 425606, 'first_name': 'Dmitrii', 'language_code': 'root'},
                'entities': [
                    {'offset': 0, 'type': 'bot_command', 'length': 4},
                    {'offset': 5, 'type': 'bot_command', 'length': 4},
                    {'offset': 10, 'type': 'bot_command', 'length': 6},
                    {'offset': 17, 'type': 'bot_command', 'length': 5}
                ],
                'message_id': 198890,
                'chat': {'type': 'private', 'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitrii', 'username': 'djudman'},
                'date': 1529232628
            }
        }
        update = TelegramUpdate(data)
        self.assertIsNone(update.get_command()) # because there are several entities
