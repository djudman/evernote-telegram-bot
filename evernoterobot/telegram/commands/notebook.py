import json


async def notebook(robot, chat_id, telegram):
    user_id = robot.user.id
    access_token = await robot.get_evernote_access_token(user_id)
    notebooks = robot.evernote.list_notebooks(access_token)
    buttons = []
    for notebook in notebooks:
        btn = {
            'text': notebook.name,
            'callback_data': json.dumps({
                'cmd': 'set_notebook',
                'guid': notebook.guid,
            }),
        }
        buttons.append(btn)
    keyboard = {'inline_keyboard': [[b] for b in buttons]}
    message = await telegram.sendMessage(chat_id, 'Choose notebook:',
                                         json.dumps(keyboard))
    for notebook in notebooks:
        btn = {
            'text': notebook.name,
            'callback_data': json.dumps({
                'cmd': 'set_notebook',
                'mid': message['message_id'],
                'guid': notebook.guid,
            }),
        }
        buttons.append(btn)
    keyboard = {'inline_keyboard': [[b] for b in buttons]}
    await telegram.editMessageReplyMarkup(chat_id, message['message_id'],
                                          json.dumps(keyboard))
