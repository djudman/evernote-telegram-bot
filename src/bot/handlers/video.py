from os.path import basename
from os.path import join
from urllib.parse import urlparse

from util.http import make_request


def handle_video(bot, telegram_message):
    status_message = bot.api.sendMessage(telegram_message.chat.id, 'Video accepted')
    max_size = 20 * 1024 * 1024 # telegram restriction. We can't download any file that has size more than 20Mb
    if telegram_message.video.file_size > max_size:
        raise Exception('File too big. Telegram does not allow to the bot to download files over 20Mb.')
    file_id = telegram_message.video.file_id
    download_url = bot.api.getFile(file_id)
    data = make_request(download_url)
    short_name = basename(urlparse(download_url).path)
    filename = join(bot.config['tmp_root'], '{0}_{1}'.format(file_id, short_name))
    with open(filename, 'wb') as f:
        f.write(data)
    user = bot.get_user(telegram_message)
    quota = bot.evernote.get_quota_info(user.evernote.access.token)
    if quota['remaining'] < len(data):
        reset_date = quota['reset_date'].strftime('%Y-%m-%d %H:%M:%S')
        raise Exception('Your evernote quota is out ({0} bytes remains till {1})'.format(quota['remaining'], reset_date))
    title = telegram_message.caption or telegram_message.text[:20] or 'Video'
    bot.save_note(user, text=telegram_message.text, title=title, files=({'path': filename, 'name': short_name},))
    bot.api.editMessageText(telegram_message.chat.id, status_message['message_id'], 'Saved')

