def help_command(bot, chat_id):
    help_text = '''This is bot for Evernote (https://evernote.com).

Just send message to bot and it creates note in your Evernote notebook. 

You can send to bot:

* text
* photo (size < 12 Mb) - Telegram restriction
* file (size < 12 Mb) - Telegram restriction
* voice message (size < 12 Mb) - Telegram restriction
* location

There are modes:

1) "One note" mode.
On this mode there are just one note will be created in Evernote notebook. All messages that you will send, will be saved in this note.

2) "Multiple notes" mode.
On this mode for every message you sent there is separate note will be created in Evernote notebook.

You can switch bot mode with command /switch_mode
Note that every time you select "One note" mode, new note will be created and set as current note for this bot.

Also, you can switch your current notebook with command /notebook
Note that every time you switch notebook in mode "One note", new note will be created in selected notebook.

We are sorry for low speed, but Evernote API are slow (about 1 sec per request).

Contacts: djudman@gmail.com
'''
    bot.api.sendMessage(chat_id, help_text)


def start_command(user, telegram_update):
    pass
