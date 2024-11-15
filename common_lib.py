import json
import socket


class ServerAction:
    info = "information"
    allowAccess = "give permission to access the given group" #this will allow to create private group later
    joinGroup = "join the given group"
    shareGroups = "give a list of existing groups"
# To perform an action, the server must send a message as the sender,
# which the "content" must followed the format:
# => "action:::content of the action"


def encode_full_message(msg: dict) -> bytes:
    dictToStr = json.dumps(msg)
    return dictToStr.encode('utf-8')


def decode_full_message(msg: bytes) -> dict:
    bytesToStr = msg.decode('utf-8')
    return json.loads(bytesToStr)


def formate_message(msg, sender, target) -> dict:
    full_message = {
        "content": msg,
        "sender" : sender,
        "target" : target,
    }
    return full_message


# Protocole to send a message
# It MUST be formated BEFORE this function
def send_message(sckt: socket.socket, message, sender, target):
    if not sckt:
        return

    try:
        #formate message
        msg_formated = formate_message(message, sender, target)
        #encode message
        encoded_msg = encode_full_message(msg_formated)
        #send the size of the message
        message_lenght = len(encoded_msg)
        sckt.send(message_lenght.to_bytes(4, byteorder='big'))
        #send the message
        sckt.send(encoded_msg)

    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")
