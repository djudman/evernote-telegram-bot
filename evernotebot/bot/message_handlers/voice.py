def on_voice(bot, message: dict):
    file_id = message['voice']['file_id']
    file_size = message['voice']['file_size']
    bot.save_file_to_evernote(file_id, file_size, message)
