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
    def broadcast(self, msg, sender = "server", target: str = "default", ignore: socket.socket = None):
        for client in self.groups[target]:
            if ignore is client:
                continue
            self.send_message(client, msg, sender, target)


    # Recevoir les messages de clients connectés
    def handle(self, client):
        while True:
            try:
                msg = common_lib.receive_message(client)
                content = msg["content"]
                sender = msg["sender"]
                target = msg["target"]
                self.broadcast(content, sender, target)
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.broadcast(f"{ServerAction.info}:::{nickname} has left group", target=target)
                self.nicknames.remove(nickname)
                break

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}\n")

            msg = common_lib.receive_message(client)
            nickname = msg["content"]
            self.nicknames.append(nickname)
            self.clients.append(client)
            print(f"Well hello {nickname}\n")
            self.broadcast(f"{ServerAction.info}:::{nickname} joined the chat", ignore=client)
            self.send_message(client, f"{ServerAction.info}:::Connected to the server, port " + str(self.port))

            # SEND EXISTING GROUPS
            self.send_message(client, f"{ServerAction.shareGroups}:::{list(self.groups.keys())}")

            # GIVE ACCESS TO A GROUP DEFAULT
            self.send_message(client, f"{ServerAction.allowAccess}:::default")

            self.groups["default"].append(client)

            # ALLOW TO JOIN GROUP
            self.send_message(client, f"{ServerAction.joinGroup}:::default")

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(10)

        print("The server is ready.")
        self.receive()


    def formate_message(self, msg, sender = "server", target = "") -> dict:
        return common_lib.formate_message(msg, sender, target)
    

    def send_message(self, client: socket.socket, msg, sender = "server", target = ""):
        common_lib.send_message(client, msg, sender, target)



server = server_socket()
server.start()