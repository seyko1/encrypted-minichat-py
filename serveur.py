import socket
import threading

class server_socket ():
    def __init__(self, host: str = "", port: int = 5555):
        self.host = host # localhost by default
        self.port = port # 5555 by default

        self.server: socket.socket = None

        self.clients = []
        self.nicknames = []

    # Envoie un message à tous les clients connectés
    def broadcast(self, msg):
        encoded_msg = self.encode_full_message(msg)
        for client in self.clients:
            client.send(encoded_msg)

    # Recevoir les messages de clients connectés
    def handle(self, client):
        while True:
            try:
                msg = self.decode_full_message(client.recv(1024))
                self.broadcast(msg)
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.broadcast(f"{nickname} has left the chat\n")
                self.nicknames.remove(nickname)
                break

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}\n")

            nickname = self.decode_full_message(client.recv(1024))
            self.nicknames.append(nickname)
            self.clients.append(client)
            print(f"Well hello {nickname}\n")
            self.broadcast(f"{nickname} just joined the chat.\n")
            client.send((self.encode_full_message("Connected to the server, port " + str(self.port))))

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(10)

        print("The server is ready.")
        self.receive()


    def encode_full_message(self, msg: str) -> bytes:
        return msg.encode('utf-8')
    

    def decode_full_message(self, msg: bytes) -> str:
        return msg.decode('utf-8')


server = server_socket()
server.start()