import json

from telegram.bot import TelegramBotCommand


class SwitchModeCommand(TelegramBotCommand):

    name = 'switch_mode'

    async def execute(self, user, message):
        buttons = []
        for mode in ['one_note', 'multiple_notes']:
            mode = mode.capitalize().replace('_', ' ')
            if user.mode == mode:
                name = "> %s <" % mode
            else:
                name = mode
            buttons.append({'text': name})

        markup = json.dumps({
                'keyboard': [[b] for b in buttons],
                'resize_keyboard': True,
                'one_time_keyboard': True,
            })
        await self.bot.api.sendMessage(
            user.telegram_chat_id, 'Please, select mode',
            reply_markup=markup)

        user.state = 'switch_mode'
        await user.save()
