import base64
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

def encrypt(box: nacl.secret.SecretBox, msg: str) -> str:
    enc = box.encrypt(msg.encode())

    assert len(enc) == len(msg) + box.NONCE_SIZE + box.MACBYTES

    return base64.b64encode(enc.nonce + enc.ciphertext).decode('utf-8') 

# déchiffrer un message chiffré et encodé en Base64
def decrypt(box: nacl.secret.SecretBox, enc_msg: str):
    dec_bytes = base64.b64decode(enc_msg)

    nonce = dec_bytes[:box.NONCE_SIZE]  # 24 premiers octets ?
    ciphertext = dec_bytes[box.NONCE_SIZE:]  # restant..

    if len(nonce) != box.NONCE_SIZE:
        raise ValueError("Nonce de taille incorrecte.")

    try:
        dec_msg = box.decrypt(ciphertext, nonce)
    except nacl.exceptions.CryptoError as e:
        raise nacl.exceptions.CryptoError(f"Erreur lors du déchiffrement : {e}")

    return dec_msg.decode()

# Conversion de la clé de groupe chiffrée de int vers hexadécimal et vis versa...

def int_secret_key_to_hex(cipher: int) -> str:
    return hex(cipher)[2:]

def hex_secret_key_to_int(cipher: str) -> int:
    return int.from_bytes(binascii.unhexlify(cipher.encode("utf-8")), 'big')