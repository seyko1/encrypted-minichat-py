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
    def broadcast(self, entries: dict, sender = "server", target: str = "default", ignore: socket.socket = None):
        for client in self.groups[target]:
            if ignore is client:
                continue
            self.send_message(client, entries, sender, target)


    # Recevoir les messages de clients connectés
    def handle(self, client):
        while True:
            try:
                msg = common_lib.receive_message(client)
                content = msg["content"]
                sender = msg["sender"]
                target = msg["target"]
                self.broadcast({'content': content}, sender, target)
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                entries = {
                    "request": ServerAction.info,
                    "informations": f"{nickname} has left group"}
                self.broadcast(entries, target=target)
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
            entries_newMember = {
                "request": ServerAction.info,
                "informations": f"{nickname} joined the chat"}
            self.broadcast(entries_newMember, ignore=client)
            entries_port = {
                "request": ServerAction.info,
                "informations": "Connected to the server, port " + str(self.port)}
            self.send_message(client, entries_port)

            # SEND EXISTING GROUPS
            entries_groupsList = {
                "request": ServerAction.shareGroups,
                "groupsList": f"{list(self.groups.keys())}"}
            self.send_message(client, entries_groupsList)

            # GIVE ACCESS TO A GROUP DEFAULT
            entries_allowAccess = {
                "request": ServerAction.allowAccess,
                "groupName": "default"}
            self.send_message(client, entries_allowAccess)

            self.groups["default"].append(client)

            # ALLOW TO JOIN GROUP
            entries_joinGroup = {
                "request": ServerAction.joinGroup,
                "groupName": "default"}
            self.send_message(client, entries_joinGroup)

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(10)

        print("The server is ready.")
        self.receive()


    def send_message(self, client: socket.socket, entries: dict, sender = "server", target = ""):
        common_lib.send_message(client, sender, target, entries)



server = server_socket()
server.start()