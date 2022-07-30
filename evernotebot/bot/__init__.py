import logging
import traceback
from time import time
from typing import Optional

from evernotebot.bot.errors import EvernoteBotException
from evernotebot.bot.mixins import (
    StartCommandMixin,
    SwitchModeCommand,
    SwitchNotebookCommand,
    HelpCommandMixin,
    MessageHandlerMixin
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

    def stop(self):
        self.exec_all_mixins('on_bot_stop')
        self.failed_updates.close()

    def process_update(self, update: dict):
        self.logger.fatal(update)
        try:
            self.exec_all_mixins('on_bot_update', update)
            if 'message' in update:
                self.receive_message(update['message'])
            elif 'edited_message' in update:
                pass
            elif 'channel_post' in update:
                self.channel_post(update['channel_post'])
            elif 'edited_channel_post' in update:
                pass
            else:
                self.logger.warning('update is ignored: {0}'.format(str(update)))
        except EvernoteBotException as e:
            self.logger.error(f'{traceback.format_exc()} {e}')
            self.send_message(f'\u274c Error. {e}')
        except Exception:
            self.logger.error(traceback.format_exc())
            self.failed_updates.create({
                'created': time(),
                'update_data': update,
                'exception': traceback.format_exc(),
            })
        finally:
            self.exec_all_mixins('on_bot_update_finished')

    def receive_message(self, message: dict):
        if command_name := parse_command(message):
            self.exec_all_mixins('on_command', command_name)
            return
        user_state = self.user.get('state')
        if user_state:
            self.exec_all_mixins('on_user_state', user_state, message)
            return
        self.exec_all_mixins('on_message', message)
        message_attrs = ('text', 'photo', 'voice', 'audio', 'video', 'document', 'location')
        for name in message_attrs:
            message_type = message.get(name)
            if not message_type:
                continue
            status_message = self.send_message(f'{message_type.capitalize()} accepted')
            self.exec_all_mixins(f'on_receive_{message_type}', message)
            if status_message:
                self.edit_message(status_message['message_id'], 'Saved')

    def channel_post(self, channel_post: dict):
        self.receive_message(channel_post)
