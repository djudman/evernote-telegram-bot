from evernotebot.bot.shortcuts import get_message_caption, get_telegram_link


def on_message_text(bot, message: dict):
    user = bot.ctx['user']
    html = format_html(message)
    telegram_link = get_telegram_link(message)
    if telegram_link:
        html = f'<div><p><a href="{telegram_link}">{telegram_link}</a></p>{html}</div>'
    title = get_message_caption(message) or '[Telegram bot]'
    bot.save_note(user, '', title=title, html=html)


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
