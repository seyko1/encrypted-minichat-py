import socket
import threading
import tkinter as tk
from common_lib import ServerAction, EntryForFormatedMessage
import common_lib
import ast #use to transform str sembling as python type list to an atual list: "['default', 'more']" -> list['default', 'more']


class ClientNetwork:
    def __init__(self, nickname: str, host = 'localhost', port = 5555):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.socket: socket.socket = None
        self.groups: dict = {}
        self.actual_group: str = None
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
            self.send_message({EntryForFormatedMessage.content: self.nickname})

            # lancer le thread de reception des messages
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
        except Exception:
            self.disconnect()

    def disconnect(self):
        if self.socket:
            self.socket.close()

    def send_message(self, entries: dict = {}, target = "server"):
        common_lib.send_message(self.socket, self.nickname, target, entries)
    
    def receive_messages(self):
        while True:
            try:
                message: dict = common_lib.receive_message(self.socket)
                sender = message["sender"]
                target = message["target"]
                if sender == "server":
                    self.handle_message_from_server(message, message[EntryForFormatedMessage.action])
                    continue

                # déléguer l'affichage d'un message dans une fonction de rappel
                if self.display_callback:
                    self.display_callback(message[EntryForFormatedMessage.content], sender)
            except Exception as e:
                print(f"Erreur lors de la reception d'un message : {e}")
                self.disconnect()
                break


    def handle_message_from_server(self, message: dict, action: str):

        match action:
            case ServerAction.info:
                content = message[EntryForFormatedMessage.info]
                self.display_callback(content)

            case ServerAction.allowAccess:
                groupName = message[EntryForFormatedMessage.groupName]
                self.groups[groupName]["have access"] = True

            case ServerAction.joinGroup:
                groupName = message[EntryForFormatedMessage.groupName]
                if not self.groups[groupName]["have access"]:
                    print(f"You don't have acces to group [{groupName}]")
                else:
                    self.actual_group = groupName
                    print(f"Join group [{groupName}]")

            case ServerAction.shareGroups:
                groups = message[EntryForFormatedMessage.groupsList]
                groups = ast.literal_eval(groups)
                for group in groups:
                    self.groups[group] = {"have access": False}

            case _:
                print(f"Server tried this action: [{action}], but as no effect, because is undefined.")



class ClientUi(tk.Tk):
    TITLE = "P8 Mini Chat"

    def __init__(self, nickname: str): #nickname devrait être demandé dans la méthode de connection, mais pour l'instant, on l'obtient avant la création de l'ui
        super().__init__()

        self.network_client: ClientNetwork = None
        self.nickname = nickname #existe temporairement, permet d'obtenir le nom avant le création de l'objet UI

        self.connection_ui()


    def start_network_connection(self, nickname: str):
        self.network_client = ClientNetwork(nickname, host = "localhost", port = 5555)

        self.network_client.display_callback = self.display_messages
        self.network_client.connect()


    # Création d'une interface recueillant le nom de l'utilisateur
    # !! pour l'instant, il n'y a pas d'interface
    def connection_ui(self):
        #self.nickname = input("Entrez votre nom: ")
        # je voulais faire l'input ici, ce qui se ferait avec une interface,
        # mais en passant par le terminale, c'est mieux de faire l'input avant l'initialisation de l'objet UI
        # sinon, ça ouvre une interface vide, puis il faut rebasculer dans le terminal pour entrer le nom
        self.init_ui()
        self.start_network_connection(self.nickname) #oui c'est bizarre de donner un nom qu'on a déjà, mais plus tard, c'est ici, qu'il sera créé


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
        self.send_button = tk.Button(self.text_bar, text = 'Send', command = lambda:self.send_message(self.txt.get()))

        # paramétrage du scrollbar
        chat_scroll = tk.Scrollbar(self.connect_interf, orient=tk.VERTICAL)
        chat_scroll.config(command=self.chatbox.yview)
        self.chatbox.config(yscrollcommand=chat_scroll.set)
        
        # préparation de tags pour placer les messages
        self.chatbox.tag_configure('right', justify='right')
        self.chatbox.tag_configure('left', justify='left')
        self.chatbox.tag_configure('center', justify='center')
        
        # permet d'appuyer sur Entrer pour envoyer le message
        self.bind("<Return>", lambda _:self.send_message(self.txt.get()))

        # placement des widgets
        self.connect_interf.grid()
        
        # espace des messages
        self.text_bar.grid(row=2, column=0, columnspan=4)
        
        # espace de l'input
        self.chatbox.grid(row=1, column=0, columnspan=4)
        self.input_space.grid(row=0, column=1)
        self.send_button.grid(row=0, column=2)

        self.display_messages("<connecté>")

    def send_message(self, message):
        if (message):
            self.network_client.send_message({'content': message}, self.network_client.actual_group)

    def display_messages(self, message: str, sender = "server"):
        if not message:
            return

        self.chatbox.config(state='normal')

        # message du serveur
        if sender == 'server':
            self.chatbox.insert(tk.END, f'\n{message}\n', 'center')
        # message du client actuel
        elif sender == self.nickname:
            self.chatbox.insert(tk.END, f'\nME:\n{message}\n', 'right')
        # message d'un autre client
        else:
            self.chatbox.insert(tk.END, f'\n{sender}:\n{message}\n', 'left')

        self.chatbox.config(state='disabled') # bloque le texte
        self.chatbox.see(tk.END)
        self.input_space.delete(0, tk.END) # vide l'input


nickname = input("Entrez votre nom: ") #est voué à disparaitre

client_ui = ClientUi(nickname) #l'argument ne sera plus donné ici, lorsqu'une interface de connection existera

client_ui.mainloop()