import math
from Cryptodome.Util.number import getPrime

# Prend en paramètre une taille de clé exprimée en bits, et renvoie une paire de clé publique/privée de cette taille
def gen_rsa_keypair(bits):
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

# Chiffrement à l'aide du message à chiffrer m, de l'exposant de chiffrement exp et du module de chiffrement n
def rsa_enc(m, exp, n):
  # Conversion d'une chaine en bytes, puis en entier.
  m_int = int.from_bytes(m.encode("utf-8"), 'big')

  # Le message m doit être strictement inférieur à n.
  if m_int >= n:
    raise ValueError("m must be lower to n.")
  
  return rsa_exp(m_int, exp, n)

# Déchiffrement à l'aide du chiffré c, de l'exposant de déchiffrement exp et du module de chiffrement n
def rsa_dec(c, exp, n):
  m_int = rsa_exp(c, exp, n)

  # Conversion inverse d'un entier en chaine de caractère.
  m = m_int.to_bytes((m_int.bit_length() + 7) // 8, 'big').decode('utf-8')

  return m

# Exponentiation modulaire à partir d'un message m, d'un exposant exp et du module de chiffrement n
def rsa_exp(m, exp, n):
  return pow(m, exp, n)