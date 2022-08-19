import os
from multiprocessing import Process
from time import sleep

from evernotebot.app import EvernoteBotApplication
from evernotebot.util.logs import init_logging

from tests.telegram.api import Api
from tests.telegram.client import BotClient
from tests.telegram.server import Server


class TelegramApi(Process):
    def run(self) -> None:
        init_logging(debug=True)
        app = Api('127.0.0.1', 11000)
        app.run()


class TelegramServer(Process):
    def run(self) -> None:
        init_logging(debug=True)
        self.srv = Server(('127.0.0.1', 12000), 'http://127.0.0.1:11000')
        self.srv.add_bot('evernotebot', 'bot_api_token')
        self.srv.serve_forever()

    def close(self) -> None:
        self.srv.server_close()


class TestBot(Process):
    def run(self) -> None:
        init_logging(debug=True)
        app = EvernoteBotApplication(port=8081)
        app.run()


def check_env(var_names: list[str]):
    vars = {name: os.environ.get(name) for name in var_names}
    empty_vars = list(filter(lambda v: v[1] is None, vars.items()))
    if empty_vars:
        names = [f'`{name}`' for name, v in empty_vars]
        raise Exception(f'\nEnvironment variables is not set: {",".join(names)}')


if __name__ == '__main__':
    check_env(['EVERNOTE_READONLY_KEY', 'EVERNOTE_READONLY_SECRET'])
    files = (
        '/tmp/evernotebot-data/evernotebot',
        '/tmp/telegram-api/telegram_api',
    )
    for filename in files:
        if os.path.exists(filename):
            os.unlink(filename)
    TelegramApi().start()
    sleep(1)
    TelegramServer().start()
    sleep(1)
    TestBot().start()
    sleep(1)

    client = BotClient()
    client.run()
