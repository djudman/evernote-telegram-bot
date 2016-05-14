import json


async def help(robot, chat_id, telegram):
    text = '''What is it?
- Bot for fast saving notes to Evernote
Contacts
- djudman@gmail.com'''
    await telegram.sendMessage(chat_id, text,
                               json.dumps({'hide_keyboard': True}))
