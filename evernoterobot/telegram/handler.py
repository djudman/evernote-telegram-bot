from aiohttp import web


async def handle_update(request):
    data = await request.json()

    request.app.logger.info(request.path_qs)
    request.app.logger.info(str(data))

    bot = request.app.bot

    if 'message' in data:
        # TODO: process the message
        message = data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        await bot.sendMessage(chat_id, text)
    elif 'inline_query' in data:
        # TODO: process inline query
        pass
    elif 'chosen_inline_result' in data:
        # TODO: process inline result
        pass
    elif 'callback_query' in data:
        # TODO: process callback query
        pass
    else:
        # TODO: unsupported update
        pass

    return web.Response(body=b'ok')
