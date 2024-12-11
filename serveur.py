import socket
import threading
from common_lib import ServerAction, ClientAction, EntryForFormatedMessage, ErrorType
import common_lib
from typing import Optional



class Client ():
    counter = 0

    def __init__(self, socket: socket.socket):
        self.id = Client.generate_unique_id()
        self.nickname:str = self.id
        self.public_key: tuple[str, str] = None
        self.socket = socket
        self.connected = True
        self.pending_messages = {} #key = group name, value = list of messages
    

    def __str__(self) -> str:
        id = self.id
        n = self.nickname
        key = self.public_key
        sckt = 'Have one' if self.socket else None
        pending_msgs = list(self.pending_messages.items()) if self.pending_messages else None
        connected = 'O' if self.connected else 'X'
        return f'{connected} id:{id}, name:{n}, sckt:{sckt}, key:{key}, waiting_msg:{pending_msgs}'


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
    def __init__(self, host: str = common_lib.HOST, port: int = common_lib.PORT):
        self.host = host # localhost by default
        self.port = port # 5555 by default

        self.server: socket.socket = None

        self.groups: dict[str | Client] = {"L3B": []}
        self.clients: list[Client] = []
        # dictionnaire pour garder les callbacks par groupe
        self.group_key_response_callbacks = {}


    def show_clients(self):
        for i, client in enumerate(self.clients, 1):
            print(f'{i:>3} | {client}')


    # Envoie un message à tous les clients du groupe ciblé
    def broadcast(self, entries: dict, sender = "server", target: str = "default", ignore: socket.socket = None):
        for client in self.groups[target]:
            if ignore is client.socket:
                continue
            if not client.connected:
                client.pending_messages.setdefault(target, []).append(entries)
                continue

            self.send_message(client.socket, entries, sender, target)


    # Recevoir les messages de clients connectés
    def handle(self, client: Client):
        while client.connected:
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
                client.connected = False
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

            self.show_clients()


    def handle_action_from_client(self, message: dict):
        action = message[EntryForFormatedMessage.action]

        match action:
            case ClientAction.requestConnection:
                sender = message[EntryForFormatedMessage.sender]
                public_key = message[EntryForFormatedMessage.publicKey]
                nickname = message[EntryForFormatedMessage.nickname]
                client_connecting = Client.get_client(sender, self.clients)

                #search for client with the same nickname
                firstConnection = True
                for client in self.clients:
                    if nickname == client.nickname:
                        firstConnection = False
                
                #valideConnection
                if firstConnection:
                    client_connecting.update_data(nickname, public_key)

                    #confirme connection, and share groups list
                    acceptConnection = {
                        EntryForFormatedMessage.action: ServerAction.acceptConnection,
                        EntryForFormatedMessage.nickname: nickname,
                        EntryForFormatedMessage.groupsList: f"{list(self.groups.keys())}"
                    }
                    self.send_message(client_connecting.socket, acceptConnection)
                    self.show_clients()
                
                #valide reconnection
                else:
                    existing_account = Client.get_client(nickname, self.clients)
                    #already connected
                    if existing_account.connected:
                        refuseConnection = {
                            EntryForFormatedMessage.action: ServerAction.error,
                            EntryForFormatedMessage.errorType: ErrorType.alreadyConnected
                        }
                        self.send_message(client_connecting.socket, refuseConnection)
                        return

                    # update the existing account with the temporary data of the joining client
                    rejoining_client = Client.get_client(sender, self.clients)
                    existing_account.update_data(nickname, public_key, rejoining_client.socket)
                    existing_account.connected = True

                    self.clients.remove(rejoining_client)

                    #TODO: Il faut aussi envoyer les messages en attentes
                    acceptReconnection = {
                        EntryForFormatedMessage.action: ServerAction.acceptReconnection,
                        EntryForFormatedMessage.nickname: nickname,
                        EntryForFormatedMessage.groupsList: f"{list(self.groups.keys())}"
                    }
                    self.send_message(client_connecting.socket, acceptReconnection)
                    self.show_clients()

            case ClientAction.requestJoinGroup:
                group_name = message[EntryForFormatedMessage.groupName]
                requester_name = message[EntryForFormatedMessage.sender]
                
                self.join_group(requester_name, group_name)

            case ClientAction.requestAddGroup:
                group_name = message[EntryForFormatedMessage.groupName]
                creator_name = message[EntryForFormatedMessage.sender]

                # check if the group name already exists
                if group_name in self.groups:
                    group_name_taken = {             
                        EntryForFormatedMessage.action: ServerAction.error,
                        EntryForFormatedMessage.errorType: ErrorType.groupNameTaken,
                        EntryForFormatedMessage.groupName: group_name
                    }
                    self.send_message(client.socket, group_name_taken)
                    return

                self.add_group(group_name, creator_name)

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

            case ClientAction.shareGroupKey:
                group_name = message[EntryForFormatedMessage.groupName]                
                nickname, groupKey = message[EntryForFormatedMessage.groupKey]

                # retrouver le client pour qui la clé est destinée
                target_client = Client.get_client(nickname, self.clients)

                # faire appel à la fonction de callback correspondant au groupe dans le dictionnaire key_response_callbacks
                # lors d'une prochaine demande pour rejoindre le groupe [group_name] : un nouveau callback écrasera l'ancien dans le dictionnaire
                callback = self.group_key_response_callbacks[group_name]
                callback(groupKey, target_client)

            case ClientAction.requestDisconnection:
                sender = message[EntryForFormatedMessage.sender]
                client = Client.get_client(sender, self.clients)
                client.connected = False

                disconnect = {
                    EntryForFormatedMessage.action: ServerAction.disconnect}
                self.send_message(client.socket, disconnect)

                client.socket.close()
                self.broadcast_deconnection(client)

                self.handle_admin_deconnection(client)

                self.show_clients()

            case _:
                print(f"Client tried this action: [{action}], but as no effect, because is undefined.")


    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(10)

        print("The server is ready.")
        self.show_clients()
        self.receive()


    def send_message(self, client: socket.socket, entries: dict, sender = "server", target = ""):
        common_lib.send_message(client, sender, target, entries)


    def add_group(self, group_name: str, creator_name: str):
        client = Client.get_client(creator_name, self.clients)

        # create the group with his creator
        self.groups[group_name] = [client]

        # make the creator join the group
        makeJoin = {
            EntryForFormatedMessage.action: ServerAction.joinGroup,
            EntryForFormatedMessage.groupName: group_name}
        self.send_message(client.socket, makeJoin)
        
        # broadcast all the groups
        share_groups = {
            EntryForFormatedMessage.action: ServerAction.shareGroups,
            EntryForFormatedMessage.groupsList: f"{list(self.groups.keys())}"
        }

        for client in self.clients:
            self.send_message(client.socket, share_groups)
    
    # enregistrer une fonction de rappel lors d'une demande de clé de groupe
    def register_callback_for_groupkey_response(self, group_name: str, callback: callable):
        # enregistrer le callback pour un groupe donné
        self.group_key_response_callbacks[group_name] = callback

    # transmets la clé de groupe envoyé par l'admin vers le client à l'origine de la demande
    def handle_key_from_admin(self, group_key: str, client: Client, group_name: str):
        print(f'callback de partage de clé pour le groupe {group_name} !')
        print(f'clé de groupe reçue : {group_key}')
        print(f'client à l\'origine de la demande : {client.nickname}')

        # ajouter le client à l'origine de la demande parmi les membres du groupe
        group = self.groups[group_name]
        already_in_group = any(member.nickname == client.nickname for member in group)

        if not already_in_group:
            self.groups[group_name].append(client)

        # broadcast that client has join
        broadcast_msg = {
            EntryForFormatedMessage.action: ServerAction.info,
            EntryForFormatedMessage.content: f'{client.nickname} has join'
        }
        self.broadcast(broadcast_msg, target = group_name, ignore=client.socket)

        # make the client join the group with group key
        make_join_msg = {
            EntryForFormatedMessage.action: ServerAction.joinGroup,
            EntryForFormatedMessage.groupName: group_name,
            EntryForFormatedMessage.groupKey: group_key
        }
        self.send_message(client.socket, make_join_msg)


    def join_group(self, requester_name: str, group_name: str):
        client = Client.get_client(requester_name, self.clients)
        members: list[Client] = self.groups[group_name]

        # return an error if a participant requests to join an empty group
        if not members:
            self.send_message(client.socket, {             
                EntryForFormatedMessage.action: ServerAction.error,
                EntryForFormatedMessage.errorType: ErrorType.emptyGroup
            })
            return
            
        # determine if the client is already a member
        in_group = any(member.nickname == requester_name for member in members)


        admin = members[0]
        keyRequester = (client.nickname, client.public_key)

        # envoyer une requete à l'admin pour demande la clé de groupe
        self.send_message(admin.socket, {
            EntryForFormatedMessage.action: ServerAction.requestKey,
            EntryForFormatedMessage.groupName: group_name,
            EntryForFormatedMessage.keyRequester: keyRequester
        })

        # enregistrer une fonction de rappel pour traiter la réponse de l'admin
        self.register_callback_for_groupkey_response(
            group_name,
            lambda key, client : self.handle_key_from_admin(key, client, group_name)
        )

    def handle_admin_deconnection(self, client: Client):
        # vérifie si le client déconnecté est l'admin (index 0) dans un groupe et le déplace à la fin de la liste.
        for group_name, members in self.groups.items():
            if members and members[0] == client:
                members.append(members.pop(0))  # déplacer l'admin à la fin du groupe

                broadcast_admin_changed = {
                    EntryForFormatedMessage.action: ServerAction.info,
                    EntryForFormatedMessage.content: f"{client.nickname} n'est plus admin du groupe."
                }
                self.broadcast(broadcast_admin_changed, target=group_name, ignore=client.socket)

    def broadcast_deconnection(self, client: Client):
        # parcourir les groupes auxquels appartient le client
        for group_name, members in self.groups.items():
            if client in members:
                # diffuser uniquement aux membres de ce groupe
                entries = {
                    EntryForFormatedMessage.action: ServerAction.info,
                    EntryForFormatedMessage.content: f"{client.nickname} left group."
                }
                self.broadcast(entries, target=group_name, ignore=client.socket)

server = server_socket()
server.start()