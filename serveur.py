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
        for client in self.clients:
            client.send(msg)

    # Recevoir les messages de clients connectés
    def handle(self, client):
        while True:
            try:
                msg = client.recv(1024).decode('ascii')
                self.broadcast(msg.encode('ascii'))
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.broadcast(f"{nickname} has left the chat\n".encode('ascii'))
                self.nicknames.remove(nickname)
                break

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}\n")

            client.send('NICK'.encode('ascii'))
            nickname = client.recv(1024).decode('ascii')
            self.nicknames.append(nickname)
            self.clients.append(client)
            print(f"Well hello {nickname}\n")
            self.broadcast(f"{nickname} just joined the chat.\n".encode('ascii'))
            client.send(("Connected to the server, port " + str(self.port)).encode('ascii'))

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(10)

        print("The server is ready.")
        self.receive()

server = server_socket()
server.start()