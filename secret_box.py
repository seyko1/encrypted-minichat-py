import nacl.secret
import nacl.utils
import binascii

def secret_box_gen() -> tuple[nacl.secret.SecretBox, bytes]:
    secret_key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
    secret_box = nacl.secret.SecretBox(secret_key)

    return (secret_box, secret_key)

def secret_box_gen_by_key(secret_key: bytes) -> nacl.secret.SecretBox:
    secret_box = nacl.secret.SecretBox(secret_key)
    return secret_box

def encrypt(box: nacl.secret.SecretBox, msg: bytes):
    return box.encrypt(msg)

def decrypt(box: nacl.secret.SecretBox, enc_msg: bytes):
    return box.decrypt(enc_msg)

# Conversion de la clé de groupe chiffrée de int vers hexadécimal et vis versa...

def int_secret_key_to_hex(cipher: int) -> str:
    return hex(cipher)[2:]

def hex_secret_key_to_int(cipher: str) -> int:
    return int.from_bytes(binascii.unhexlify(cipher.encode("utf-8")), 'big')