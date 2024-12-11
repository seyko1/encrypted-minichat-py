import socket
import threading
import tkinter as tk
from common_lib import ServerAction, ClientAction, EntryForFormatedMessage, ErrorType
import common_lib
import ast #use to transform str sembling as python type list to an atual list: "['default', 'more']" -> list['default', 'more']
from typing import Optional
import rsa 
import secret_box
import os # for os.path.exists()



class ClientNetwork:
    def __init__(self, ui: Optional['ClientUi'], host = common_lib.HOST, port = common_lib.PORT):
        self.host = host
        self.port = port
        self.nickname = None
        self.rsa_keypair = None
        self.ui = ui
        self.socket: socket.socket = None
        self.groups: dict = {}
        self.actual_group: str = None
        self.receive_thread: threading.Thread = None  
        self.listen_messages = True
        # fonction de rappel à ajouter depuis la classe parente ClientUi
        self._display_callback = None

        self.connect_to_server()


    @property
    def display_callback(self):
        return self._display_callback


    @display_callback.setter
    def display_callback(self, callback):
        if not callable(callback):
            raise ValueError("display_callback doit être une fonction.")
        self._display_callback = callback


    def show_groups(self):
        print("\n" + "="*20)
        print(f"{'GROUPS':^20}")
        print("= "*10)
        for name, dictionary in self.groups.items():
            print(f"{name}:\n" + "\n".join([f"  {key}:\n{value}" for key, value in dictionary.items()]))
        print("="*20 + '\n')


    def connect_to_server(self):
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


    def log_in(self, nickname: str):
        self.rsa_keypair = rsa.gen_rsa_keypair(512)

        public_key = self.rsa_keypair[0]
        hex_public_key = rsa.int_rsa_key_to_hex(public_key)

        requestConnection = {
            EntryForFormatedMessage.action: ClientAction.requestConnection,
            EntryForFormatedMessage.nickname: nickname,
            EntryForFormatedMessage.publicKey: hex_public_key
        }
        self.send_message(requestConnection)


    def disconnect(self):
        self.listen_messages = False
        if self.socket:
            self.socket.close()
        print("Network closed.")


    def requestDisconnection(self):
        request = {
            EntryForFormatedMessage.action: ClientAction.requestDisconnection,
        }
        self.send_message(request)


    def sharePublicKey(self):
        public_key = self.rsa_keypair[0]
        hexkey = rsa.int_rsa_key_to_hex(public_key)

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
        if groupName in self.groups:
            print(f"Le groupe {groupName} existe déjà.")
            return

        # ajouter le groupe avec None, en attendant une confirmation du serveur
        self.groups[groupName] = None

        request = {
            EntryForFormatedMessage.action: ClientAction.requestAddGroup,
            EntryForFormatedMessage.groupName: groupName
        }
        self.send_message(request)

    def get_group_box(self, groupName: str):
        group_box = self.groups.get(groupName, {}).get("group_box", None)
        
        if group_box is None:
            print(f"Clé du groupe {groupName} introuvable.")
        return group_box

    def encrypt_msg(self, msg: str, group_name: str):
        group_box = self.get_group_box(group_name)
        return secret_box.encrypt(group_box, msg)
        
    def decrypt_msg(self, msg: str, group_name: str):
        group_box = self.get_group_box(group_name)
        return secret_box.decrypt(group_box, msg)
         
    def send_message(self, entries: dict = {}, target = "server"): 
        if target != "server" and self.actual_group:
            enc_msg = self.encrypt_msg(entries['content'], self.actual_group)
            entries['content'] = enc_msg
        
        common_lib.send_message(self.socket, self.nickname, target, entries)
    

    def receive_messages(self):
        while self.listen_messages:
            try:
                message: dict = common_lib.receive_message(self.socket)
                sender = message[EntryForFormatedMessage.sender]
                target = message[EntryForFormatedMessage.target]

                if sender == "server":
                    self.handle_message_from_server(message)
                    continue

                content = message[EntryForFormatedMessage.content]

                if target == self.actual_group:
                    dec_msg = self.decrypt_msg(content, self.actual_group)
                    reformated_message = {
                        'sender': sender,
                        'content': dec_msg
                    }
                    self.groups[target]['messages'].append(reformated_message)
                    print(f"message déchiffré : {dec_msg}")
                    content = dec_msg

                # déléguer l'affichage d'un message dans une fonction de rappel
                if self.display_callback:
                    self.display_callback(content, sender)

                #clear entry of the TextingPage
                if sender == self.nickname:
                    self.ui.frames[TextingPage].clear_entry()

            except Exception as e:
                print(f"Erreur lors de la reception d'un message : {e}")
                self.disconnect()
                break


    def handle_message_from_server(self, message: dict):
        action = message[EntryForFormatedMessage.action]

        match action:
            case ServerAction.info:
                content = message[EntryForFormatedMessage.content]
                group = message[EntryForFormatedMessage.target]

                if group == self.actual_group:
                    self.display_callback(content)

            case ServerAction.error:
                self.handle_error(message)
            
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
                self.ui.show_frame(LandingPage)

            #TODO: Fait les mêmes choses que la connection classic
            # car on ne traite pas encore les message en attentes
            case ServerAction.acceptReconnection:
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
                self.ui.show_frame(LandingPage)

            case ServerAction.giveTempNickname:
                tempNickname = message[EntryForFormatedMessage.nickname]
                self.nickname = tempNickname

            case ServerAction.joinGroup:
                groupName = message[EntryForFormatedMessage.groupName]
                cipher_group_key = message.get(EntryForFormatedMessage.groupKey)

                # cas où le serveur répond à une requête de création de groupe.
                if not cipher_group_key:
                    # créer une clé pour le nouveau groupe
                    
                    group_box, new_group_key = secret_box.secret_box_gen()
                    self.groups[groupName] = {
                        'group_box' : group_box,
                        'group_key': new_group_key,
                        'messages': []
                    }
                # Cas où le serveur répond à une demande pour rejoindre un groupe existant.
                else :
                    private_key = self.rsa_keypair[1]

                    group_key = rsa.rsa_dec(cipher_group_key, private_key[0], private_key[1])
                    group_box = secret_box.secret_box_gen_by_key(group_key)

                    self.groups[groupName] = {
                        'group_box' : group_box,
                        'group_key': group_key,
                        'messages': []
                    }                    

                
                self.actual_group = groupName
                print(f"Join group [{groupName}]")
                self.ui.show_frame(TextingPage)

                self.show_groups()
            
            case ServerAction.leaveGroup:
                groupName = message[EntryForFormatedMessage.groupName]
                self.groups[groupName] = {}
                self.ui.show_frame(LandingPage)

            case ServerAction.shareGroups:
                groups = message[EntryForFormatedMessage.groupsList]
                groups = ast.literal_eval(groups)
                for group in groups:
                    if group in self.groups.keys():
                        continue
                    self.groups[group] = {}
                if self.ui.current_ui == "groupChoice_ui":
                    self.ui.groupChoice_ui()

                self.ui.frames[LandingPage].update_convo_buttons()

            case ServerAction.requestKey:
                group_name = message[EntryForFormatedMessage.groupName]
                nickname, public_key = message[EntryForFormatedMessage.keyRequester]

                int_public_key = rsa.hex_rsa_key_to_int(public_key)
                group_key = self.groups[group_name]['group_key']
              
                # envoyer la clé de groupe au serveur
                hex_cipher_groupkey = rsa.rsa_enc(group_key, int_public_key[0], int_public_key[1])

                self.send_message({
                    EntryForFormatedMessage.action: ClientAction.shareGroupKey,
                    EntryForFormatedMessage.groupName: group_name,
                    EntryForFormatedMessage.groupKey: (nickname, hex_cipher_groupkey)
                })

            case ServerAction.disconnect:
                self.disconnect()
                self.listen_messages = False
                self.ui.destroy()

            case _:
                print(f"Server tried this action: [{action}], but as no effect, because is undefined.")


    def handle_error(self, message: dict):
            errorType = message[EntryForFormatedMessage.errorType]
            match errorType:
                case ErrorType.nicknameTaken:
                    print("Nom déjà utilisé")
                    #must be shown to the user, on the Connection interface
                case ErrorType.alreadyConnected:
                    print("Vous êtes déjà connecté ailleurs")
                    #must be shown to the user, on the Connection interface
                case ErrorType.groupNameTaken:
                    group_name = message[EntryForFormatedMessage.groupName]
                    print(f"Le groupe {group_name} existe déjà.")


class ClientUi(tk.Tk):
    TITLE = "P8 Mini Chat"


    def __init__(self): #nickname devrait être demandé dans la méthode de connection, mais pour l'instant, on l'obtient avant la création de l'ui
        super().__init__()

        self.network_client: ClientNetwork = None
        self.nickname = None
        self.current_ui: str = "" #used to reload the groupe page when a new group comes
        self.frames = {}

        # Configuration de la fenêtre
        self.geometry("1280x832")
        self.title("P8 Mini Chat")

        # Initialisation du thème
        self.theme = "light"
        self.colors = {
            "light": {"bg": "#E2D0F8", "fg": "#317874", "button": "#B5A8A8", "canvas": "#317874"},
            "dark": {"bg": "#2C2C2C", "fg": "#E2D0F8", "button": "#444444", "canvas": "#1E1E1E"}
        }


        self.protocol("WM_DELETE_WINDOW", lambda: self.on_closing())
        self.start_network_connection()
        self.open_window()
        self.show_frame(LoginPage)


    def open_window(self):
        # Fenêtre principale
        window = tk.Frame(self)
        window.pack(side="top", fill="both", expand=True)
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)

        for F in (LoginPage, LandingPage, GroupCreationPage, TextingPage):
            frame = F(window, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")


    def on_closing(self):
        self.network_client.requestDisconnection()


    def show_frame(self, page):
        # Affiche la page demandée.
        frame = self.frames[page]
        frame.tkraise()

        self.unbind('<Return>')
        #clear the entry of GroupCreationPage #can't do elsewhere when the groupName is validated
        self.frames[GroupCreationPage].clear_entry()

        #update title
        if page is LoginPage:
            self.title(f'{ClientUi.TITLE} - Connection')
            frame.init_binds()
        elif page is LandingPage:
            self.title(f'{ClientUi.TITLE} - Accueil - {self.nickname}')
            frame.update_convo_buttons()
        elif page is GroupCreationPage:
            self.title(f'{ClientUi.TITLE} - Création de groupe - {self.nickname}')
            frame.init_binds()
        elif page is TextingPage:
            frame.update_group(self.network_client.actual_group)
            self.title(f'{ClientUi.TITLE} - {self.network_client.actual_group} - {self.nickname}')
            frame.init_binds()


    def toggle_theme(self):
        """Bascule entre mode clair et mode sombre."""
        self.theme = "dark" if self.theme == "light" else "light"
        for frame in self.frames.values():
            frame.update_theme()


    def try_to_log_in(self, nickname: str):
        if not nickname:
            return
        self.nickname = nickname
        self.network_client.log_in(nickname)
    

    def try_to_join_group(self, groupName: str):
        print(f'Try to join "{groupName}"')
        print(self.network_client.groups)
        has_key = self.network_client.groups[groupName].get('key')
        #switch window
        if has_key:
            self.network_client.actual_group = groupName
            self.show_frame(TextingPage)
        #request for joining
        else:
            self.network_client.joinGroup(groupName)


    def try_to_leave_group(self, groupName: str):
        print(f'Try to leave "{groupName}"')
        self.network_client.leaveGroup(groupName)


    def try_create_group(self, groupName:str):
        print(f'Try to create the groupe "{groupName}"')
        # refuse empty name
        if not (groupName and groupName.lstrip()):
            print("Le nom du groupe ne peut être vide")
            return

        self.network_client.addGroup(groupName)
        # self.groupChoice_ui()


    def start_network_connection(self):
        self.network_client = ClientNetwork(self)

        # self.network_client.display_callback = self.display_messages


    def send_message(self, message):
        if (message):
            self.network_client.send_message({'content': message}, self.network_client.actual_group)


    #old. TODO VAL je (Valentin) préfère avoir un tk.Text en guise de chat, et le gérer comme dans la fonction qui suit 
    # def display_messages(self, message: str, sender = "server"):
    #     if not message:
    #         return

    #     self.chatbox.config(state='normal')

    #     # message du serveur
    #     if sender == 'server':
    #         self.chatbox.insert(tk.END, f'\n{message}\n', 'center')
    #     # message du client actuel
    #     elif sender == self.nickname:
    #         self.chatbox.insert(tk.END, f'\nME:\n{message}\n', 'right')
    #     # message d'un autre client
    #     else:
    #         self.chatbox.insert(tk.END, f'\n{sender}:\n{message}\n', 'left')

    #     self.chatbox.config(state='disabled') # bloque le texte
    #     self.chatbox.see(tk.END)
    #     self.input_space.delete(0, tk.END) # vide l'input



# Fonctions pour les différentes pages
class ThemedFrame(tk.Frame):
    def __init__(self, parent: tk.Frame, controller: ClientUi):
        super().__init__(parent)
        self.controller = controller
        self.button_images = {}  # Stocke les images des boutons pour chaque thème
        self.update_theme()


    def update_theme(self):
        colors = self.controller.colors[self.controller.theme]
        self.configure(bg=colors["bg"])

        # change colors or image of each widgets
        for widget in self.winfo_children():
            if isinstance(widget, (tk.Label, tk.Entry)):
                widget.configure(bg=colors["bg"], fg=colors["fg"])

            elif isinstance(widget, tk.Button):
                widget.configure(bg=colors["bg"], fg=colors["fg"],highlightbackground=colors["bg"],activebackground=colors["bg"])
                # Mise à jour de l'image si le bouton est enregistré avec un thème
                if hasattr(widget, "image_key") and widget.image_key in self.button_images:
                    widget.configure(image=self.button_images[widget.image_key][self.controller.theme])

            elif isinstance(widget, tk.Canvas):
                widget.configure(bg=colors["canvas"])


    def add_button_image(self, button: tk.Button, image_key: str, light_image_path: str, dark_image_path:str):
        # Ajoute une image associée à un bouton pour chaque thème.
        light_image = tk.PhotoImage(file=light_image_path) if os.path.exists(light_image_path) else None
        dark_image = tk.PhotoImage(file=dark_image_path) if os.path.exists(dark_image_path) else None
        self.button_images[image_key] = {"light": light_image, "dark": dark_image}
        button.image_key = image_key  # Attribut pour suivre le bouton
        button.configure(image=self.button_images[image_key][self.controller.theme])


    def change_button_image(self, button: tk.Button, gicp: str, picp: str, gisp: str, pisp: str):
        # Toggle button pour lister les groupes ou les gens.
        if not hasattr(button, 'state'):
            button.state = 'group'

        if self.controller.theme == "light":
            print("claiiiir")
            gic = tk.PhotoImage(file=gicp) if os.path.exists(gicp) else None
            pic = tk.PhotoImage(file=picp) if os.path.exists(picp) else None
            button.images = {
                'group': gic,
                'people': pic
            }

        else : 
            print("sombre")
            gis = tk.PhotoImage(file=gisp) if os.path.exists(gisp) else None
            pis = tk.PhotoImage(file=pisp) if os.path.exists(pisp) else None
            button.images = {
                'group':  gis,
                'people': pis
            }

        button.state = 'people' if button.state == 'group' else 'group'
        button.configure(image=button.images[button.state])


# Page de connexion
class LoginPage(ThemedFrame):
    def __init__(self, parent: tk.Frame, controller: ClientUi):
        super().__init__(parent, controller)

    # Configuration de la grille
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1) 
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)

    #Colonne gauche :
        # CONNEXION
        tk.Label(self, text="CONNEXION", fg="#317874", bg="#E2D0F8", font=("Montserrat", 32, "bold")).grid(column=0, row=1, pady=10)

        # Pseudo
        tk.Label(self, text="Pseudo",  fg="#317874", bg="#E2D0F8",font=("Montserrat", 16, "bold")).grid(column=0, row=3, sticky="sw", padx=50, pady=(5, 0))

        # Case pour entrer le pseudo utilisateur
        self.user_entry = tk.Entry(
            self,
            bd=4,
            highlightthickness=4,
            highlightbackground="#cccccc",
            highlightcolor="#317874",
            font=("Montserrat", 14)
        )
        self.user_entry.grid(column=0, row=4, padx=50, sticky="ew")
        self.user_entry.config(width=25) 

        # Bouton Entree
        button_image_path = "assets/frame0/entry_button.png"
        self.button_entry_image = tk.PhotoImage(file=button_image_path) if os.path.exists(button_image_path) else None
        tk.Button(
            self, image=self.button_entry_image, relief="flat",
            command=lambda: controller.try_to_log_in(self.user_entry.get())
        ).grid(column=0, row=6, pady=20)

    #Colone droite :
        #Rectangle bleu
        self.rectangle_bleu_image = tk.PhotoImage(file="assets/frame0/rectangle_bleu.png")
        rectangle_bleu = tk.Label(self, image=self.rectangle_bleu_image, bg="#317874")
        rectangle_bleu.grid(column=1, row=0, rowspan=10, columnspan=1, sticky="nsew")

    #Ancinne colonne droite
        # # Titre "P8 Mini Chat" sur la droite
        # canvas = tk.Canvas(self, width=400, height=1024, bg="#317874", highlightthickness=0)
        # canvas.grid(column=1, row=0, rowspan=10, sticky="nswe")
        # tk.Label(self, text="P8 Mini Chat", font=("Montserrat", 32, "bold"), fg="#E2D0F8", bg="#317874").grid(column=1, row=3)

        # # Image en dessous du titre (réduction de la taille)
        # logo_image_path = "assets/frame0/logo_chat.png"
        # if os.path.exists(logo_image_path):
        #     self.logo_image = tk.PhotoImage(file=logo_image_path).subsample(2, 2)  # Divise la taille par 2
        #     tk.Label(self, image=self.logo_image, bg="#317874").grid(column=1, row=4)


    def init_binds(self):
        self.user_entry.focus()
        self.controller.bind('<Return>', lambda e: self.controller.try_to_log_in(self.user_entry.get()))



class LandingPage(ThemedFrame):
    def __init__(self, parent: tk.Frame, controller: ClientUi):
        super().__init__(parent, controller)

        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)

    # Colonne gauche
        tk.Label(self, text="P8 Mini Chat", bg="#E2D0F8", fg="#317874", font=("Montserrat", 24, "bold")).grid(column=0, row=0, sticky="w")

        # Bouton pour changer le thème
        theme_button = tk.Button(self, relief="flat", bd=0, bg="#E2D0F8", activebackground="#E2D0F8", highlightbackground="#E2D0F8", command=controller.toggle_theme)
        self.add_button_image(
            theme_button,
            image_key="theme_switch",
            light_image_path="assets/frame1/theme_switch_clair.png",
            dark_image_path="assets/frame1/theme_switch_sombre.png"
        )
        theme_button.grid(column=0, row=1)

        # Bouton pour créer un groupe
        group_button = tk.Button(self, relief="flat", bd=0, bg="#E2D0F8", activebackground="#E2D0F8", highlightbackground="#E2D0F8", command=lambda: controller.show_frame(GroupCreationPage))
        self.add_button_image(
            group_button,
            image_key="group_create",
            light_image_path="assets/frame1/group_create_clair.png",
            dark_image_path="assets/frame1/group_create_sombre.png"
        )
        group_button.grid(column=0, row=2)

    # Colonne droite
        # Rectangle bleu/gris
        canvas1 = tk.Canvas(self, bg="#317874", highlightthickness=0)
        canvas1.grid(column=1, row=0, rowspan=10, sticky="nsew")

        # Groupchat_button (basculer entre la page des groupes et personnes)
        groupchat_button = tk.Button(self, relief="flat", bd=0, bg="#317874", activebackground="#317874", highlightbackground="#317874")
        # groupchat_button.configure(command=lambda: self.change_button_image(groupchat_button, "assets/frame1/groups_button_clair.png", "assets/frame1/people_button_clair.png","assets/frame1/groups_button_sombre.png","assets/frame1/people_button_sombre.png"))
        groupchat_button.configure(command=lambda: print('Does Nothing.'))
        #TODO must (could) implemente the switch between group and private chat
        groupchat_button.grid(column=1, row=0)
        self.add_button_image(
            groupchat_button,
            image_key="groups_button",
            light_image_path="assets/frame1/groups_button_clair.png",
            dark_image_path="assets/frame1/groups_button_sombre.png"
        )

        # create as many buttons as groupe conversations 
        self.convo_buttons = tk.Label(self, text="aled", bg="red")
        self.convo_buttons.grid(column=1, row=2)

        # Exemple de Peoplechat_button (Redirection vers les pages de convo)
        # peoplechat_button = tk.Button(self, relief="flat", bd=0, bg="#317874", activebackground="#317874", highlightbackground="#317874", command=lambda: [print("Affiche les discussions privées"),controller.show_frame(TextingPage)])
        # self.add_button_image(
        #     peoplechat_button,
        #     image_key="peoplechat_button",
        #     light_image_path="assets/frame1/groupchat_button_clair.png",
        #     dark_image_path="assets/frame1/groupchat_button_sombre.png"
        # )
        # peoplechat_button.grid(column=1, row=2)

        # tk.Label(self, text="Exemple d'affichage de convo", bg="#E2D0F8", fg="black", font=("Montserrat", 12, "normal")).grid(column=1, row=2)


    def update_convo_buttons(self):
        # remove present buttons
        for layout in self.convo_buttons.winfo_children():
            # TODO VAL ?? remove from self.button_images ?
            layout.destroy()

        groups = self.controller.network_client.groups.keys()

        # recreate buttons
        for i, groupName in enumerate(groups):
            btn = tk.Button(self.convo_buttons, text=groupName, relief="flat", bd=0, bg="#317874", activebackground="#317874", highlightbackground="#317874", command = lambda name = groupName: self.controller.try_to_join_group(name))
            # self.add_button_image(
            #     btn,
            #     image_key="peoplechat_button",
            #     light_image_path="assets/frame1/groupchat_button_clair.png",
            #     dark_image_path="assets/frame1/groupchat_button_sombre.png"
            # )
            btn.grid(column=0, row=i)
            # tk.Label(self.convo_buttons, text=groupeName, bg="#E2D0F8", fg="black", font=("Montserrat", 12, "normal")).grid(column=0, row=i)



# Page de création du groupe
class GroupCreationPage(ThemedFrame):
    def __init__(self, parent: tk.Frame, controller: ClientUi):
        super().__init__(parent, controller)

        # Configuration de la grille :
        self.grid_columnconfigure(0, weight=1)
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)
        self.configure(bg="#E2D0F8")

        tk.Label(self, text="P8 Mini Chat", bg="#E2D0F8", fg="#317874", font=("Montserrat", 24, "bold")).grid(column=0, row=1, sticky="nw")

        #Rectangle principal 
        grouppad = tk.Button(self, relief="flat", bd=0, bg="#E2D0F8", activebackground="#E2D0F8", highlightbackground="#E2D0F8")
        self.add_button_image(
            grouppad,
            image_key="grouppad_button",
            light_image_path="assets/frame2/grouppad_clair.png",
            dark_image_path="assets/frame2/grouppad_sombre.png"
        )
        grouppad.grid(column=0,row=1)
        
        # Entry du groupname
        self.groupname_entry = tk.Entry(self, bd=0, highlightthickness=0, bg="#E2D0F8", fg="#ffffff")
        self.groupname_entry.grid(column=0, row=1, ipadx=230, ipady=10)

        # Bouton valider
        valider_button = tk.Button(self, relief="flat", bd=0, bg="#E2D0F8", activebackground="#E2D0F8", highlightbackground="#E2D0F8", command=lambda: controller.try_create_group(self.groupname_entry.get()))
        self.add_button_image(
            valider_button,
            image_key="groupname_entry_button",
            light_image_path="assets/frame2/valider_button_clair.png",
            dark_image_path="assets/frame2/valider_button_sombre.png"
        )
        valider_button.grid(column=0,row=2)
        cancel_button = tk.Button(self, relief="flat", bd=0, bg="#E2D0F8", activebackground="#E2D0F8", highlightbackground="#E2D0F8", command=lambda: [self.clear_entry(), controller.show_frame(LandingPage)])
        self.add_button_image(
            cancel_button,
            image_key="groupname_cancel_button",
            light_image_path="assets/frame2/annuler_button_clair.png",
            dark_image_path="assets/frame2/annuler_button_sombre.png"
        )
        cancel_button.grid(column = 0,row = 3)


    def init_binds(self):
        self.groupname_entry.focus()
        self.controller.bind('<Return>', lambda e: self.controller.try_create_group(self.groupname_entry.get()))


    def clear_entry(self):
        self.groupname_entry.delete(0, tk.END)



#a finir
class TextingPage(ThemedFrame):
    def __init__(self, parent: tk.Frame, controller: ClientUi):
        super().__init__(parent, controller)
        self.network_client = controller.network_client
        self.network_client.display_callback = self.display_message

        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)  # Colonne gauche (groupes)
        self.grid_columnconfigure(1, weight=3)  # Colonne droite (messages)
        self.grid_rowconfigure(1, weight=1)  # Zone principale

        # === SECTION GAUCHE : LISTE DES GROUPES + RETOUR ===
        self.group_frame = tk.Frame(self, bg=self.controller.colors[self.controller.theme]["canvas"])
        self.group_frame.grid(column=0, row=0, rowspan=3, sticky="nsew", padx=10, pady=10)
        self.group_frame.grid_rowconfigure(0, weight=1)

        # Bouton Retour
        back_button = tk.Button(
            self.group_frame, text="Retour", font=("Montserrat", 12, "bold"),
            bg=self.controller.colors[self.controller.theme]["button"],
            fg=self.controller.colors[self.controller.theme]["fg"],
            command=lambda: self.controller.try_to_leave_group(self.network_client.actual_group) 
        )
        back_button.pack(pady=10, padx=10, fill="x")

        # Label pour les groupes
        tk.Label(
            self.group_frame, text="Groupes", font=("Montserrat", 16, "bold"),
            bg=self.controller.colors[self.controller.theme]["canvas"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        ).pack(pady=10)

        # Liste des groupes
        self.groups_list = ["Groupe 1", "Groupe 2", "Groupe 3"]
        for group in self.groups_list:
            tk.Button(
                self.group_frame, text=group, font=("Montserrat", 12),
                bg=self.controller.colors[self.controller.theme]["bg"],
                fg=self.controller.colors[self.controller.theme]["fg"],
                command=lambda g=group: self.network_client.join_group(g)
            ).pack(fill="x", pady=5)

        # === SECTION DROITE : MESSAGES DU GROUPE ===
        # Nom du groupe
        self.group_label = tk.Label(
            self, text="Nom du groupe (en attente)", font=("Montserrat", 24, "bold"),
            bg=self.controller.colors[self.controller.theme]["bg"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        )
        self.group_label.grid(column=1, row=0, pady=10, padx=10, sticky="ew")

        # Cadre pour les messages avec un canvas (zone défilante)
        message_frame_container = tk.Frame(self, bg=self.controller.colors[self.controller.theme]["bg"])
        message_frame_container.grid(column=1, row=1, sticky="nsew", pady=10, padx=10)
        message_frame_container.grid_rowconfigure(0, weight=1)
        message_frame_container.grid_columnconfigure(0, weight=1)

        self.message_canvas = tk.Canvas(
            message_frame_container, bg=self.controller.colors[self.controller.theme]["bg"], highlightthickness=0
        )
        self.message_canvas.grid(column=0, row=0, sticky="nsew")

        self.message_scrollbar = tk.Frame(self.message_canvas)
        self.message_canvas.create_window((0, 0), window=self.message_scrollbar, anchor="nw")

        self.message_scrollbar.bind(
            "<Configure>",
            lambda event: self.message_canvas.configure(scrollregion=self.message_canvas.bbox("all"))
        )

        # Champ de saisie pour les messages
        self.entry_message = tk.Entry(
            self, font=("Montserrat", 14),
            bg=self.controller.colors[self.controller.theme]["bg"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        )
        self.entry_message.grid(column=1, row=2, sticky="ew", padx=10, pady=10)

        # Bouton d'envoi
        send_button = tk.Button(
            self, text="Envoyer", command=self.send_message,
            bg=self.controller.colors[self.controller.theme]["button"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        )
        send_button.grid(column=1, row=3, sticky="ew", padx=10, pady=10)


    def init_binds(self):
        self.entry_message.focus()
        self.controller.bind('<Return>', lambda e: self.send_message())


    def clear_entry(self):
        self.entry_message.delete(0, tk.END)


    def display_message(self, content: str, sender = 'server'):
        # Affiche un message reçu dans la zone des messages.
        message_label = tk.Label(
            self.message_scrollbar,
            text=f"{sender}: {content}",
            font=("Montserrat", 12),
            anchor="w",
            justify="left",
            wraplength=500,
            bg=self.controller.colors[self.controller.theme]["bg"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        )
        message_label.pack(fill="x", padx=10, pady=5)

        # Scroll automatiquement vers le bas
        self.message_canvas.update_idletasks()
        self.message_canvas.yview_moveto(1.0)


    def send_message(self):
        #Gère l'envoi d'un message.
        if not self.network_client.actual_group:
            return

        message = self.entry_message.get()
        message = message.strip()
        if not message:
            return
        
        self.controller.send_message(message)

        # TODO VAL !! Messages displayed are those send by the server (even own messages)
        # MUST BE DELETED
        # self.display_message(message, "Moi")  # Affiche immédiatement dans l'interface
        # self.entry_message.delete(0, "end")


    def update_group(self, group_name: str):
        # Met à jour le nom du groupe actif.
        self.group_label.config(text=f"Conversation : {group_name}")



client_ui = ClientUi()
client_ui.mainloop()
print("Prog end.\nPlease, Press Ctrl+C...")

# !!! ici, le thread "receive_message" n'a pas été arrếté (trop chiant -_-'')

