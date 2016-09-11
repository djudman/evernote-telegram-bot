from typing import List, Dict


class TelegramUpdate:
    def __init__(self, data: dict):
        self.id = data['update_id']
        if data.get('message'):
            self.message = Message(data['message'])
        if data.get('callback_query'):
            self.callback_query = CallbackQuery(data['callback_query'])

class Chat:
    def __init__(self, data: dict):
        self.id = data['id']
        self.type = data['type']

class TelegramUser:
    def __init__(self, data: dict):
        self.id = data['id']
        self.last_name = data.get('last_name', '')
        self.first_name = data.get('first_name', '')
        self.username = data.get('username', '')

class File:
    def __init__(self, data: dict):
        self.file_size = data['file_size']
        self.file_id = data['file_id']
        self.mime_type = data.get('mime_type')

class Photo(File):
    def __init__(self, data: dict):
        super().__init__(data)
        self.width = data['width']
        self.height = data['height']

class Video(File):
    def __init__(self, data: dict):
        super().__init__(data)

class Document(File):
    def __init__(self, data: dict):
        super().__init__(data)
        self.file_name = data['file_name']

class Voice(File):
    def __init__(self, data: dict):
        super().__init__(data)
        self.duration = data['duration']

class Location:
    def __init__(self, data: dict):
        self.latitude = data['latitude']
        self.longitude = data['longitude']

class Venue:
    def __init__(self, data: dict):
        self.foursquare_id = data.get('foursquare_id')
        self.address = data.get('address')
        self.title = data.get('title')
        self.location = Location(data['location'])

class Entity:
    def __init__(self, data: dict):
        self.type = data['type']
        self.length = data.get('length')
        self.offset = data.get('offset')

class Message:
    def __init__(self, data: dict):
        self.raw = data
        self.id = data['message_id']
        self.date = data['date']
        self.user = TelegramUser(data['from'])
        self.caption = data.get('caption')
        self.chat = Chat(data['chat'])
        self.text = data.get('text')
        self.bot_commands = self.__get_bot_commands(data.get('entities', []), self.text)
        if data.get('photo'):
            self.photos = [Photo(photo_data) for photo_data in data.get('photo')]
        if data.get('video'):
            self.video = Video(data['video'])
        if data.get('document'):
            self.document = Document(data['document'])
        if data.get('voice'):
            self.voice = Voice(data['voice'])
        if data.get('location'):
            self.location = Location(data['location'])
            if data.get('venue'):
                self.venue = Venue(data['venue'])

    def __get_bot_commands(self, entities: List[Dict], text: str):
        bot_cmd_entities = [entity for entity in entities
                            if entity.get('type') == 'bot_command']
        return [
            text[entity['offset']:entity['length']]
            for entity in bot_cmd_entities
        ]


class CallbackQuery:
    def __init__(self, data: dict):
        self.id = data['id']
        self.user = TelegramUser(data['from'])
        self.message = Message(data['message'])
        self.inline_message_id = data.get('inline_message_id')
        self.data = data.get('data')