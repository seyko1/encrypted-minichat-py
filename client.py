import socket
import threading
import tkinter as tk
from common_lib import ServerAction, ClientAction, EntryForFormatedMessage, ErrorType
import common_lib
import ast #use to transform str sembling as python type list to an atual list: "['default', 'more']" -> list['default', 'more']
from typing import Optional
from rsa import gen_rsa_keypair, rsa_key_to_hex



class ClientNetwork:
    def __init__(self, ui: Optional['ClientUi'], host = 'localhost', port = 5555):
        self.host = host
        self.port = port
        self.nickname = None
        self.rsa_keypair = None
        self.ui = ui
        self.socket: socket.socket = None
        self.groups: dict = {}
        self.actual_group: str = None
        self.receive_thread: threading.Thread = None  
        # fonction de rappel à ajouter depuis la classe parente ClientUi
        self._display_callback = None

        self.preconnect()


    @property
    def display_callback(self):
        return self._display_callback


    @display_callback.setter
    def display_callback(self, callback):
        if not callable(callback):
            raise ValueError("display_callback doit être une fonction.")
        self._display_callback = callback


    def preconnect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((self.host, self.port))

            # lancer le thread de reception des messages
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()

        except Exception:
            self.disconnect()
            print("Le server n'est pas ouvert.")
            exit()


    def connect(self, nickname: str):
        self.rsa_keypair = gen_rsa_keypair(512)

        public_key = self.rsa_keypair[0]
        hexkey = rsa_key_to_hex(public_key)

        requestConnection = {
            EntryForFormatedMessage.action: ClientAction.requestConnection,
            EntryForFormatedMessage.nickname: nickname,
            EntryForFormatedMessage.public_key: hexkey
        }
        self.send_message(requestConnection)


    def disconnect(self):
        if self.socket:
            self.socket.close()


    def sharePublicKey(self):
        public_key = self.rsa_keypair[0]
        hexkey = rsa_key_to_hex(public_key)

        request = {
            EntryForFormatedMessage.action: ClientAction.sharePublicKey,
            EntryForFormatedMessage.public_key: hexkey
        }
        self.send_message(request)


    def joinGroup(self, groupName):
        request = {
            EntryForFormatedMessage.action: ClientAction.requestJoinGroup,
            EntryForFormatedMessage.groupName: groupName
        }
        self.send_message(request)


    def leaveGroup(self, groupName):
        request = {
            EntryForFormatedMessage.action: ClientAction.requestLeaveGroup,
            EntryForFormatedMessage.groupName: groupName
        }
        self.send_message(request)


    def addGroup(self, groupName):
        request = {
            EntryForFormatedMessage.action: ClientAction.requestAddGroup,
            EntryForFormatedMessage.groupName: groupName
        }
        self.send_message(request)


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

            case ServerAction.acceptConnection:
                #get confirmed nickName
                new_name = message[EntryForFormatedMessage.nickname]
                self.nickname = new_name
                self.ui.nickname = new_name

                #get groups
                groups = message[EntryForFormatedMessage.groupsList]
                groups = ast.literal_eval(groups)
                for group in groups:
                    self.groups[group] = {}

                #switch interface
                self.ui.groupChoice_ui()

            case ServerAction.giveTempNickname:
                tempNickname = message[EntryForFormatedMessage.nickname]
                self.nickname = tempNickname

            case ServerAction.joinGroup:
                groupName = message[EntryForFormatedMessage.groupName]
                self.actual_group = groupName
                print(f"Join group [{groupName}]")
                self.ui.conversation_ui(groupName)
            
            case ServerAction.leaveGroup:
                self.ui.groupChoice_ui()

            case ServerAction.shareGroups:
                groups = message[EntryForFormatedMessage.groupsList]
                groups = ast.literal_eval(groups)
                for group in groups:
                    self.groups[group] = {}
                if self.ui.current_ui == "groupChoice_ui":
                    self.ui.groupChoice_ui()

            case _:
                print(f"Server tried this action: [{action}], but as no effect, because is undefined.")



class ClientUi(tk.Tk):
    TITLE = "P8 Mini Chat"


    def __init__(self): #nickname devrait être demandé dans la méthode de connection, mais pour l'instant, on l'obtient avant la création de l'ui
        super().__init__()

        self.network_client: ClientNetwork = None
        self.nickname = None
        self.current_ui: str = "" #used to reload the groupe page when a new group comes

        self.start_network_connection()
        self.connection_ui()


    def try_to_connect(self, nickname: str):
        if not nickname:
            return
        self.nickname = nickname
        self.network_client.connect(nickname)
    

    def try_to_join_group(self, groupName: str):
        print(f'Try to join "{groupName}"')
        self.network_client.joinGroup(groupName)


    def try_to_leave_group(self, groupName: str):
        print(f'Try to leave "{groupName}"')
        self.network_client.leaveGroup(groupName)


    def try_create_group(self, groupName):
        print(f'Try to create the groupe "{groupName}"')
        self.network_client.addGroup(groupName)
        self.groupChoice_ui()


    def start_network_connection(self):
        self.network_client = ClientNetwork(self)

        self.network_client.display_callback = self.display_messages


    def clear_ui(self):
        for layout in self.winfo_children():
            layout.destroy()


    # Création d'une interface recueillant le nom de l'utilisateur
    def connection_ui(self):
        self.clear_ui()
        self.current_ui = "connection_ui"

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


    def conversation_ui(self, groupName: str):
        self.clear_ui()
        self.current_ui = "conversation_ui"

        self.title(f"{self.nickname} in {groupName}")
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
        self.exit_button = tk.Button(self.text_bar, text = 'Leave', command = lambda: self.try_to_leave_group(groupName))

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
        self.text_bar.grid(row=2, column=0, columnspan=5)
        
        # espace de l'input
        self.chatbox.grid(row=1, column=0, columnspan=5)
        self.exit_button.grid(row=0, column=1)
        self.input_space.grid(row=0, column=2)
        self.send_button.grid(row=0, column=3)

        self.display_messages("<connecté>")


    def groupChoice_ui(self):
        self.clear_ui()
        self.current_ui = "groupChoice_ui"

        self.title(f"{self.nickname} - Groupes")
        self.geometry("600x500")
        self.configure()

        majorFrame = tk.Frame(self)
        self.rootLayout = majorFrame
        majorFrame.grid(sticky='nsew')

        createGroup = tk.Button(majorFrame, text = '+', command=lambda: self.newGroup_ui())
        createGroup.grid(row = 0)

        groupButtonsFrame = tk.Frame(majorFrame)
        groupButtonsFrame.grid(row=1)

        #create as many buttons as groups
        for i, groupName in enumerate(self.network_client.groups.keys()):
            button = tk.Button(
                groupButtonsFrame,
                text = groupName,
                command = lambda groupName = groupName: self.try_to_join_group(groupName))
            button.grid(row = i)


    def newGroup_ui(self):
        self.clear_ui()
        self.current_ui = "newGroup_ui"
        #destroy the content of the previous window
        if self.rootLayout:
            self.rootLayout.destroy()

        majorFrame = tk.Frame(self)
        self.rootLayout = majorFrame
        majorFrame.grid(sticky='nsew')

        cancel = tk.Button(majorFrame, text="Annuler", command=lambda: self.groupChoice_ui())
        cancel.grid(row=0)

        entry = tk.Entry(majorFrame)
        entry.grid(row=1)

        add = tk.Button(majorFrame, text='Ajouter', command=lambda:self.try_create_group(entry.get()))
        add.grid(row=2)


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
