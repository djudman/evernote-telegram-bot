import json


async def notebook(robot, chat_id, telegram):
    message = await telegram.sendMessage(
        chat_id, 'Please wait. Getting list of your notebooks...')
    user_id = robot.user.id
    access_token, guid = await robot.get_evernote_access_token(user_id)
    notebooks = robot.evernote.list_notebooks(access_token)
    buttons = []
    for notebook in notebooks:
        btn = {
            'text': notebook.name,
            'callback_data': json.dumps({
                'cmd': 'nb',
                'id': notebook.guid,
            }),
        }
        buttons.append(btn)
    keyboard = {'inline_keyboard': [[b] for b in buttons]}
    await telegram.editMessageText(chat_id, message['message_id'],
                                   'Choose notebook:')
    await telegram.editMessageReplyMarkup(chat_id, message['message_id'],
                                          json.dumps(keyboard))
