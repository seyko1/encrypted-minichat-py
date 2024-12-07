import math
import binascii
from typing import TypeAlias
from Cryptodome.Util.number import getPrime

RsaKeypair: TypeAlias = tuple[tuple[int, int], tuple[int, int]]

# Prend en paramètre une taille de clé exprimée en bits, et renvoie une paire de clé publique/privée de cette taille
def gen_rsa_keypair(bits: int) -> RsaKeypair:
    size = bits // 2

    # Définir 2 grands nombres premiers distincts
    p = getPrime(size)
    q = getPrime(size)
    while p == q: q = getPrime(size)

    # Calculer le module de chiffrement n
    n = p * q 

    # Indicatrice d'Euler pour n
    phi_n = (p - 1) * (q - 1)
    
    # Exposant de chiffrement e (public)
    e = 65537

    # S'assurer que e soit bien premier avec p-1 et avec q-1
    assert((math.gcd(e, p - 1) == 1) and (math.gcd(e, q - 1) == 1))

    # Calcul de l'inverse modulaire de e % phi_n
    d = pow(e, -1, phi_n)

    return ((e, n), (d, n))

# Chiffrement de la clé de groupe à l'aide de l'exposant de chiffrement exp et du module de chiffrement n
# -> Retourne le chiffré en hexadécimal
def rsa_enc(key: bytes, exp: int, n: int) -> str:
  # Conversion de bytes vers un entier.
  m_int = int.from_bytes(key, 'big')

  if m_int >= n:
    raise ValueError("m must be lower to n.")
  
  cipher = rsa_exp(m_int, exp, n)
  bytes = cipher.to_bytes((cipher.bit_length() + 7) // 8, 'big')
  return binascii.hexlify(bytes).decode()

# Déchiffrement de la clé de groupe à l'aide de l'exposant de déchiffrement exp et du module de chiffrement n
# -> Retourne la clé déchiffrée en bytes
def rsa_dec(cipher: str, exp: int, n: int) -> bytes:
  int_cipher = int(cipher, 16)
  int_decipher = rsa_exp(int_cipher, exp, n)

  return int_decipher.to_bytes((int_decipher.bit_length() + 7) // 8, 'big')

# Exponentiation modulaire à partir d'un message m, d'un exposant exp et du module de chiffrement n
def rsa_exp(m: int, exp: int, n: int) -> int:
  return pow(m, exp, n)

# Conversion de la clé publique RSA de int vers hexadécimal et vis versa...

def int_rsa_key_to_hex(key: tuple[int, int]) -> tuple[str, str]:
  return tuple(hex(value)[2:] for value in key)

def hex_rsa_key_to_int(hex_key: tuple[str, str]) -> tuple[int, int]:
  return (int(hex_key[0], 16), int(hex_key[1], 16))