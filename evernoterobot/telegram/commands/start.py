import json


async def start(robot, chat_id, telegram):
    welcome_text = '''Hi! I'm robot for saving your notes to Evernote on fly.
Please tap on button below to link your Evernote account with me.'''
    signin_button = {
        'text': 'Preparing link for you...',
        'url': robot.bot_url,
    }
    inline_keyboard = [[signin_button]]
    message = await telegram.sendMessage(chat_id, welcome_text,
                                         json.dumps(inline_keyboard))
    # startsession = await session.get_start_session(self.user.id)
    # if not startsession:
    #     callback_key = self.get_callback_key(self.user.id)
    #     callback_url = "%(callback_url)s?key=%(key)s" % {
    #             'callback_url': self.evernote_oauth_callback,
    #             'key': callback_key,
    #         }
    #     request_token = self.evernote.get_request_token(callback_url)
    #     oauth_token = request_token['oauth_token']
    #     oauth_token_secret = request_token['oauth_token_secret']
    #     # TODO: put tokens to cache
    #     oauth_url = self.evernote.get_authorize_url(request_token)
    #     await session.save_start_session(self.user.id, oauth_url,
    #                                      callback_key)
    # else:
    #     oauth_url = startsession['oauth_url']

    signin_button['text'] = 'Sign in to Evernote'
    signin_button['url'] = robot.bot_url
    await telegram.editMessageReplyMarkup(chat_id, message['message_id'],
                                          json.dumps(inline_keyboard))
