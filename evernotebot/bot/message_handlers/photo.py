import math


def on_photo(bot, message: dict):
    max_size = 20 * 1024 * 1024  # telegram restriction. We can't download any file that has size more than 20Mb
    file_id = None
    file_size = math.inf
    for photo in message['photo']:  # pick the biggest file
        if photo.file_size <= max_size and \
                (file_size == math.inf or file_size < photo.file_size):
            file_size = photo.file_size
            file_id = photo.file_id
    bot.save_file_to_evernote(file_id, file_size, message)
