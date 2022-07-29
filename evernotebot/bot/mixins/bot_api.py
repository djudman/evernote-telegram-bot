from evernotebot.bot.api import BotApi
from evernotebot.bot.mixins.base import BaseMixin


class BotApiMixin(BaseMixin):
    def __init__(self, config: dict):
        super(BotApiMixin, self).__init__(config)
        token = config['telegram']['token']
        bot_api_url = config['telegram']['api_url']
        self.api = BotApi(token, bot_api_url)
