import hmac
import json
import base64


class JwtInvalidSignature(Exception):
    pass


def create_token(payload: dict, secret: str):
    header = json.dumps({
        "alg": "HS256",
        "typ": "JWT",
    })
    payload = json.dumps(payload)
    token = "{b64_header}.{b64_payload}".format(
        b64_header=base64.b64encode(header.encode()).decode(),
        b64_payload=base64.b64encode(payload.encode()).decode(),
    )
    signature = hmac.new(secret.encode(), token.encode(), "sha256").digest()
    return "{token}.{b64_signature}".format(token=token,
        b64_signature=base64.b64encode(signature).decode())


def verify_token(token: str, secret: str):
    _token, signature = token.rsplit(".", 1)
    signature = base64.b64decode(signature)
    expected_signature = hmac.new(secret.encode(), _token.encode(), "sha256").digest()
    if signature != expected_signature:
        raise JwtInvalidSignature(token)
    header, payload = _token.split(".")
    header = json.loads(base64.b64decode(header))
    payload = json.loads(base64.b64decode(payload))
    return header, payload

