from hashlib import sha256
from random import SystemRandom

from cryptography.fernet import Fernet

crypto_rand = SystemRandom()


def encrypt(data, key):
    f = Fernet(key)
    return f.encrypt(data)


def decrypt(data, key):
    f = Fernet(key)
    return f.decrypt(data)


def get_label():
    return Fernet.generate_key().decode()


def hasher(b):
    return sha256(b).hexdigest()


def rand_int(n):
    return crypto_rand.randrange(n)
