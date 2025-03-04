import string
import random
import hashlib


def create_random_string(n: int = 10, digits: bool = False) -> str:
    """Генерирует случайную строку длиной N из букв и цифр"""
    symbols = string.digits
    if not digits:
        symbols += string.ascii_letters
    return ''.join([random.choice(symbols) for _ in range(n)])


def hash_password(password: str, salt: str) -> str:
    """Хеширует пароль"""
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 1000)


def verify_password(input_password, hashed, salt):
    """Проверяет совпадает ли пароль c хешем"""
    new_hash = hash_password(input_password, salt).hex()
    return new_hash == hashed
