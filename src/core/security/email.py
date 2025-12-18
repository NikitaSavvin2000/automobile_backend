import os
from dotenv import load_dotenv
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Загружаем .env
load_dotenv()

KEY = os.environ.get("EMAIL_ENCRYPT_KEY")
if not KEY:
    raise ValueError("Не найден EMAIL_ENCRYPT_KEY")
key_bytes = base64.urlsafe_b64decode(KEY)[:32]

def encrypt_email(email: str) -> str:
    cipher = Cipher(algorithms.AES(key_bytes), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    pad_len = 16 - (len(email.encode()) % 16)
    padded = email.encode() + bytes([pad_len]*pad_len)
    ct = encryptor.update(padded) + encryptor.finalize()
    return base64.urlsafe_b64encode(ct).decode()

def decrypt_email(token: str) -> str:
    cipher = Cipher(algorithms.AES(key_bytes), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(base64.urlsafe_b64decode(token)) + decryptor.finalize()
    pad_len = padded[-1]
    return padded[:-pad_len].decode()



def test_encrypt_email_deterministic():
    email = "Admin@yandex.ru"
    encrypted1 = encrypt_email(email)
    encrypted2 = encrypt_email(email)
    assert encrypted1 == encrypted2, "Результаты шифрования не совпадают!"
    decrypted = decrypt_email(encrypted1)
    assert decrypted == email, "Дешифрование не вернуло исходный email!"
    print("Тест пройден: шифрование детерминированное, дешифрование верное.")
    print(encrypted1)
    print(encrypted2)
    print(decrypted)


if __name__ == "__main__":
    test_encrypt_email_deterministic()
