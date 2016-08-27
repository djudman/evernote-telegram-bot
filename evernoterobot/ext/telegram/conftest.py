import pytest


@pytest.fixture
def location_update():
    return "{'message': {'chat': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'type': 'private', 'username': 'djudman'}, 'location': {'latitude': 55.64221, 'longitude': 37.618894}, 'message_id': 5363, 'venue': {'foursquare_id': '4daaf4910437dccbd81159ba', 'address': 'Балаклавский пр-т, 2 к5', 'title': 'Камелот', 'location': {'latitude': 55.64221, 'longitude': 37.618894}}, 'date': 1472245857, 'from': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'username': 'djudman'}}, 'update_id': 729409811}".replace("'", '"')


@pytest.fixture
def text_update():
    return "{'message': {'message_id': 5365, 'chat': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'type': 'private', 'username': 'djudman'}, 'date': 1472288841, 'text': 'test text', 'from': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'username': 'djudman'}}, 'update_id': 729409812}".replace('\'', '"')


@pytest.fixture
def command_update():
    return "{'message': {'chat': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'type': 'private', 'username': 'djudman'}, 'message_id': 5369, 'entities': [{'offset': 0, 'type': 'bot_command', 'length': 5}], 'from': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'username': 'djudman'}, 'date': 1472289023, 'text': '/help'}, 'update_id': 729409814}".replace('\'', '"')

@pytest.fixture
def photo_update():
    return "{'message': {'photo': [{'file_size': 1444, 'width': 90, 'height': 90, 'file_id': 'AgADAgADsKkxG4Z-BgABt0N0hcSgpChHGHENAATSqztMWQW9AcWCAQABAg'}, {'file_size': 16926, 'width': 320, 'height': 320, 'file_id': 'AgADAgADsKkxG4Z-BgABt0N0hcSgpChHGHENAARYWAh_IH8xXcSCAQABAg'}, {'file_size': 38827, 'width': 600, 'height': 600, 'file_id': 'AgADAgADsKkxG4Z-BgABt0N0hcSgpChHGHENAARBzpeDiwGQDsOCAQABAg'}], 'message_id': 5367, 'chat': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'type': 'private', 'username': 'djudman'}, 'caption': 'test photo description', 'date': 1472288889, 'from': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'username': 'djudman'}}, 'update_id': 729409813}".replace('\'', '"')


@pytest.fixture
def video_update():
    return "".replace('\'', '"')


@pytest.fixture
def voice_update():
    return "{'message': {'message_id': 5361, 'voice': {'duration': 2, 'mime_type': 'audio/ogg', 'file_size': 17677, 'file_id': 'AwADAgADlQADhn4GAAGbewW705w3ygI'}, 'chat': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'type': 'private', 'username': 'djudman'}, 'date': 1472245486, 'from': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'username': 'djudman'}}, 'update_id': 729409810}".replace('\'', '"')


@pytest.fixture
def document_update():
    return "{'message': {'message_id': 5359, 'document': {'file_size': 173, 'file_name': 'yadisk_mount', 'mime_type': 'text/plain', 'file_id': 'BQADAgADlAADhn4GAAGEdxhGqdDaNAI'}, 'chat': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'type': 'private', 'username': 'djudman'}, 'date': 1472245046, 'from': {'id': 425606, 'last_name': 'Dorofeev', 'first_name': 'Dmitry', 'username': 'djudman'}}, 'update_id': 729409809}".replace('\'', '"')
