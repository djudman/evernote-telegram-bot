import logging
from .api import BotApi


class EvernoteRobot:

    def __init__(self, token):
        self.api = BotApi(token)
        self.logger = logging.getLogger()

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
                text = self.execute_command(cmd)
                await self.api.sendMessage(self.chat_id, text)
        else:
            text = message.get('text', '')
            await self.api.sendMessage(self.chat_id, text)

    def execute_command(self, cmd):
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            text = func(self)
        else:
            text = "Unsupported command '%s'" % cmd
            self.logger.warning(text)
        return text

    def start(self):
        return '''Hi! I'm robot for __fast__ saving your notes to Evernote.
First of all you should link your Evernote account with me.'''

    def help(self):
        return '''
What is it?
- Bot for fast saving notes to Evernote
Contacts
- djudman@gmail.com'''
