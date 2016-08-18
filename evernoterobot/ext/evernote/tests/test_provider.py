import pytest

from conftest import AsyncMock
from ext.evernote.provider import NoteProvider


@pytest.mark.async_test
async def test_evernote_provider():
    provider = NoteProvider()
    provider.cache = AsyncMock()
    provider._api = AsyncMock()
    # TODO: