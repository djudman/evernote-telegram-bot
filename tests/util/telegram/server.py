import _socket
import json
from socketserver import ThreadingTCPServer, StreamRequestHandler
from http.client import HTTPConnection
from typing import Any

import urllib3.util


class Server(ThreadingTCPServer):
    def __init__(self, server_address: tuple, api_url: str):
        super(Server, self).__init__(server_address, RequestHandlerClass)
        self.api_url = api_url.rstrip('/')
        self.clients = {}
        self.chats = []

    def get_request(self) -> tuple[_socket, Any]:
        sock, addr = super().get_request()
        client_id = addr[1]
        self.clients[client_id] = {
            'addr': addr,
            'sock': sock,
        }
        return sock, addr

    def send_response(self, client_id: int, data: dict):
        body = json.dumps(data)
        body_length = len(body)
        sock = self.clients[client_id]['sock']
        message = str(body_length) + '\n' + body + '\n'
        sock.sendall(message.encode())

    def api_request(self, endpoint: str, data: dict, http_method: str = 'post') -> dict:
        api_url = f'{self.api_url}{endpoint}'
        url = urllib3.util.parse_url(api_url)
        conn = HTTPConnection(url.host, url.port)
        body = json.dumps(data).encode()
        conn.request(http_method.upper(), endpoint, body)
        response = conn.getresponse()
        if response.status != 200:
            # TODO: write to log
            pass
        out = response.read()
        out = json.loads(out)
        conn.close()
        return out

    def exec_client_cmd(self, client_id: int, name: str, data: dict):
        cmd = getattr(self, f'cmd_{name}')
        if not cmd:
            raise Exception(f'Unknown command `{name}`')
        response = cmd(client_id, data) or {}
        self.send_response(client_id, response)

    def add_bot(self, name: str, token: str = None):
        user_data = {'is_bot': True, 'bot_name': name, 'token': token}
        self.api_request('/user', user_data, http_method='create')

    def cmd_enter(self, client_id, data: dict):
        user_data = {'user_id': client_id}
        user_data = self.api_request('/user', user_data, http_method='create')
        self.api_request(f'/user/{client_id}/chats', {}, http_method='create')
        response = self.api_request(f'/user/{client_id}/chats', {}, http_method='get')
        return {'user': user_data, 'chats': response['chats']}

    def cmd_message(self, client_id, data: dict):
        chat_id = data['chat_id']
        response = self.api_request(f'/chat/{chat_id}/message', {
            'from': client_id,
            'text': data['text'],
        }, http_method='post')
        if 'send_to' in response:
            self.send_message_to_client(response['send_to'], data['text'])
        return response

    def send_message_to_client(self, client_id: int, text: str):
        sock = self.clients[client_id]['sock']
        sock.sendall(text.encode())


class RequestHandlerClass(StreamRequestHandler):
    def handle(self):
        while True:
            request_data = self.read_request()
            if not request_data:
                continue
            cmd = request_data['cmd']
            data = request_data['data']
            client_id = self.client_address[1]
            self.server.exec_client_cmd(client_id, cmd, data)

    def read_request(self):
        _bytes = []
        try:
            while self.connection.fileno() and not _bytes or _bytes[-1] != '\n':
                _byte = self.rfile.read(1)
                _bytes.append(_byte.decode())
            data = ''.join(_bytes)
            data = data.rstrip('\r\n')
            if not data:
                return
            body_length = int(data)
            body = self.rfile.read(body_length).decode()
            return json.loads(body)
        except Exception:
            pass


if __name__ == '__main__':
    srv = Server(('127.0.0.1', 12000), f'http://127.0.0.1:11000')
    srv.add_bot('evernotebot', 'bot_api_token')
    srv.serve_forever()
