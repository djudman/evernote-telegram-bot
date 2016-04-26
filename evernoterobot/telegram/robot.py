from os.path import realpath, dirname, join
import logging
import asyncio
import traceback

from user import User


class EvernoteRobot:

    def __init__(self, telegram, evernote, db_client):
        self.bot_url = 'https://telegram.me/evernoterobot'
        self.telegram = telegram
        self.evernote = evernote
        self.db = db_client
        self.logger = logging.getLogger()
        self.commands = self.collect_commands(
                join(realpath(dirname(__file__)), 'commands')
            )

    def collect_commands(self, dir_path):
        # TODO:
        from .commands.help import help
        from .commands.start import start
        return {
            'start': start,
            'help': help,
        }

    async def handle_update(self, data):
        if 'message' in data:
            await self.handle_message(data['message'])
        elif 'inline_query' in data:
            # TODO: process inline query
            pass
        elif 'chosen_inline_result' in data:
            # TODO: process inline result
            pass
        elif 'callback_query' in data:
            # TODO: process callback query
            pass
        else:
            # TODO: unsupported update
            pass

    async def handle_message(self, message):
        self.chat_id = message['chat']['id']
        if message.get('from'):
            self.user = User(message.get('from'))

        commands = []
        for entity in message.get('entities', []):
            if entity['type'] == 'bot_command':
                offset = entity['offset']
                length = entity['length']
                cmd = message.get('text', '')[offset:length]
                if cmd.startswith('/'):
                    cmd = cmd.replace('/', '')
                commands.append(cmd)

        if commands:
            for cmd in commands:
                await self.execute_command(cmd)
        else:
            # TODO: just for fun
            text = message.get('text', '')
            await self.api.sendMessage(self.chat_id, text)

    async def execute_command(self, cmd_name):
        try:
            callable_func = self.commands.get(cmd_name)
            if callable_func:
                if asyncio.iscoroutinefunction(callable_func):
                    await callable_func()
                else:
                    callable_func()
            else:
                text = "WTF? I don't know this words: '%s'" % cmd_name
                await self.telegram.sendMessage(self.chat_id, text)
                # TODO: send list available commands
                # help_cmd = self.commands['help']
                # await help_cmd(self.chat_id, self.telegram)
                self.logger.error("Unsupported command '%s'" % cmd_name)
        except Exception:
            text = "Houston, we have a problem. Please try again later"
            await self.telegram.sendMessage(self.chat_id, text)
            self.logger.error(traceback.format_exc())
