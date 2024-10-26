import socket
import threading

class client_socket ():
    def __init__(self, host: str = "", port: int = 5555):
        self.host = host # localhost by default
        self.port = port # 5555 by default

        self.client: socket.socket = None

        self.receive_thread: threading.Thread = None
        self.write_thread: threading.Thread = None

        self.nickname: str = None


    def start(self):
        self.nickname = input("Choose a nickname: ")

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))

        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()

        self.write_thread = threading.Thread(target=self.write)
        self.write_thread.start()


    def receive(self):
        while True:
            try:
                msg = self.client.recv(1024).decode('ascii')
                if msg == 'NICK':
                    self.client.send(self.nickname.encode('ascii'))
                else:
                    print(msg)
            except:
                print("An error occurred")
                self.client.close()
                break
            
    def write(self):
        limit = 10
        while limit > 0:
            print("-> ")
            msg = f'{self.nickname}: {input("")}'
            self.client.send(msg.encode('ascii'))
            limit -= 1
        self.client.close()

c = client_socket()
c.start()
