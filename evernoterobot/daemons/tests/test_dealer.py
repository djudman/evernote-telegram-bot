import asyncio
import pytest

from bot import TelegramUpdate
from bot import User
from conftest import AsyncMock
from daemons.dealer import EvernoteDealer
import evernote.edam.type.ttypes as Types


@pytest.mark.async_test
async def test_process_text():
    User.create(user_id=1,
                telegram_chat_id=2,
                mode='one_note',
                evernote_access_token='token',
                current_notebook={ 'guid': '000', 'name': 'test_notebook' },
                places={ '000': 'note_guid' })
    TelegramUpdate.create(user_id=1,
                          request_type='text',
                          status_message_id=5,
                          data={
                              'chat': {'id': 1},
                              'message_id': 10,
                              'text': 'test_text',
                              'from': {'id': 1},
                          })
    dealer = EvernoteDealer()
    mock_note_provider = AsyncMock()
    note = Types.Note()
    mock_note_provider.get_note = AsyncMock(return_value=note)
    mock_telegram_api = AsyncMock()
    dealer._telegram_api = mock_telegram_api
    dealer._note_provider = mock_note_provider
    updates = dealer.fetch_updates()
    for user_id, update_list in updates.items():
        await dealer.process_user_updates(user_id, update_list)

    assert mock_note_provider.get_note.call_count == 1
    assert dealer._note_provider.update_note.call_count == 1