import json
import os
from os.path import exists

import evernote.edam.type.ttypes as Types
import pytest

from bot import TelegramUpdate
from bot import User
from bot.dealer import EvernoteDealer
from bot.model import FailedUpdate
from conftest import AsyncMock
from ext.telegram.conftest import text_update


@pytest.mark.async_test
async def test_process_text(text_update):
    update = json.loads(text_update)
    User.create(id=425606,
                telegram_chat_id=2,
                mode='one_note',
                evernote_access_token='token',
                current_notebook={ 'guid': '000', 'name': 'test_notebook' },
                places={ '000': 'note_guid' })
    TelegramUpdate.create(user_id=425606,
                          request_type='text',
                          status_message_id=5,
                          message=update['message'])
    dealer = EvernoteDealer()
    mock_note_provider = AsyncMock()
    note = Types.Note()
    mock_note_provider.get_note = AsyncMock(return_value=note)
    mock_telegram_api = AsyncMock()
    dealer._telegram_api = mock_telegram_api
    for k, handlers in dealer._EvernoteDealer__handlers.items():
        for handler in handlers:
            handler._note_provider = mock_note_provider
    updates = dealer.fetch_updates()
    for user_id, update_list in updates.items():
        user = User.get({'id': user_id})
        await dealer.process_user_updates(user, update_list)

    assert mock_note_provider.get_note.call_count == 1
    assert dealer._EvernoteDealer__handlers['text'][0]._note_provider.update_note.call_count == 1


@pytest.mark.async_test
async def test_process_photo_in_one_note_mode():
    User.create(id=1,
                telegram_chat_id=2,
                mode='one_note',
                evernote_access_token='token',
                current_notebook={'guid': '000', 'name': 'test_notebook'},
                places={'000': 'note_guid'})
    TelegramUpdate.create(user_id=1,
                          request_type='photo',
                          status_message_id=5,
                          message={
                              'date': 123123,
                              'chat': {'id': 1, 'type': 'private'},
                              'message_id': 10,
                              'photo': [
                                  {
                                      'height': 200,
                                      'width': 200,
                                      'file_id': 'xBcZ1dW',
                                      'file_size': 100,
                                  },
                              ],
                              'from': {'id': 1},
                          })
    dealer = EvernoteDealer()
    mock_note_provider = AsyncMock()
    note = Types.Note()
    mock_note_provider.get_note = AsyncMock(return_value=note)
    mock_note_provider.save_note = AsyncMock(return_value=Types.Note())
    mock_note_provider.get_note_link = AsyncMock(return_value='http://evernote.com/some/stuff/here/')
    mock_telegram_api = AsyncMock()
    file_path = "/tmp/xBcZ1dW.txt"
    if exists(file_path):
        os.unlink(file_path)
    with open(file_path, 'w') as f:
        f.write('test data')

    dealer._telegram_api = mock_telegram_api
    for k, handlers in dealer._EvernoteDealer__handlers.items():
        for handler in handlers:
            handler._note_provider = mock_note_provider
            handler.get_downloaded_file = AsyncMock(return_value=(file_path, 'text/plain'))

    updates = dealer.fetch_updates()
    for user_id, update_list in updates.items():
        user = User.get({'id': user_id})
        await dealer.process_user_updates(user, update_list)


@pytest.mark.async_test
async def test_failed_update(text_update):
    update = json.loads(text_update)
    User.create(id=425606,
                telegram_chat_id=2,
                mode='one_note',
                evernote_access_token='token',
                current_notebook={'guid': '000', 'name': 'test_notebook'},
                places={'000': 'note_guid'})
    TelegramUpdate.create(user_id=425606,
                          request_type='text',
                          status_message_id=5,
                          message=update['message'])
    dealer = EvernoteDealer()
    mock_note_provider = AsyncMock()
    note = Types.Note()
    mock_note_provider.get_note = AsyncMock(return_value=note)
    mock_telegram_api = AsyncMock()
    dealer._telegram_api = mock_telegram_api
    # for k, handlers in dealer._EvernoteDealer__handlers.items():
    #     for handler in handlers:
    #         handler._note_provider = mock_note_provider
    updates = dealer.fetch_updates()
    for user_id, update_list in updates.items():
        user = User.get({'id': user_id})
        await dealer.process_user_updates(user, update_list)
    failed_updates = FailedUpdate.find()
    assert len(failed_updates) == 1
