import os
from evernotebot.app import EvernoteBotApplication


def set_var(name, value):
    os.environ[name] = value


map(set_var, (
    ('TELEGRAM_API_TOKEN', 'debug'),
    ('EVERNOTE_BASIC_ACCESS_KEY', 'debug'),
    ('EVERNOTE_BASIC_ACCESS_SECRET', 'debug'),
    ('EVERNOTE_FULL_ACCESS_KEY', 'debug'),
    ('EVERNOTE_FULL_ACCESS_SECRET', 'debug'),
))


app = EvernoteBotApplication()
try:
    print(f'Starting `{app.bot.name}` at http://{app.config["host"]}...')
    app.run()
except KeyboardInterrupt:
    app.shutdown()
