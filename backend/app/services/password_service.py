import hashlib
import secrets


def hash_password(plain_password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f'{salt}:{plain_password}'.encode('utf-8')).hexdigest()
    return f'{salt}${digest}'


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash or '$' not in password_hash:
        return False
    salt, digest = password_hash.split('$', 1)
    check = hashlib.sha256(f'{salt}:{plain_password}'.encode('utf-8')).hexdigest()
    return secrets.compare_digest(check, digest)
