import aiohttp_jinja2

from bot import DownloadTask
from bot.model import FailedUpdate


def list_downloads(request):
    downloads = [task.save_data() for task in DownloadTask.find()]
    response = aiohttp_jinja2.render_template('downloads.html',
                                              request,
                                              { 'list_downloads': downloads })
    return response


def list_failed_updates(request):
    failed_updates = [update.save_data() for update in FailedUpdate.find()]
    response = aiohttp_jinja2.render_template('failed_updates.html',
                                              request,
                                              { 'failed_updates': failed_updates })
    return response