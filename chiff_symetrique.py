import nacl.secret
import nacl.utils


def gen_key_sym():
  secret_key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
  box = nacl.secret.SecretBox(secret_key)
  return (secret_key,box)

def encrypt(msg,box):
  enc_msg = box.encrypt(msg.encode('utf-8'))
  return enc_msg

def decrypt(enc_msg,box):
  dec_msg = box.decrypt(enc_msg)
  return dec_msg