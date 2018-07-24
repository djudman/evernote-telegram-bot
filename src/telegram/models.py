from typing import List, Dict


class TelegramUpdate:
    def __init__(self, data: dict):
        self.id = data['update_id']
        self.message = TelegramMessage(data['message']) if data.get('message') else None
        self.edited_message = TelegramMessage(data['edited_message']) if data.get('edited_message') else None
        self.channel_post = TelegramMessage(data['channel_post']) if data.get('channel_post') else None
        self.edited_channel_post = TelegramMessage(data['edited_channel_post']) if data.get('edited_channel_post') else None
        self.callback_query = TelegramCallbackQuery(data['callback_query']) if data.get('callback_query') else None
        # TODO: support other fields

    def get_command(self):
        message = self.message
        if not message:
            return
        if not message.entities or len(message.entities) > 1:
            return
        entity = next(iter(message.entities))
        if entity.type != 'bot_command':
            return
        if message.text.startswith('/') and entity.offset == 0:
            return message.text[1:entity.length] # skip ahead '/'


class TelegramChat:
    def __init__(self, data: dict):
        self.id = data['id']
        self.type = data['type'] # “private”, “group”, “supergroup” or “channel”
        self.title = data.get('title')
        self.username = data.get('username')
        self.first_name = data.get('first_name')
        self.last_name = data.get('last_name')
        self.description = data.get('decription')
        # TODO: support other fields


class TelegramUser:
    def __init__(self, data: dict):
        self.id = data['id']
        self.is_bot = data['is_bot']
        self.first_name = data['first_name']
        self.last_name = data.get('last_name')
        self.username = data.get('username')
        self.language_code = data.get('language_code')


class TelegramAudio:
    def __init__(self, data: dict):
        self.file_id = data['file_id']
        self.duration = int(data['duration'])
        self.performer = data.get('performer')
        self.title = data.get('title')
        self.mime_type = data.get('mime_type')
        self.file_size = int(data['file_size']) if data.get('file_size') else None


class TelegramPhotoSize:
    def __init__(self, data: dict):
        self.file_id = data['file_id']
        self.width = int(data['width'])
        self.height = int(data['height'])
        self.file_size = int(data['file_size']) if data.get('file_size') else None


class TelegramSticker:
    def __init__(self, data: dict):
        self.file_id = data['file_id']
        self.width = int(data['width'])
        self.height = int(data['height'])
        self.thumb = TelegramPhotoSize(data['thumb']) if data.get('thumb') else None
        self.emoji = data.get('emoji')
        self.set_name = data.get('set_name')
        # TODO: mask_position
        self.file_size = int(data['file_size']) if data.get('file_size') else None


class TelegramVideo:
    def __init__(self, data: dict):
        self.file_id = data['file_id']
        self.width = int(data['width'])
        self.height = int(data['height'])
        self.duration = data['duration']
        self.thumb = TelegramPhotoSize(data['thumb']) if data.get('thumb') else None
        self.mime_type = data.get('mime_type')
        self.file_size = int(data['file_size']) if data.get('file_size') else None


class TelegramDocument:
    def __init__(self, data: dict):
        self.file_id = data['file_id']
        self.thumb = TelegramPhotoSize(data['thumb']) if data.get('thumb') else None
        self.file_name = data.get('file_name')
        self.mime_type = data.get('mime_type')
        self.file_size = int(data['file_size']) if data.get('file_size') else None


class TelegramVoice:
    def __init__(self, data: dict):
        self.file_id = data['file_id']
        self.duration = data['duration']
        self.mime_type = data.get('mime_type')
        self.file_size = int(data['file_size']) if data.get('file_size') else None


class TelegramLocation:
    def __init__(self, data: dict):
        self.latitude = float(data['latitude'])
        self.longitude = float(data['longitude'])


class TelegramVenue:
    def __init__(self, data: dict):
        self.location = TelegramLocation(data['location'])
        self.title = data['title']
        self.address = data['address']
        self.foursquare_id = data.get('foursquare_id')


class TelegramMessage:
    def __init__(self, data: dict):
        self.raw = data
        self.id = int(data['message_id'])
        self.from_user = TelegramUser(data['from']) if data.get('from') else None
        self.date = int(data['date'])
        self.chat = TelegramChat(data['chat'])
        self.forward_from = TelegramUser(data['forward_from']) if data.get('forward_from') else None
        self.forward_from_chat = TelegramChat(data['forward_from_chat']) if data.get('forward_from_chat') else None
        self.forward_from_message_id = int(data['forward_from_message_id']) if data.get('forward_from_message_id') else None
        self.forward_signature = data['forward_signature'] if data.get('forward_signature') else None
        self.forward_date = int(data['forward_date']) if data.get('forward_date') else None
        # TODO: reply_to_message
        # TODO: edit_date
        self.text = data.get('text')
        self.entities = []
        if data.get('entities'):
            for entity_data in data['entities']:
                entity = TelegramMessageEntity(entity_data)
                self.entities.append(entity)
        self.audio = TelegramAudio(data['audio']) if data.get('audio') else None
        self.document = TelegramDocument(data['document']) if data.get('document') else None
        # TODO: game
        self.photo = [TelegramPhotoSize(data) for data in data['photo']] if data.get('photo') else None
        self.sticker = TelegramSticker(data['sticker']) if data.get('sticker') else None
        self.video = TelegramVideo(data['video']) if data.get('video') else None
        self.voice = TelegramVoice(data['voice']) if data.get('voice') else None
        # TODO: video_note
        self.caption = data.get('caption')
        # TODO: contact
        if data.get('location'):
            self.location = TelegramLocation(data['location'])
            self.venue = TelegramVenue(data['venue']) if data.get('venue') else None
        # TODO: add other fields


class TelegramMessageEntity:
    def __init__(self, data: dict):
        self.type = data['type'] # Can be mention (@username), hashtag, bot_command, url, email, bold (bold text), italic (italic text), code (monowidth string), pre (monowidth block), text_link (for clickable text URLs), text_mention (for users without usernames)
        self.offset = int(data['offset'])
        self.length = int(data['length'])
        self.url = data.get('url') # Optional. For “text_link” only, url that will be opened after user taps on the text
        self.user = TelegramUser(data['user']) if data.get('user') else None # Optional. For “text_mention” only, the mentioned user


class TelegramCallbackQuery:
    def __init__(self, data: dict):
        self.id = data['id']
        self.user = TelegramUser(data['from'])
        self.message = TelegramMessage(data['message'])
        self.inline_message_id = data.get('inline_message_id')
        self.data = data.get('data')
