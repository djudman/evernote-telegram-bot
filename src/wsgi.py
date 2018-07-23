from app import Application
from config import ConfigLoader


config = ConfigLoader().load()
webapp = Application(config)

def app(environ, start_response):
    status, response_headers, response_body = webapp.handle_request(environ)
    start_response(status, response_headers)
    return [response_body]
