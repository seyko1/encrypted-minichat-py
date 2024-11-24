import socket
import threading
from common_lib import ServerAction, EntryForFormatedMessage
import common_lib
from typing import Optional


class Client ():
    def __init__(self, nickname: str, socket: socket.socket):
        self.nickname = nickname
        self.socket = socket

    @staticmethod
    def get_client(nickname: str, clientsList: list[Optional['Client']]) -> Optional['Client']:
        for client in clientsList:
            if client.nickname == nickname:
                return client
        
        # should not happen
        return None


class server_socket ():
    def __init__(self, host: str = "", port: int = 5555):
        self.host = host # localhost by default
        self.port = port # 5555 by default

        self.server: socket.socket = None

        self.groups: dict[str | Client] = {"default": []}
        self.clients: list[Client] = []

    # Envoie un message à tous les clients du groupe ciblé
    def broadcast(self, entries: dict, sender = "server", target: str = "default", ignore: socket.socket = None):
        for client in self.groups[target]:
            if ignore is client.socket:
                continue
            self.send_message(client.socket, entries, sender, target)


    # Recevoir les messages de clients connectés
    def handle(self, client: Client):
        while True:
            try:
                msg = common_lib.receive_message(client.socket)
                content = msg[EntryForFormatedMessage.content]
                sender = msg[EntryForFormatedMessage.sender]
                target = msg[EntryForFormatedMessage.target]

                if target == 'server':
                    self.handle_action_from_client(msg)
                else:
                    self.broadcast({EntryForFormatedMessage.content: content}, sender, target)

            except:
                self.clients.remove(client)
                client.socket.close()
                entries = {
                    EntryForFormatedMessage.action: ServerAction.info,
                    EntryForFormatedMessage.content: f"{client.nickname} has left group"}
                self.broadcast(entries, target=target)
                break

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}\n")

            msg = common_lib.receive_message(client)
            nickname = msg[EntryForFormatedMessage.content]
            client = Client(nickname, client)

            self.clients.append(client)
            print(f"Well hello {nickname}\n")

            # SEND EXISTING GROUPS
            entries_groupsList = {
                EntryForFormatedMessage.action: ServerAction.shareGroups,
                EntryForFormatedMessage.groupsList: f"{list(self.groups.keys())}"}
            self.send_message(client.socket, entries_groupsList)

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()


    def handle_action_from_client(self, message: dict):
        action = message[common_lib.EntryForFormatedMessage.action]

        match action:
            case _:
                print(f"Client tried this action: [{action}], but as no effect, because is undefined.")


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