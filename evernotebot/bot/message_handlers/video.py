def on_video(bot, message: dict):
    file_size = message['video']['file_size']
    file_id = message['video']['file_id']
    bot.save_file_to_evernote(file_id, file_size, message)
