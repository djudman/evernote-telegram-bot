from web.app import Application
from config import load_config


config = load_config()
webapp = Application(config)
webapp.bot.api.setWebhook(config['webhook_url'])


def app(environ, start_response):
    status, response_headers, response_body = webapp.handle_request(environ)
    start_response(status, response_headers)
    return [response_body]
