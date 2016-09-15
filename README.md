Telegram bot for [Evernote](https://evernote.com).
==========================

This bot available in Telegram: https://telegram.me/evernoterobot

Description:
-----------

You can just send message to this bot and it saves your message as note in Evernote. You can send to bot:

* text
* photo
* file
* video
* voice message
* location


Commands:
--------

* [__/start__](https://telegram.me/evernoterobot)

  Send this command to start work with this bot
* /notebook

  Send this command if you would like change notebook for your notes
* /switch_mode

  Bot support two modes (see below for more information). You can switch between them with this command.
* /help

  This command just sends some information about bot to you. Like this description


Bot modes
---------
Bot can work in two modes:


1. **Multiple notes** mode.

  In this mode all your messages will be saved as **separate** note in Evernote notebook.
2. **One note** mode.

  In this mode all your messages will be save in **same** note in Evernote notebook.
  
  *Note*: When you are switch current notebook in this mode, there are new "common" note will be created (each time)
  
  *Warning*: to use this mode, you should give permissions to bot to read and update notes.
