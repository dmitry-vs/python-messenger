import hashlib
from os import urandom
import hmac

from helpers import bytes_to_hexstring, hexstring_to_bytes

HASH_ALGORITHM = 'sha256'
HASH_SALT = b'\xca\xfe\xbe\xef\xca\xfe\xbe\xef\xca\xfe\xbe\xef\xca\xfe\xbe\xef\xca\xfe\xbe\xef\xca\xfe\xbe\xef'
HASH_ITERATIONS = 100000
AUTH_TOKEN_LEN = 16


def create_password_hash(password: str) -> str:
    if not password:
        raise RuntimeError('password value empty or incorrect')
    digest = hashlib.pbkdf2_hmac(HASH_ALGORITHM, password.encode('utf-8'), HASH_SALT, HASH_ITERATIONS)
    return bytes_to_hexstring(digest)


def create_auth_token() -> str:
    return bytes_to_hexstring(urandom(AUTH_TOKEN_LEN))


def create_auth_digest(secret: str, token: str) -> str:
    if not secret or not token:
        raise RuntimeError('secret or token value empty or incorrect')
    digest = hmac.new(hexstring_to_bytes(secret), hexstring_to_bytes(token)).digest()
    return bytes_to_hexstring(digest)


def check_auth_digest_equal(digest_1: str, digest_2: str) -> bool:
    return hmac.compare_digest(digest_1, digest_2)
