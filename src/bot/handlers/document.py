from os.path import basename
from os.path import join
from urllib.parse import urlparse

from util.http import make_request


def handle_document(bot, telegram_message):
    max_size = 20 * 1024 * 1024 # telegram restriction. We can't download any file that has size more than 20Mb
    if telegram_message.document.file_size > max_size:
        raise Exception('File too big. Telegram does not allow to the bot to download files over 20Mb.')
    file_id = telegram_message.document.file_id
    download_url = bot.api.getFile(file_id)
    data = make_request(download_url)
    filename = join(bot.config['tmp_root'], '{0}_{1}'.format(file_id, basename(urlparse(download_url).path)))
    with open(filename, 'wb') as f:
        f.write(data)
    user = bot.get_user(telegram_message)
    title = telegram_message.caption or telegram_message.text[:20] or 'Document'
    bot.save_note(user, text=telegram_message.text, title=title, files=(filename,))

