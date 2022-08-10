import logging
import traceback
from time import time
from typing import Optional

from evernotebot.bot.errors import EvernoteBotException
from evernotebot.bot.mixins import (
    HelpCommandMixin,
    MessageHandlerMixin,
    StartCommandMixin,
    SwitchModeCommand,
    SwitchNotebookCommand
)
from evernotebot.storage import Storage


def parse_command(message: dict) -> Optional[str]:
    entities = message.get('entities', [])
    if len(entities) != 1:
        return
    entity = entities[0]
    if entity['type'] != 'bot_command':
        return
    text = message['text']
    if text.startswith('/') and entity['offset'] == 0:
        name = text[1:entity['length']]  # skip ahead '/'
        return name


class EvernoteBot(
    MessageHandlerMixin,
    StartCommandMixin,
    SwitchModeCommand,
    SwitchNotebookCommand,
    HelpCommandMixin
):

    def __init__(self, config: dict):
        super().__init__(config)
        self.debug = config['debug']
        self.logger = logging.getLogger('evernotebot')
        storage_config = config['storage']
        self.failed_updates = Storage('failed_updates', storage_config)

    async def stop(self):
        await self.exec_all_mixins('on_bot_stop')
        self.failed_updates.close()

    async def process_update(self, update: dict):
        self.logger.debug(update)
        try:
            await self.exec_all_mixins('on_bot_update', update)
            if 'message' in update:
                await self.receive_message(update['message'])
            elif 'edited_message' in update:
                pass
            elif 'channel_post' in update:
                await self.channel_post(update['channel_post'])
            elif 'edited_channel_post' in update:
                pass
            else:
                self.logger.warning('update is ignored: {0}'.format(str(update)))
        except EvernoteBotException as e:
            self.logger.error(f'{traceback.format_exc()} {e}')
            await self.send_message(f'\u274c Error. {e}')
        except Exception:
            self.logger.error(traceback.format_exc())
            self.failed_updates.create({
                'created': time(),
                'update_data': update,
                'exception': traceback.format_exc(),
            })
        finally:
            await self.exec_all_mixins('on_bot_update_finished')

    async def receive_message(self, message: dict):
        if command_name := parse_command(message):
            await self.exec_all_mixins('on_command', command_name)
            return
        user_state = self.user.get('state')
        if user_state:
            await self.exec_all_mixins('on_user_state', user_state, message)
            return
        await self.exec_all_mixins('on_message', message)
        message_attrs = ('text', 'photo', 'voice', 'audio', 'video', 'document', 'location')
        for message_type in message_attrs:
            if not message.get(message_type):
                continue
            status_message = await self.send_message(f'{message_type.capitalize()} accepted')
            await self.exec_all_mixins(f'on_receive_{message_type}', message)
            if status_message:
                await self.edit_message(status_message['message_id'], 'Saved')

    async def channel_post(self, channel_post: dict):
        await self.receive_message(channel_post)
