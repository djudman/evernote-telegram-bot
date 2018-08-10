from bot.models import User


def handle_text(bot, telegram_message):
    user_id = telegram_message.from_user.id
    user = bot.get_storage(User).get(user_id)
    bot.evernote.create_note(
        user.evernote.access_token,
        user.evernote.notebook.guid,
        telegram_message.text,
        telegram_message.text[:20]
    )
