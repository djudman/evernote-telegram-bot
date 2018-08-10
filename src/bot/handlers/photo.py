from os.path import basename
from os.path import join
from urllib.parse import urlparse

from bot.models import User
from util.http import make_request


def handle_photo(bot, telegram_message):
    max_size = 20 * 1024 * 1024 # telegram restriction. We can't download any file that has size more than 20Mb
    filenames = []
    for photo in telegram_message.photo:
        if photo.file_size > max_size:
            continue
        download_url = bot.api.getFile(photo.file_id)
        data = make_request(download_url)
        filename = join(bot.config['tmp_root'], '{0}_{1}'.format(photo.file_id, basename(urlparse(download_url).path)))
        with open(filename, 'wb') as f:
            f.write(data)
        filenames.append(filename)
    user_id = telegram_message.from_user.id
    user = bot.get_storage(User).get(user_id)
    bot.evernote.create_note(
        user.evernote.access_token,
        user.evernote.notebook.guid,
        telegram_message.text,
        telegram_message.caption or telegram_message.text[:20] or 'Photo',
        filenames
    )

