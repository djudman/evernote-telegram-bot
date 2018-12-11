import json
import time
import sys
from urllib.parse import urlparse
from threading import Thread
from wsgiref.simple_server import make_server

from config import load_config
from util.http import make_request
from web.app import Application


class DummyTelegramApi:
    def __init__(self):
        self.messages = []

    def sendMessage(self, chat_id, text, reply_markup=None, parse_mode=None):
        message_id = len(self.messages) + 1
        self.messages.append({
            'message_id': message_id,
            'chat_id': chat_id,
            'text': text,
            'reply_markup': reply_markup,
            'parse_mode': parse_mode,
        })
        print('[bot message] > {}'.format(text))
        return self.messages[-1]

    def editMessageReplyMarkup(self, chat_id, message_id, reply_markup):
        for message in reversed(self.messages):
            if message_id == message['message_id']:
                message['reply_markup'] = reply_markup
                break

    def editMessageText(self, chat_id, message_id, text, reply_markup=None):
        for message in reversed(self.messages):
            if message_id == message['message_id']:
                message['text'] = text
                print('[bot message, edited] > {}'.format(text))
                break


class DummyEvernoteApi:
    def get_oauth_data(self, user_id, session_key, evernote_config, access='basic'):
        return {
            'oauth_url': 'http://127.0.0.1:8080/evernote/oauth',
            'oauth_token': 'secret',
            'oauth_token_secret': 'secret',
            'callback_key': 'secret',
        }

    def get_access_token(self, api_key, api_secret, oauth_token, oauth_token_secret, oauth_verifier):
        return 'token'

    def get_default_notebook(self, token):
        return {'guid': 'test', 'name': 'test'}

    def create_note(self, token, notebook_guid, text=None, title=None, files=None, html=None):
        pass

    def update_note(self, token, note_guid, text=None, title=None, files=None, html=None):
        pass


class DevServer(Thread):
    def __init__(self):
        super().__init__()
        self.running = True
        config = load_config()
        self.webapp = Application(config)
        self.webapp.bot.api = DummyTelegramApi()
        self.webapp.bot.evernote = DummyEvernoteApi()

    def run(self):
        def app(environ, start_response):
            status, response_headers, response_body = self.webapp.handle_request(environ)
            start_response(status, response_headers)
            return [response_body]

        server = make_server('', 8080, app)
        while self.running:
            server.handle_request()

    def stop(self):
        print('Stopping server...', end='')
        self.running = False
        print('OK')


class Debugger:
    def __init__(self):
        self.user_id = 1
        self.server = DevServer()
        self.server.start()
        self.host = 'localhost'
        self.port = 8080
        self.config = load_config()
        self.updates_counter = 1
        self.stderr = open('/tmp/stderr', 'w')
        sys.stderr = self.stderr

    def register_user(self):
        self.send('/start')
        last_message = self.server.webapp.bot.api.messages[-1]
        print(last_message)
        url = json.loads(last_message['reply_markup'])['inline_keyboard'][0][0]['url']
        params = {
            'key': 'secret',
            'oauth_verifier': 'secret',
        }
        make_request(url, 'GET', params)

    def get_text(self):
        return input('[debugger] > ')

    def send(self, text):
        webhook_url = urlparse(self.config['webhook_url'])
        url = 'http://{host}:{port}{path}'.format(host=self.host, port=self.port, path=webhook_url.path)
        telegram_update_data = self.make_telegram_update(text)
        data = json.dumps(telegram_update_data)
        response_data = make_request(url, 'POST', None, data)
        if response_data != b'':
            print('[invalid bot response] > {}'.format(response_data))

    def make_telegram_update(self, text):
        update_id = self.updates_counter
        self.updates_counter += 1
        update_data = {
            "update_id": update_id,
            "message": {
                "message_id": update_id,
                "from": {
                    "id": self.user_id,
                    "is_bot": False,
                    "first_name": "Debugger",
                    "last_name": "Debugger",
                    "username": "debugger",
                    "language_code": "root"
                },
                "chat": {
                    "id": self.user_id,
                    "first_name": "Debugger",
                    "last_name": "Debugger",
                    "username": "debugger",
                    "type": "private"
                },
                "date": time.time(),
                "text": text
            }
        }
        if text.startswith('/'):
            entities = [
                {
                    'offset': 0,
                    'length': len(text),
                    'type': 'bot_command',
                }
            ]
            update_data['message']['entities'] = entities
        return update_data

    def run(self):
        self.register_user()
        while True:
            text = self.get_text()
            self.send(text)

    def stop(self):
        self.server.stop()
        self.send('')
        self.server.join()
        self.stderr.close()


if __name__ == '__main__':
    debugger = Debugger()
    print('Evernotebot debugger.')
    try:
        debugger.run()
    except KeyboardInterrupt:
        pass
    debugger.stop()
    print('\nStopped.')
