import nacl.secret
import nacl.utils
import binascii

def secret_box_gen(secret_key: bytes = None):
    if not secret_key:
        secret_key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)

    box = nacl.secret.SecretBox(secret_key)

    hexkey = key_to_hex(secret_key)

    return (box, hexkey)

def encrypt(box: nacl.secret.SecretBox, msg: bytes):
    return box.encrypt(msg)

def decrypt(box: nacl.secret.SecretBox, enc_msg: bytes):
    return box.decrypt(enc_msg)

def key_to_hex(key):
    return binascii.hexlify(key).decode()

def hexkey_to_bytes(hexkey: str):
    return binascii.unhexlify(hexkey)