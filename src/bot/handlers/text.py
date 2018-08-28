def handle_text(bot, telegram_message):
    user = bot.get_user(telegram_message)
    state = user.state
    if state:
        bot.handle_state(state, telegram_message)
    else:
        bot.save_note(user, text=telegram_message.text, title=telegram_message.text[:20])
