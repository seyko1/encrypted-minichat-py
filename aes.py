import binascii
from Cryptodome.Random import get_random_bytes

# Renvoie une clé d'une taille de 256 bits pour le chiffrement AES
def gen_aes256_key():
    key = get_random_bytes(32)
    return key

# Convertit la clé binaire en une chaîne hexadécimale (à chiffrer)
def encode_key_to_hex(bytes):
    hexkey = binascii.hexlify(bytes).decode()
    return hexkey

# Reconvertit la chaîne hexadécimale en clé binaire (après déchiffrement)
def decode_hex_to_bytes(hex):
    bytes_key = binascii.unhexlify(hex)
    return bytes_key