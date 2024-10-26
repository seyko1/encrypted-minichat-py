import socket
import threading
import tkinter as tk

class interface_client (tk.Tk):
    TITLE: str = 'P8 Mini Chat'

    def __init__(self):
        tk.Tk.__init__(self)

        #paramètres de l'interface
        self.title(interface_client.TITLE)
        self.geometry('400x500')
        self.config(bg='white')

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.host = None # localhost by default
        self.port = None # 5555 by default
        self.nickname = None
        self.client: socket.socket = None
        self.receive_thread: threading.Thread = None
        # self.write_thread: threading.Thread = None


    def init_client(self, name: str, host: str = "", port: int = 5555):
        self.host = host # localhost by default
        self.port = port # 5555 by default

        self.nickname = name


    def start(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))

        self.connection()

        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()

        # self.write_thread = threading.Thread(target=self.write)
        # self.write_thread.start()


    def receive(self):
        while True:
            try:
                msg = self.client.recv(1024).decode('ascii')
                if msg == 'NICK':
                    self.client.send(self.nickname.encode('ascii'))
                else:
                    print(msg)
                    msg: dict[str] = self.decompose_message(msg)
                    print(msg)
                    self.create_msg_box(msg['content'], msg['sender'])
            except:
                print("An error occurred")
                self.client.close()
                break
            
    # def write(self):
    #     limit = 10
    #     while limit > 0:
    #         print("-> ")
    #         msg = f'{self.nickname}: {input("")}'
    #         self.client.send(msg.encode('ascii'))
    #         limit -= 1
    #     self.client.close()

    def send(self, message):
        msg = f'{self.nickname}: {message}'
        self.client.send(msg.encode('ascii'))


    # En supposant que les messages sont formaté comme suit -> "envoyeur: contenu",
    # retourne un dictionnaire {'sender': envoyeur, 'content': contenu}
    def decompose_message(self, message: str) -> dict[str]:
        splitted = message.split(': ')
        if len(splitted) == 1:
            return {'sender': 'server', 'content': splitted[0]}
        else:
            return {'sender': splitted[0], 'content': splitted[1]}


    # créé une interface permettant l'envoie et la réception de messages
    def connection(self):
        self.title(interface_client.TITLE + ' - ' + self.nickname)
        #fenêtre
        self.connect_interf = tk.Frame(self, bg='white')

        #=== CRÉATION / PRÉPARATION DES WIDGETS ===
        #espaces de messages
        self.tchat = tk.Text(self.connect_interf, bg='#EEEEEE', width=40, height=20, state='disabled')
        #scrollbar
        tchat_scroll = tk.Scrollbar(self.connect_interf, orient=tk.VERTICAL)
        #espaces pour l'input de l'utilisateur
        self.text_bar = tk.Frame(self.connect_interf, bg='pink')
        self.txt = tk.StringVar()
        self.input_space: tk.Entry = tk.Entry(self.text_bar, textvariable=self.txt)
        self.send_button = tk.Button(self.text_bar, text='SEND', command=lambda:self.send(self.txt.get()))
        #paramétrage du scrollbar
        tchat_scroll.config(command=self.tchat.yview)
        self.tchat.config(yscrollcommand=tchat_scroll.set)
        #préparation de tags pour placer les messages
        self.tchat.tag_configure('right', justify='right')
        self.tchat.tag_configure('left', justify='left')
        self.tchat.tag_configure('center', justify='center')
        #permet d'appuyer sur Entrer pour envoyer le message
        self.bind("<Return>", lambda e: self.send(self.txt.get()))

        #=== PLACEMENT DES WIDGETS ==============
        self.connect_interf.grid()
        #espace des messages
        self.text_bar.grid(row=2, column=0, columnspan=4)
        # tchat_scroll.pack(side='right')
        #espace de l'input
        self.tchat.grid(row=1, column=0, columnspan=4)
        self.input_space.grid(row=0, column=1)
        self.send_button.grid(row=0, column=2)

        self.create_msg_box("<connecté>")


    # insère un texte dans l'espace de message, et le positionne horizontalement selon l'envoyer (serveur, soi-même ou quelqu'un d'autre)
    def create_msg_box(self, msg:str, sender:str = 'server'):
        if not msg:
            return

        self.tchat.config(state='normal') #débloque le Text

        #message du serveur
        if sender == 'server':
            self.tchat.insert(tk.END, f'\n{msg}\n', 'center')
        #message de moi-même
        elif sender == self.nickname:
            self.tchat.insert(tk.END, f'\nME:\n{msg}\n', 'right')
        #message de quelqu'un d'autre
        else:
            self.tchat.insert(tk.END, f'\n{sender}:\n{msg}\n', 'left')

        self.tchat.config(state='disabled') # bloque le Text
        self.tchat.see(tk.END)
        self.input_space.delete(0, tk.END) # vide l'input



nickname = input("Choose a nickname: ")
app = interface_client()
app.init_client(nickname)
app.start()
app.mainloop()
