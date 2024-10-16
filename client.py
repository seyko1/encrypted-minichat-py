import socket
import threading

host = "" # localhost
port = 5555

nickname = input("Choose a nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

def receive():
    while True:
        try:
            msg = client.recv(1024).decode('ascii')
            if msg == 'NICK':
                client.send(nickname.encode('ascii'))
            else:
                print(msg)
        except:
            print("An error occurred")
            client.close()
            break

def write():
    limit = 10
    while limit > 0:
        print("-> ")
        msg = f'{nickname}: {input("")}'
        client.send(msg.encode('ascii'))
        limit -= 1
    client.close()


receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
