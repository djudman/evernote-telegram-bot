from http import handle_request


def app(environ, start_response):
    status, response_headers, response_body = handle_request(environ)
    start_response(status, response_headers)
    return [response_body]
