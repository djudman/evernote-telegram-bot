def on_document(bot, message: dict):
    file_size = message['document']['file_size']
    file_id = message['document']['file_id']
    bot.save_file_to_evernote(file_id, file_size, message)
