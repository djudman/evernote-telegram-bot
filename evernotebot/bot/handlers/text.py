def handle_text(bot, telegram_message):
    user = bot.get_user(telegram_message)
    status_message = bot.api.sendMessage(telegram_message.chat.id, 'Text accepted')
    bot.save_note(user, text=telegram_message.text, title=telegram_message.text[:20])
    bot.api.editMessageText(telegram_message.chat.id, status_message['message_id'], 'Saved')
