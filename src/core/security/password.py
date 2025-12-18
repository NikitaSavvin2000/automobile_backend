from passlib.context import CryptContext
from passlib.exc import UnknownHashError

import os
from cryptography.fernet import Fernet
import base64
import hashlib
from dotenv import load_dotenv
import hmac
import hashlib
import os
load_dotenv()  # подгружаем .env


# Единый контекст хеширования паролей для всего сервиса
pwd_context = CryptContext(
    schemes=[
        "bcrypt",
    ],
    deprecated="auto",
)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
        Безопасно проверяет пароль
        Возвращает False, если хэш не распознан
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


SECRET_KEY = os.getenv("PASSWORD_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("PASSWORD_SECRET_KEY не задан в .env")


PASSWORD_SECRET_KEY = os.getenv("PASSWORD_SECRET_KEY")

if not PASSWORD_SECRET_KEY:
    raise RuntimeError("PASSWORD_SECRET_KEY не задан в .env")


def hash_password(password: str) -> str:
    return hmac.new(
        PASSWORD_SECRET_KEY.encode(),
        password.encode(),
        hashlib.sha256
    ).hexdigest()



def verify_password(password: str, hashed: str) -> bool:
    is_verify = hmac.compare_digest(
        hash_password(password),
        hashed
    )
    return is_verify