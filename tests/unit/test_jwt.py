import unittest

from evernotebot.web.admin.jwt import (
    create_token, verify_token, JwtInvalidSignature
)


class TestJwt(unittest.TestCase):
    def test_token(self):
        payload = {
            "sid": "xxx",
        }
        token = create_token(payload, "secret")
        jwt_token = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJzaWQiOiAieHh4In0=.i6Wsev3NDhRY8Ao80A+zaaiVa3Nf+nuDihWuVlW4p2Y="
        self.assertEqual(token, jwt_token)
        header, payload = verify_token(token, "secret")
        self.assertEqual(header, {"alg": "HS256", "typ": "JWT"})
        self.assertEqual(payload, {"sid": "xxx"})
        with self.assertRaises(JwtInvalidSignature) as ctx:
            verify_token(token, "xxx")
        self.assertEqual(str(ctx.exception), jwt_token)
