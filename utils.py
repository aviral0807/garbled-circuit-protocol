from cryptography.fernet import Fernet


def encrypt(data, key):
    f = Fernet(key)
    return f.encrypt(data)


def decrypt(data, key):
    f = Fernet(key)
    return f.decrypt(data)


def get_label():
    return Fernet.generate_key()


def keys_to_int(x):
    return {int(k): v for k, v in x}
