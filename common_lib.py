import json


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
