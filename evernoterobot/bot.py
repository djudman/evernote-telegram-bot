import settings
from telegram.api import BotApi


bot = BotApi(settings.SECRET['token'])
