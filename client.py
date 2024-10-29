import socket
import threading
import tkinter as tk

class ClientNetwork:
    def __init__(self, nickname: str, host = 'localhost', port = 5555):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.socket: socket.socket = None
        self.receive_thread: threading.Thread = None  
        # fonction de rappel à ajouter depuis la classe parente ClientUi
        self._display_callback = None

    @property
    def display_callback(self):
        return self._display_callback

    @display_callback.setter
    def display_callback(self, callback):
        if not callable(callback):
            raise ValueError("display_callback doit être une fonction.")
        self._display_callback = callback

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((self.host, self.port))

            # lancer le thread de reception des messages
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
        except Exception:
            self.disconnect()

    def disconnect(self):
        if self.socket:
            self.socket.close()

    def send_message(self, message):
        if self.socket:
            try:  
                self.socket.send(message.encode('ascii'))
            except Exception as e:
                print(f"Erreur lors de l'envoi du message : {e}")
    
    def receive_messages(self):
        while True:
            try:
                message = self.socket.recv(1024).decode('ascii')

                if message == 'NICK':
                    self.send_message(self.nickname)
                else:
                    # décomposer le message depuis le format <sender>: <message>
                    split = message.split(': ', 1)
                    
                    sender  = split[0] if len(split) > 1 else "server"
                    content = split[1] if len(split) > 1 else split[0]

                    # déléguer l'affichage d'un message dans une fonction de rappel
                    if self.display_callback:
                        self.display_callback(content, sender)
            except Exception as e:
                print(f"Erreur lors de la reception d'un message : {e}")
                self.disconnect()
                break

class ClientUi(tk.Tk):
    TITLE = "P8 Mini Chat"

    def __init__(self, network_client: ClientNetwork):
        super().__init__()

        self.network_client = network_client
        self.nickname = network_client.nickname

        self.network_client.display_callback = self.display_messages
        
        self.init_ui()

    def start_network_connection(self):
        self.network_client.connect()

    def init_ui(self):
        self.title(f"{ClientUi.TITLE} - {self.nickname}")
        self.geometry('400x500')
        self.configure(bg='white')
        
        # Configurer les widgets ici...
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # fenêtre
        self.connect_interf = tk.Frame(self, bg='white')

        # espaces de messages
        self.chatbox = tk.Text(self.connect_interf, bg='#EEEEEE', width=40, height=20, state='disabled')
        
        # espaces pour l'input de l'utilisateur
        self.text_bar = tk.Frame(self.connect_interf, bg='pink')
        self.txt = tk.StringVar()
        self.input_space: tk.Entry = tk.Entry(self.text_bar, textvariable=self.txt)
        self.send_button = tk.Button(self.text_bar, text='SEND', command=lambda:self.send(self.txt.get()))

        # paramétrage du scrollbar
        chat_scroll = tk.Scrollbar(self.connect_interf, orient=tk.VERTICAL)
        chat_scroll.config(command=self.chatbox.yview)
        self.chatbox.config(yscrollcommand=chat_scroll.set)
        
        # préparation de tags pour placer les messages
        self.chatbox.tag_configure('right', justify='right')
        self.chatbox.tag_configure('left', justify='left')
        self.chatbox.tag_configure('center', justify='center')
        
        # permet d'appuyer sur Entrer pour envoyer le message
        self.bind("<Return>", lambda e: self.send_message())

        # placement des widgets
        self.connect_interf.grid()
        
        # espace des messages
        self.text_bar.grid(row=2, column=0, columnspan=4)
        
        # espace de l'input
        self.chatbox.grid(row=1, column=0, columnspan=4)
        self.input_space.grid(row=0, column=1)
        self.send_button.grid(row=0, column=2)

        self.display_messages("<connecté>")

    def send_message(self):
        message = self.txt.get()

        if (message):
            full_message = f'{self.nickname}: {message}'
            self.network_client.send_message(full_message)

    def display_messages(self, msg: str, sender: str = 'server'):
        if not msg:
            return

        self.chatbox.config(state='normal')

        # message du serveur
        if sender == 'server':
            self.chatbox.insert(tk.END, f'\n{msg}\n', 'center')
        # message du client actuel
        elif sender == self.nickname:
            self.chatbox.insert(tk.END, f'\nME:\n{msg}\n', 'right')
        # message d'un autre client
        else:
            self.chatbox.insert(tk.END, f'\n{sender}:\n{msg}\n', 'left')

        self.chatbox.config(state='disabled') # bloque le texte
        self.chatbox.see(tk.END)
        self.input_space.delete(0, tk.END) # vide l'input

nickname = input("Entrez votre nom: ")

client_network = ClientNetwork(nickname, host = "localhost", port = 5555)
client_ui = ClientUi(client_network)
client_ui.start_network_connection()

client_ui.mainloop()