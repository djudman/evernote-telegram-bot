import json
import pytest
from ext.telegram.models import *


@pytest.fixture
def telegram_update(text_update) -> TelegramUpdate:
    return TelegramUpdate(json.loads(text_update))


def test_telegram_update(telegram_update: TelegramUpdate):
    assert telegram_update.id


def test_message(telegram_update: TelegramUpdate):
    assert telegram_update.message
    assert telegram_update.message.user


def test_photo(photo_update: str):
    update = TelegramUpdate(json.loads(photo_update))
    assert update.message.photos
    assert update.message.caption == 'test photo description'
    assert len(update.message.photos) == 3
    photo = update.message.photos[0]
    assert photo.file_id
    assert photo.file_size
    assert photo.height
    assert photo.width


def test_location(location_update: str):
    update = TelegramUpdate(json.loads(location_update))
    assert update.message.location
    assert update.message.venue


def test_voice(voice_update: str):
    update = TelegramUpdate(json.loads(voice_update))
    assert update.message.voice
    assert update.message.voice.file_id
    assert update.message.voice.duration
    assert update.message.voice.file_size
    assert update.message.voice.mime_type


def test_document(document_update: str):
    update = TelegramUpdate(json.loads(document_update))
    assert update.message.document
    assert update.message.document.file_size
    assert update.message.document.file_id
    assert update.message.document.file_name
    assert update.message.document.mime_type
