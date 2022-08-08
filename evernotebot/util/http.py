import ssl
from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlencode, urlparse


def make_request(url, method='GET', params=None, body=None, headers=None):
    parse_result = urlparse(url)
    protocol = parse_result.scheme
    hostname = parse_result.netloc
    port = None
    if ':' in hostname:
        hostname, port = hostname.split(':')
    if protocol == 'https':
        context = ssl.SSLContext()
        conn = HTTPSConnection(hostname, port, context=context)
    elif protocol == 'http':
        conn = HTTPConnection(hostname, port)
    else:
        raise Exception('Unsupported protocol {}'.format(protocol))
    if headers is None:
        headers = {}
    if method == 'POST':
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if params and not body:
            body = urlencode(params)
    request_url = f'{parse_result.path}?{parse_result.query}'
    conn.request(method, request_url, body, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return data
