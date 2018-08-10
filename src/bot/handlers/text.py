from bot.models import User


def handle_text(bot, telegram_message):
    status_message = bot.api.sendMessage(telegram_message.chat.id, 'Text accepted')
    user_id = telegram_message.from_user.id
    user = bot.get_storage(User).get(user_id)
    bot.evernote.create_note(
        user.evernote.access_token,
        user.evernote.notebook.guid,
        telegram_message.text,
        telegram_message.text[:20]
    )
    bot.api.editMessageText(telegram_message.chat.id, status_message['message_id'], 'Saved.')
