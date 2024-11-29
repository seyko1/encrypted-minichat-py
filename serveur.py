import socket
import threading
from common_lib import ServerAction, ClientAction, EntryForFormatedMessage
import common_lib
from typing import Optional



class Client ():
    counter = 0

    def __init__(self, socket: socket.socket):
        self.id = Client.generate_unique_id()
        self.nickname:str = self.id
        self.public_key: tuple[str, str] = None
        self.socket = socket
    

    def __str__(self) -> str:
        id = self.id
        n = self.nickname
        key = self.public_key
        sckt = 'Have one' if self.socket else None
        return f'id:{id}, name:{n}, sckt:{sckt}, key:{key}'


    @staticmethod
    def generate_unique_id() -> str:
        Client.counter += 1
        return f'__{Client.counter}'


    @staticmethod
    def get_client(nickname: str, clientsList: list[Optional['Client']]) -> Optional['Client']:
        for client in clientsList:
            if client.nickname == nickname:
                return client
        
        # should not happen
        return None


    def update_data(self, nickname: str = None, public_key: tuple[str, str] = None, socket: socket.socket = None) -> None:
        if nickname:
            self.nickname = nickname
        if public_key:
            self.public_key = public_key
        if socket:
            self.socket = socket



class server_socket ():
    def __init__(self, host: str = "", port: int = 5555):
        self.host = host # localhost by default
        self.port = port # 5555 by default

        self.server: socket.socket = None

        self.groups: dict[str | Client] = {"default": [], "L3B": [], "Les Monsieurs": [], "Les madames": []}
        self.clients: list[Client] = []


    def show_clients(self):
        for i, client in enumerate(self.clients, 1):
            print(f'{i:>3} | {client}')


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
                target = msg[EntryForFormatedMessage.target]

                if target == 'server':
                    self.handle_action_from_client(msg)
                else:
                    content = msg[EntryForFormatedMessage.content]
                    sender = msg[EntryForFormatedMessage.sender]
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
            socket, address = self.server.accept()
            print(f"Connected with {str(address)}\n")

            new_client = Client(socket)
            self.clients.append(new_client)

            thread = threading.Thread(target=self.handle, args=(new_client,))
            thread.start()

            #send a temporary nickname
            tempNickname = new_client.id
            giveTempNickname = {
                EntryForFormatedMessage.action: ServerAction.giveTempNickname,
                EntryForFormatedMessage.nickname: tempNickname
            }
            self.send_message(new_client.socket, giveTempNickname)


    def handle_action_from_client(self, message: dict):
        action = message[EntryForFormatedMessage.action]

        match action:
            case ClientAction.requestConnection:
                sender = message[EntryForFormatedMessage.sender]
                public_key = message[EntryForFormatedMessage.public_key]
                nickname = message[EntryForFormatedMessage.nickname]
                client_connecting = Client.get_client(sender, self.clients)

                #valideConnection
                client_connecting.update_data(nickname, public_key)

                #confirme connection, and share groups list
                acceptConnection = {
                    EntryForFormatedMessage.action: ServerAction.acceptConnection,
                    EntryForFormatedMessage.nickname: nickname,
                    EntryForFormatedMessage.groupsList: f"{list(self.groups.keys())}"
                }
                self.send_message(client_connecting.socket, acceptConnection)

            case ClientAction.requestJoinGroup:
                groupName = message[EntryForFormatedMessage.groupName]

                ## TODO
                ##
                ## must add the protocole to give the key of the group here
                ##

                ## Here's the protocole without the key.
                ## Must be changed.
                senderName = message[EntryForFormatedMessage.sender]
                groupMembers: list[Client] = self.groups[groupName]

                # determine if the client is already a member
                isInGroup = False
                for client in groupMembers:
                    nickname = client.nickname
                    if nickname == senderName:
                        isInGroup = True
                        break
                
                client = Client.get_client(senderName, self.clients)
                #prepare the message to the group
                msg = ''
                if isInGroup:
                    msg = f'{senderName} has rejoin'
                else:
                    self.groups[groupName].append(client)
                    msg = f'{senderName} has join'

                #broadcast that client has join
                joinMessage = {
                    EntryForFormatedMessage.action: ServerAction.info,
                    EntryForFormatedMessage.content: msg
                    }
                self.broadcast(joinMessage, target = groupName, ignore=client.socket)

                #make the client join the group
                makeJoin = {
                    EntryForFormatedMessage.action: ServerAction.joinGroup,
                    EntryForFormatedMessage.groupName: groupName}
                self.send_message(client.socket, makeJoin)

                ## Must be changed.

            case ClientAction.requestAddGroup:
                groupName = message[EntryForFormatedMessage.groupName]

                # check if it exist
                for group in list(self.groups.keys()):
                    if group == groupName:
                        return
                
                #create the group
                self.groups[groupName] = []
                
                #broadcast all the groups
                groupsListUpdate = {
                    EntryForFormatedMessage.action: ServerAction.shareGroups,
                    EntryForFormatedMessage.groupsList: f"{list(self.groups.keys())}"}
                
                for client in self.clients:
                    self.send_message(client.socket, groupsListUpdate)

            case ClientAction.requestLeaveGroup:
                groupName = message[EntryForFormatedMessage.groupName]
                senderName = message[EntryForFormatedMessage.sender]
                client = Client.get_client(senderName, self.clients)

                #remove client
                self.groups[groupName].remove(client)
                leaveGroup = {
                    EntryForFormatedMessage.action: ServerAction.leaveGroup,
                    EntryForFormatedMessage.groupName: groupName}
                self.send_message(client.socket, leaveGroup)

                #broadcast that someone leave
                clientHasLeave = {
                    EntryForFormatedMessage.action: ServerAction.info,
                    EntryForFormatedMessage.content: f'{senderName} has leave'}
                self.broadcast(clientHasLeave, target=groupName)


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