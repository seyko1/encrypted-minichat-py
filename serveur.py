import socket
import threading
from common_lib import ServerAction
import common_lib


class server_socket ():
    def __init__(self, host: str = "", port: int = 5555):
        self.host = host # localhost by default
        self.port = port # 5555 by default

        self.server: socket.socket = None

        self.groups: dict[str | socket.socket] = {"default": []}
        self.clients = []
        self.nicknames = []

    # Envoie un message à tous les clients du groupe ciblé
    def broadcast(self, msg, target: str = "default", ignore: socket.socket = None):
        for client in self.groups[target]:
            if ignore is client:
                continue
            self.send_message(client, msg)


    # Recevoir les messages de clients connectés
    def handle(self, client):
        while True:
            try:
                #get the size of the message
                message_lenght = int.from_bytes(client.recv(4), byteorder='big')
                #get the message
                msg = common_lib.decode_full_message(client.recv(message_lenght))
                content = msg["content"]
                sender = msg["sender"]
                target = msg["target"]
                self.broadcast(self.formate_message(content, sender, target), target)
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.broadcast(self.formate_message(f"{ServerAction.info}:::{nickname} has left group"))
                self.nicknames.remove(nickname)
                break

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}\n")

            #get the size of the message
            message_lenght = int.from_bytes(client.recv(4))
            #get the message
            msg = common_lib.decode_full_message(client.recv(message_lenght))
            nickname = msg["content"]
            self.nicknames.append(nickname)
            self.clients.append(client)
            print(f"Well hello {nickname}\n")
            self.broadcast(self.formate_message(f"{ServerAction.info}:::{nickname} joined the chat"), ignore=client)
            full_message = common_lib.encode_full_message(self.formate_message(f"{ServerAction.info}:::Connected to the server, port " + str(self.port)))
            #send the size of the message
            message_lenght = len(full_message)
            client.send(message_lenght.to_bytes(4, byteorder='big'))
            #send the message
            client.send(full_message)

            # SEND EXISTING GROUPS
            full_message = self.formate_message(f"{ServerAction.shareGroups}:::{list(self.groups.keys())}")
            self.send_message(client, full_message)

            # GIVE ACCESS TO A GROUP DEFAULT
            full_message = self.formate_message(f"{ServerAction.allowAccess}:::default")
            self.send_message(client, full_message)

            self.groups["default"].append(client)

            # ALLOW TO JOIN GROUP
            full_message = self.formate_message(f"{ServerAction.joinGroup}:::default")
            self.send_message(client, full_message)

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(10)

        print("The server is ready.")
        self.receive()


    def formate_message(self, msg, sender = "server", target = "") -> dict:
        full_message = {
            "content": msg,
            "sender" : sender,
            "target" : target,
        }
        return full_message
    

    # Protocole to send a message
    # It MUST be formated BEFORE this function
    def send_message(self, client: socket.socket, msg_formated: dict):
        #encode message
        encoded_msg = common_lib.encode_full_message(msg_formated)
        #send the size of the message
        message_lenght = len(encoded_msg)
        client.send(message_lenght.to_bytes(4, byteorder='big'))
        #send the message
        client.send(encoded_msg)



server = server_socket()
server.start()