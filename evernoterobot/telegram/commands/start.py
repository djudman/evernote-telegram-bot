import json


async def start(robot, chat_id, telegram):
    welcome_text = '''Hi! I'm robot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with me.'''
    signin_button = {
        'text': 'Waiting for Evernote...',
        'url': robot.bot_url,
    }
    inline_keyboard = {'inline_keyboard': [[signin_button]]}
    message = await telegram.sendMessage(chat_id, welcome_text,
                                         json.dumps(inline_keyboard))
    # TODO: async
    user_id = robot.user.id
    oauth_data = robot.evernote.get_oauth_data(user_id)
    await robot.create_start_session(user_id, oauth_data)

    signin_button['text'] = 'Sign in to Evernote'
    signin_button['url'] = oauth_data.oauth_url
    await telegram.editMessageReplyMarkup(chat_id, message['message_id'],
                                          json.dumps(inline_keyboard))
