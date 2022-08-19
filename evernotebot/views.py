import asyncio
import traceback

from evernotebot.bot import EvernoteBot
from evernotebot.bot.api import BotApiError
from evernotebot.bot.errors import EvernoteBotException
from evernotebot.util.asgi import Request


async def set_webhook(request: Request):
    bot: EvernoteBot = request.app.bot
    config = request.app.config
    webhook_url = config['webhook_url']
    try:
        asyncio.run(bot.api.setWebhook(webhook_url))
    except Exception:
        message = f"Can't set up webhook url `{webhook_url}`"
        bot.logger.fatal(message, exc_info=True)


async def telegram_hook(request: Request):
    data = await request.json()
    if data:
        bot: EvernoteBot = request.app.bot
        try:
            await bot.process_update(data)
        except BotApiError as e:
            bot.logger.error(f'{traceback.format_exc()} {e}')
        return 'ok'
    return 'request body is empty'


async def evernote_oauth(request: Request):
    bot: EvernoteBot = request.app.bot
    params = request.GET
    callback_key = params['key']
    access_type = params['access']
    if access_type not in {'readonly', 'readwrite'}:
        raise Exception(f'Invalid access type {access_type}')
    verifier = params.get('oauth_verifier')
    try:
        await bot.evernote_auth(callback_key, access_type, verifier)
    except EvernoteBotException as e:
        await bot.send_message(e.message)
    return request.make_response(status=302, body=bot.url.encode())
