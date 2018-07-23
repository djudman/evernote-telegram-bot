def help_command(bot, chat_id):
    help_text = 'Welcome!'
    bot.api.sendMessage(chat_id, help_text)


def start_command(user, telegram_update):
    pass
