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
                sender = message[EntryForFormatedMessage.sender]
                target = message[EntryForFormatedMessage.target]
                if sender == "server":
                    self.handle_message_from_server(message)
                    continue

                # déléguer l'affichage d'un message dans une fonction de rappel
                if self.display_callback:
                    self.display_callback(message[EntryForFormatedMessage.content], sender)
            except Exception as e:
                print(f"Erreur lors de la reception d'un message : {e}")
                self.disconnect()
                break


    def handle_message_from_server(self, message: dict):
        action = message[EntryForFormatedMessage.action]

        match action:
            case ServerAction.info:
                content = message[EntryForFormatedMessage.content]
                self.display_callback(content)

            case ServerAction.joinGroup:
                groupName = message[EntryForFormatedMessage.groupName]
                self.actual_group = groupName
                print(f"Join group [{groupName}]")

            case ServerAction.shareGroups:
                groups = message[EntryForFormatedMessage.groupsList]
                groups = ast.literal_eval(groups)

            case _:
                print(f"Server tried this action: [{action}], but as no effect, because is undefined.")



class ClientUi(tk.Tk):
    TITLE = "P8 Mini Chat"

    def __init__(self): #nickname devrait être demandé dans la méthode de connection, mais pour l'instant, on l'obtient avant la création de l'ui
        super().__init__()

        self.network_client: ClientNetwork = None
        self.nickname = None

        self.connection_ui()


    def try_to_connect(self, nickname: str):
        if not nickname:
            return
        self.nickname = nickname
        self.clear_ui()
        self.start_network_connection(nickname)


    def start_network_connection(self, nickname: str):
        self.network_client = ClientNetwork(nickname, host = "localhost", port = 5555)

        self.network_client.display_callback = self.display_messages
        self.network_client.connect()


    def clear_ui(self):
        for layout in self.winfo_children():
            layout.destroy()


    # Création d'une interface recueillant le nom de l'utilisateur
    def connection_ui(self):
        self.clear_ui()

        self.title(f"{ClientUi.TITLE}")
        self.geometry("1440x1024")
        self.configure(bg="#E2D0F8")

        canvas = tk.Canvas(
            self,
            bg="#E2D0F8",
            height=1024,
            width=1440,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        canvas.place(x=0, y=0)

        # Cadre entrée pseudo
        self.nickname_entry_image = tk.PhotoImage(file="assets/frame0/nickname_entry.png")
        nickname_entry_bg = canvas.create_image(
            428.0,
            512.5,
            image=self.nickname_entry_image
        )

        # Entrée du pseudo
        self.nickname_entry = tk.Entry(
            self,
            bd=0,
            bg="#B5A8A8",
            fg="#000716",
            highlightthickness=0
        )
        self.nickname_entry.place(
            x=63.0,
            y=457.0,
            width=730.0,
            height=109.0
        )

        canvas.create_text(
            62.0,
            418.0,
            anchor="nw",
            text="Pseudo",
            fill="#317874",
            font=("Montserrat SemiBold", 32 * -1)
        )

        # Bouton login qui lance la génération des clés et switch à la main_page
        self.entry_button_image = tk.PhotoImage(file="assets/frame0/entry_button.png")
        button = tk.Button(
            image=self.entry_button_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.try_to_connect(self.nickname_entry.get()),
            relief="flat"
        )
        button.place(
            x=164.0,
            y=696.0,
            width=528.0,
            height=100.0
        )

        canvas.create_text(
            248.0,
            161.0,
            anchor="nw",
            text="Connexion",
            fill="#317874",
            font=("Montserrat SemiBold", 64 * -1)
        )

        # Rectangle bleu
        canvas.create_rectangle(
            878.0,
            0.0,
            1440.0,
            1024.0,
            fill="#317874",
            outline=""
        )

        self.logo_image = tk.PhotoImage(file="assets/frame0/logo_chat.png")
        image_1 = canvas.create_image(
            1159.0,
            512.0,
            image=self.logo_image
        )

        canvas.create_text(
            1024.0,
            284.0,
            anchor="nw",
            text="RSCHAT",
            fill="#FFFFFF",
            font=("Montserrat SemiBold", 64 * -1)
        )


    def conversation_ui(self):
        self.clear_ui()

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


client_ui = ClientUi()

client_ui.mainloop()