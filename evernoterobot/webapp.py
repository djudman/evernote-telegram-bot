import os

import json
import asyncio
from aiohttp import web

PROJECT_DIR = os.path.realpath(os.path.dirname(__file__))


async def handle_update(request):
    return web.Response(body=b"Hello, world")


with open(os.path.join(PROJECT_DIR, 'secret.json')) as f:
    data = json.load(f)

app = web.Application()
app.router.add_route('GET', '/%s' % data['token'], handle_update)
