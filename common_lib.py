import json
import socket



class ServerAction:
    error = "error"
    acceptConnection = "acceptConnection"
    info = "info"               #give data supposed to be shown in the chat
    giveTempNickname = "giveTempNickname"
    joinGroup = "joinGroup"     #allow the client to join a group
    leaveGroup = "leaveGroup"
    shareGroups = "shareGroups" #give the existing groups to the client
# To perform an action, the server must send a message as the sender,
# which the "content" must followed the format:
# => "action:::content of the action"


class ClientAction:
    requestConnection = 'requestConnection'
    sharePublicKey = 'sharePublicKey'
    requestJoinGroup = "requestJoinGroup"
    requestAddGroup = "requestAddGroup"
    requestLeaveGroup = "requestLeaveGroup"


class EntryForFormatedMessage:
    sender = 'sender'
    target = 'target'
    content = 'content'        #basic content, usually message between clients
    action = 'action'          #type of a request or an action
    errorType = 'errorType'
    nickname = 'nickname'
    public_key = 'public_key'
    groupsList = 'groupsList'  #a list a group
    groupName = 'groupName'    #name of a specific group


class ErrorType:
    nicknameTaken = "nicknameTaken"
    groupNameTaken = "groupNameTaken"


def encode_full_message(msg: dict) -> bytes:
    dictToStr = json.dumps(msg)
    return dictToStr.encode('utf-8')


def decode_full_message(msg: bytes) -> dict:
    bytesToStr = msg.decode('utf-8')
    return json.loads(bytesToStr)


def formate_message(sender, target, entries: dict = {}) -> dict:
    full_message = {
        EntryForFormatedMessage.sender : sender,
        EntryForFormatedMessage.target : target,
    }

    for entry, value in entries.items():
        full_message[entry] = value

    return full_message


# Protocole to send a message
# It MUST be formated BEFORE this function
def send_message(sckt: socket.socket, sender, target, entries: dict = {}):
    if not sckt:
        return

    try:
        #formate message
        msg_formated = formate_message(sender, target, entries)
        #encode message
        encoded_msg = encode_full_message(msg_formated)
        #send the size of the message
        message_lenght = len(encoded_msg)
        sckt.send(message_lenght.to_bytes(4, byteorder='big'))
        #send the message
        sckt.send(encoded_msg)

    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")


def receive_message(sckt: socket.socket) -> dict:
    #get the size of the message
    message_lenght = int.from_bytes(sckt.recv(4), byteorder='big')
    #get the message
    message = decode_full_message(sckt.recv(message_lenght))
    print()
    print("Message received")
    for key, value in message.items():
        print(f'{key}: {value}')
    return message
