import unittest
import tempfile

from uhttp import Request

from evernotebot.wsgi import create_app, telegram_hook


class TestWsgi(unittest.TestCase):
    def test_telegram_hook_failed(self):
        app = create_app()
        data = b'{"test": "test"}'
        with tempfile.NamedTemporaryFile(mode="rb+", suffix=".txt",
                                         dir="/tmp") as wsgi_input:
            wsgi_input.write(data)
            wsgi_input.seek(0, 0)
            request = Request({
                'wsgi.input': wsgi_input,
                'CONTENT_LENGTH': len(data),
            })
            request.app = app
            telegram_hook(request)
