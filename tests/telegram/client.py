import json
import sys
import socket
import threading
from queue import Queue, Empty
from time import sleep

from tests.telegram.models import User


class BotClient:
    def __init__(self, server_host: str = '127.0.0.1', server_port: int = 12000):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_addr = (server_host, server_port)
        sock.connect(server_addr)
        self.sock = sock
        self.selected_chat = None
        self.user = None
        self.chats = None
        self.alive = True
        self.reader = threading.Thread(target=self.reader)
        self.queue = Queue()

    def run(self):
        try:
            self.reader.start()
            response = self.send_cmd('enter')
            self.user = response['user']
            self.chats = response['chats']
            self.loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.alive = False
            self.sock.close()

    def reader(self):
        while self.alive:
            self.read_response()
            sleep(0.5)
            try:
                response = self.queue.get_nowait()
                print(f'response = {response}')
            except Empty:
                pass

    def select_chat(self):
        while True:
            chats = list(self.chats.values())
            for i, chat in enumerate(chats):
                user = User(**chat['user'])
                print(f'{i + 1}. {user.title}')
            print('\nType number of selected chat and press `Enter`: ', end='')
            line = sys.stdin.readline().strip()
            if not line or not line.isdecimal():
                continue
            index = int(line) - 1
            if len(chats) <= index:
                continue
            self.selected_chat = chats[index]
            break

    def loop(self):
        self.select_chat()
        user = User(**self.selected_chat['user'])
        motd = f'\r{user.title} >>>'
        while True:
            print(motd, end=' ')
            line = sys.stdin.readline().strip()
            if not line:
                continue
            text = line.strip().lower()
            if text == 'exit':
                break
            self.send_cmd('message', {'chat_id': self.selected_chat['chat_id'], 'text': text})

    def send_cmd(self, cmd: str, data: dict = None):
        data = data or {}
        body = json.dumps({'cmd': cmd, 'data': data})
        body_size = len(body)
        message = f'{body_size}\n{body}\n'
        print(f'[client send request] >>> `{message}`')
        self.sock.sendall(message.encode())
        response = self.queue.get()
        print(f'[client got response] <<< `{response}`')
        return response

    def read_response(self):
        _bytes = []
        max_buf_size = 1024 * 1024
        try:
            while not _bytes or _bytes[-1] != '\n' and len(_bytes) <= max_buf_size:
                _byte = self.sock.recv(1)
                _bytes.append(_byte.decode())
            data = ''.join(_bytes)
            data = data.rstrip('\r\n')
            if not data:
                return
            body_length = int(data)
            body = self.sock.recv(body_length).decode()
            self.queue.put(json.loads(body))
        except Exception as e:
            print(e)

    def recv_message(self):
        pass
