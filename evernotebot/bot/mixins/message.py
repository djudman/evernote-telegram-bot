import math
from os.path import basename, join
from urllib.parse import urlparse

from evernotebot.bot.errors import EvernoteBotException
from evernotebot.bot.mixins import EvernoteMixin
from evernotebot.util.http import make_request


def get_message_text(message: dict, start: int = 0, end: int = None) -> str:
    text = message.get('text', '')
    text = text.encode('utf-16')
    text = text[2:]  # skip BOM
    start = start * 2 if start is not None else None  # 2 bytes per symbol
    end = end * 2 if end is not None else None
    text = text[start:end].decode('utf-16')
    text = text.replace('&', '&amp;')
    text = text.replace('>', '&gt;')
    text = text.replace('<', '&lt;')
    text = text.replace('\n', '<br />')
    return text


def format_html(message: dict) -> str:
    entities = message.get('entities', [])
    if not entities:
        return get_message_text(message)
    pointer = 0
    strings = []
    for entity in entities:
        offset = entity.get('offset')
        text = get_message_text(message, pointer, offset)
        strings.append(text)
        start, end = offset, offset + entity['length']
        if start < pointer:
            continue
        string = get_message_text(message, start, end)
        type_label = entity['type']
        if type_label == 'text_link':
            url = entity['url']
            html = f'<a href="{url}">{string}</a>'
        elif type_label == 'pre':
            html = f'<pre>{string}</pre>'
        elif type_label == 'bold':
            html = f'<b>{string}</b>'
        elif type_label == 'italic':
            html = f'<i>{string}</i>'
        elif type_label == 'underline':
            html = f'<u>{string}</u>'
        elif type_label == 'strikethrough':
            html = f'<s>{string}</s>'
        else:
            html = string
        strings.append(html)
        pointer = end
    strings.append(get_message_text(message, pointer))
    text = ''.join(strings)
    text = '<br />'.join(text.split('\n'))
    return text


def get_message_caption(message: dict) -> str:
    if user := message.get('forward_from'):
        parts = filter(lambda x: x, (user['first_name'], user['last_name']))
        name = ' '.join(parts)
        if username := user.get('username'):
            name += f' {username}'
        return f'Forwarded from {name}'
    if chat := message.get('forward_from_chat'):
        name = chat.get('title', chat['username'])
        return f'Forwarded from {chat.type} {name}'
    if sender_name := message.get('forward_sender_name'):
        return f'Forwarded from {sender_name}'
    return message.get('caption')


def get_telegram_link(message: dict) -> str:
    if chat := message.get('forward_from_chat'):
        username = chat['username']
        message_id = message['forward_from_message_id']
        return f'https://t.me/{username}/{message_id}'


class MessageHandlerMixin(EvernoteMixin):
    def on_receive_text(self, message: dict):
        html = format_html(message)
        telegram_link = get_telegram_link(message)
        if telegram_link:
            html = f'<div><p><a href="{telegram_link}">{telegram_link}</a></p>{html}</div>'
        title = get_message_caption(message) or '[Telegram bot]'
        self.save_note('', title=title, html=html)

    def on_receive_photo(self, message: dict):
        max_size = 20 * 1024 * 1024  # telegram restriction. We can't download any file that has size more than 20Mb
        file_id = None
        file_size = math.inf
        for photo in message['photo']:  # pick the biggest file
            if photo.file_size <= max_size and \
                    (file_size == math.inf or file_size < photo.file_size):
                file_size = photo.file_size
                file_id = photo.file_id
        self.save_file(file_id, file_size, message)

    def on_receive_video(self, message: dict):
        file_size = message['video']['file_size']
        file_id = message['video']['file_id']
        self.save_file(file_id, file_size, message)

    def on_receive_document(self, message: dict):
        file_size = message['document']['file_size']
        file_id = message['document']['file_id']
        self.save_file(file_id, file_size, message)

    def on_receive_voice(self, message: dict):
        file_id = message['voice']['file_id']
        file_size = message['voice']['file_size']
        self.save_file(file_id, file_size, message)

    def on_receive_location(self, message: dict):
        latitude = message['location']['latitude']
        longitude = message['location']['longitude']
        maps_url = f'https://maps.google.com/maps?q={latitude},{longitude}'
        title = 'Location'
        html = f'<a href="{maps_url}">{maps_url}</a>'
        if venue := message.get('venue'):
            title = venue.get(title) or title
            address = venue['address']
            html = f'{title}<br />{address}<br /><a href="{maps_url}">{maps_url}</a>'
            if foursquare_id := venue.get('foursquare_id'):
                url = f'https://foursquare.com/v/{foursquare_id}'
                html += f'<br /><a href="{url}">{url}</a>'
        title = get_message_caption(message) or title
        self.save_note(title=title, html=html)

    def save_file(self, file_id, file_size, message: dict):
        download_dir = self.config['tmp_root']
        filename, short_name = self.download_telegram_file(file_id, file_size, download_dir)
        self.evernote_check_quota(file_size)
        title = get_message_caption(message) or (message['text'] and message['text'][:20]) or 'File'
        files = ({'path': filename, 'name': short_name},)
        text = ''
        telegram_link = get_telegram_link(message)
        if telegram_link:
            text = f'<div><p><a href="{telegram_link}">{telegram_link}</a></p><pre>{message["caption"]}</pre></div>'
        self.save_note('', title=title, files=files, html=text)

    def download_telegram_file(self, file_id, file_size, dirpath='/tmp'):
        max_size = 20 * 1024 * 1024
        if file_size > max_size:
            raise EvernoteBotException('File too big. Telegram does not allow to the bot to download files over 20Mb.')
        download_url = self.api.getFile(file_id)
        data = make_request(download_url)
        short_name = basename(urlparse(download_url).path)
        filepath = join(dirpath, f'{file_id}_{short_name}')
        with open(filepath, 'wb') as f:
            f.write(data)
        return filepath, short_name
