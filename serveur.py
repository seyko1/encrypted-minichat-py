import socket
import threading

host = ""
port = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen(10)

clients = []
nicknames = []

#Envoie un message a tous les clients connectés
def broadcast(msg):
    for client in clients:
        client.send(msg)

# Quand un client est connecté, on veut recevoir son message si il y en a
def handle(client):
    while True:
        try:
            msg = client.recv(1024).decode('ascii')
            broadcast(msg.encode('ascii'))
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f"{nickname} has left the chat\n".encode('ascii'))
            nicknames.remove(nickname)
            break

def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}\n")

        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        nicknames.append(nickname)
        clients.append(client)
        print(f"Well hello {nickname}\n")
        broadcast(f"{nickname} just joined the chat.\n".encode('ascii'))
        client.send(("Connected to the server, port " + str(port)).encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Le serveur est pret")
receive()
