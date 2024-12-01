"""
To-do : 
- exporter le logo utilisateur (l.182)
- recuperer les groupes dans le dico du serveur, leurs creer des boutons et les afficher (l.245)
- recuperer les personnes dans le dico du serveur, leurs creer des boutons et les afficher (l.245)
- recuperer le status du bouton de liste et adapter les icones des boutons (l.245)
- eventuellement creer des id pour les differents labels (l.263)
- exporter le nom du groupe apres sa creation (l.295)
"""
import os
from tkinter import Tk, Frame, Label, Entry, Button, Canvas, PhotoImage
from typing import Optional


# Classe ClientNetwork (simplifiée pour la démo)
class ClientNetwork:
    def __init__(self, nickname: str, ui: Optional['ClientUi'] = None):
        self.nickname = nickname
        self.ui = ui
        self.actual_group = None
        self._display_callback = None

    @property
    def display_callback(self):
        return self._display_callback

    @display_callback.setter
    def display_callback(self, callback):
        if not callable(callback):
            raise ValueError("display_callback doit être une fonction.")
        self._display_callback = callback

    def send_message(self, entries: dict, target: str):
        """Simule l'envoi d'un message."""
        print(f"Message envoyé au groupe [{target}]: {entries['content']}")
        # Simuler une réponse du serveur
        if self.display_callback:
            self.display_callback(f"Réponse automatique : {entries['content']}", "Serveur")

    def join_group(self, group_name: str):
        """Rejoindre un groupe."""
        self.actual_group = group_name
        print(f"Rejoint le groupe : {group_name}")
        if self.ui:
            texting_page: TextingPage = self.ui.frames[TextingPage]
            texting_page.update_group(group_name)


# Interface utilisateur principal
class ClientUi(Tk):
    def __init__(self):
        super().__init__()
        self.client_network = ClientNetwork("Utilisateur", self)  # Instance de ClientNetwork

        # Configuration de la fenêtre
        self.geometry("1400x1024")
        self.title("RSCHAT")

        # Initialisation du thème
        self.theme = "light"
        self.colors = {
            "light": {"bg": "#E2D0F8", "fg": "#317874", "button": "#B5A8A8", "canvas": "#317874"},
            "dark": {"bg": "#2C2C2C", "fg": "#E2D0F8", "button": "#444444", "canvas": "#1E1E1E"}
        }

        # Fenêtre principale
        window = Frame(self)
        window.pack(side="top", fill="both", expand=True)
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)

        # Création des différentes pages
        self.frames = {}
        for F in (LoginPage, LandingPage, GroupCreationPage, TextingPage):
            frame = F(window, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginPage)

    def show_frame(self, page):
        """Affiche la page demandée."""
        frame = self.frames[page]
        frame.tkraise()

    def toggle_theme(self):
        """Bascule entre mode clair et mode sombre."""
        self.theme = "dark" if self.theme == "light" else "light"
        for frame in self.frames.values():
            frame.update_theme()


# Fonctions pour les différentes pages
class ThemedFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.button_images = {}  # Stocke les images des boutons pour chaque thème
        self.update_theme()

    def update_theme(self):
        colors = self.controller.colors[self.controller.theme]
        self.configure(bg=colors["bg"])
        for widget in self.winfo_children():
            if isinstance(widget, (Label, Entry)):
                widget.configure(bg=colors["bg"], fg=colors["fg"])
            elif isinstance(widget, Button):
                widget.configure(bg=colors["bg"], fg=colors["fg"],highlightbackground=colors["bg"],activebackground=colors["bg"])
                # Mise à jour de l'image si le bouton est enregistré avec un thème
                if hasattr(widget, "image_key") and widget.image_key in self.button_images:
                    widget.configure(image=self.button_images[widget.image_key][self.controller.theme])
            elif isinstance(widget, Canvas):
                widget.configure(bg=colors["canvas"])

    def add_button_image(self, button, image_key, light_image_path, dark_image_path):
        """Ajoute une image associée à un bouton pour chaque thème."""
        light_image = PhotoImage(file=light_image_path) if os.path.exists(light_image_path) else None
        dark_image = PhotoImage(file=dark_image_path) if os.path.exists(dark_image_path) else None
        self.button_images[image_key] = {"light": light_image, "dark": dark_image}
        button.image_key = image_key  # Attribut pour suivre le bouton
        button.configure(image=self.button_images[image_key][self.controller.theme])

    def change_button_image(self, button, gicp, picp,gisp,pisp):
        """Toggle button pour lister les groupes ou les gens."""
        if not hasattr(button, 'state'):
            button.state = 'group'
        if self.controller.theme == "light":
            print("claiiiir")
            gic = PhotoImage(file=gicp) if os.path.exists(gicp) else None
            pic = PhotoImage(file=picp) if os.path.exists(picp) else None
            button.images = {
                'group': gic,
                'people': pic
            }
        else : 
            print("sombre")
            gis = PhotoImage(file=gisp) if os.path.exists(gisp) else None
            pis = PhotoImage(file=pisp) if os.path.exists(pisp) else None
            button.images = {
                'group':  gis,
                'people': pis
            }
        button.state = 'people' if button.state == 'group' else 'group'
        button.configure(image=button.images[button.state])


# Page de connexion
class LoginPage(ThemedFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

    # Configuration de la grille
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1) 
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)

    #Colonne gauche :
        # CONNEXION
        Label(self, text="CONNEXION", fg="#317874", bg="#E2D0F8", font=("Montserrat", 32, "bold")).grid(column=0, row=1, pady=10)

        # Pseudo
        Label(self, text="Pseudo",  fg="#317874", bg="#E2D0F8",font=("Montserrat", 16, "bold")).grid(column=0, row=3, sticky="sw", padx=50, pady=(5, 0))

        # Case pour entrer le pseudo utilisateur
        user_entry = Entry(
            self,
            bd=4,
            highlightthickness=4,
            highlightbackground="#cccccc",
            highlightcolor="#317874",
            font=("Montserrat", 14)
        )
        user_entry.grid(column=0, row=4, padx=50, sticky="ew")
        user_entry.config(width=25) 

        # Bouton Entree
        button_image_path = "assets/frame0/entry_button.png"
        self.button_entry_image = PhotoImage(file=button_image_path) if os.path.exists(button_image_path) else None
        Button(
            self, image=self.button_entry_image, relief="flat",
            command=lambda: [print(f"{user_entry.get()}"), controller.show_frame(LandingPage)]
        ).grid(column=0, row=6, pady=20)

    #Colone droite :
        #Rectangle bleu
        self.rectangle_bleu_image = PhotoImage(file="assets/frame0/rectangle_bleu.png")
        rectangle_bleu = Label(self, image=self.rectangle_bleu_image, bg="#317874")
        rectangle_bleu.grid(column=1, row=0, rowspan=10, columnspan=1, sticky="nsew")

    #Ancinne colonne droite
        # # Titre "RSCHAT" sur la droite
        # canvas = Canvas(self, width=400, height=1024, bg="#317874", highlightthickness=0)
        # canvas.grid(column=1, row=0, rowspan=10, sticky="nswe")
        # Label(self, text="RSCHAT", font=("Montserrat", 32, "bold"), fg="#E2D0F8", bg="#317874").grid(column=1, row=3)

        # # Image en dessous du titre (réduction de la taille)
        # logo_image_path = "assets/frame0/logo_chat.png"
        # if os.path.exists(logo_image_path):
        #     self.logo_image = PhotoImage(file=logo_image_path).subsample(2, 2)  # Divise la taille par 2
        #     Label(self, image=self.logo_image, bg="#317874").grid(column=1, row=4)


class LandingPage(ThemedFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)

    # Colonne gauche
        #RSCHAT
        Label(self, text="RSCHAT", bg="#E2D0F8", fg="#317874", font=("Montserrat", 24, "bold")).grid(column=0, row=0, sticky="w")

        # Bouton pour changer le thème
        theme_button = Button(self, relief="flat", bd=0, bg="#E2D0F8", activebackground="#E2D0F8", highlightbackground="#E2D0F8", command=controller.toggle_theme)
        self.add_button_image(
            theme_button,
            image_key="theme_switch",
            light_image_path="assets/frame1/theme_switch_clair.png",
            dark_image_path="assets/frame1/theme_switch_sombre.png"
        )
        theme_button.grid(column=0, row=1)

        # Bouton pour créer un groupe
        group_button = Button(self, relief="flat", bd=0, bg="#E2D0F8", activebackground="#E2D0F8", highlightbackground="#E2D0F8", command=lambda: controller.show_frame(GroupCreationPage))
        self.add_button_image(
            group_button,
            image_key="group_create",
            light_image_path="assets/frame1/group_create_clair.png",
            dark_image_path="assets/frame1/group_create_sombre.png"
        )
        group_button.grid(column=0, row=2)

    # Colonne droite
        # Rectangle bleu/gris
        canvas1 = Canvas(self, bg="#317874", highlightthickness=0)
        canvas1.grid(column=1, row=0, rowspan=10, sticky="nsew")

        # Groupchat_button (basculer entre la page des groupes et personnes)
        groupchat_button = Button(self, relief="flat", bd=0, bg="#317874", activebackground="#317874", highlightbackground="#317874")
        groupchat_button.configure(command=lambda: self.change_button_image(groupchat_button, "assets/frame1/groups_button_clair.png", "assets/frame1/people_button_clair.png","assets/frame1/groups_button_sombre.png","assets/frame1/people_button_sombre.png"))
        groupchat_button.grid(column=1, row=0)
        self.add_button_image(
            groupchat_button,
            image_key="groups_button",
            light_image_path="assets/frame1/groups_button_clair.png",
            dark_image_path="assets/frame1/groups_button_sombre.png"
        )

        # Exemple de Peoplechat_button (Redirection vers les pages de convo)
        peoplechat_button = Button(self, relief="flat", bd=0, bg="#317874", activebackground="#317874", highlightbackground="#317874", command=lambda: [print("Affiche les discussions privées"),controller.show_frame(TextingPage)])
        self.add_button_image(
            peoplechat_button,
            image_key="peoplechat_button",
            light_image_path="assets/frame1/groupchat_button_clair.png",
            dark_image_path="assets/frame1/groupchat_button_sombre.png"
        )
        peoplechat_button.grid(column=1, row=2)
        Label(self, text="Exemple d'affichage de convo", bg="#E2D0F8", fg="black", font=("Montserrat", 12, "normal")).grid(column=1, row=2)


# Page de création du groupe
class GroupCreationPage(ThemedFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Configuration de la grille :
        self.grid_columnconfigure(0, weight=1)
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)
        self.configure(bg="#317874")

        #RSCHAT
        Label(self, text="RSCHAT", bg="#317874", fg="#E2D0F8", font=("Montserrat", 24, "bold")).grid(column=0, row=1, sticky="nw")

        #Rectangle principal 
        grouppad = Button(self, relief="flat", bd=0, bg="#317874", activebackground="#317874", highlightbackground="#317874")
        self.add_button_image(
            grouppad,
            image_key="grouppad_button",
            light_image_path="assets/frame2/grouppad_clair.png",
            dark_image_path="assets/frame2/grouppad_sombre.png"
        )
        grouppad.grid(column=0,row=1)
        
        # Entry du groupname
        groupname_entry = Entry(self, bd=0, highlightthickness=0, bg="#317874", fg="#ffffff")
        groupname_entry.grid(column=0, row=1, ipadx=230, ipady=10)

        # Bouton valider
        valider_button = Button(self, relief="flat", bd=0, bg="#317874", activebackground="#317874", highlightbackground="#317874", command=lambda: [print(f"{groupname_entry.get()}"), controller.show_frame(LandingPage)])
        self.add_button_image(
            valider_button,
            image_key="groupname_entry_button",
            light_image_path="assets/frame2/valider_button_clair.png",
            dark_image_path="assets/frame2/valider_button_sombre.png"
        )
        valider_button.grid(column=0,row=2)

#a finir
class TextingPage(ThemedFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.client_network = controller.client_network
        self.client_network.display_callback = self.display_message

        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)  # Colonne gauche (groupes)
        self.grid_columnconfigure(1, weight=3)  # Colonne droite (messages)
        self.grid_rowconfigure(1, weight=1)  # Zone principale

        # === SECTION GAUCHE : LISTE DES GROUPES + RETOUR ===
        self.group_frame = Frame(self, bg=self.controller.colors[self.controller.theme]["canvas"])
        self.group_frame.grid(column=0, row=0, rowspan=3, sticky="nsew", padx=10, pady=10)
        self.group_frame.grid_rowconfigure(0, weight=1)

        # Bouton Retour
        back_button = Button(
            self.group_frame, text="Retour", font=("Montserrat", 12, "bold"),
            bg=self.controller.colors[self.controller.theme]["button"],
            fg=self.controller.colors[self.controller.theme]["fg"],
            command=lambda: controller.show_frame(LandingPage)
        )
        back_button.pack(pady=10, padx=10, fill="x")

        # Label pour les groupes
        Label(
            self.group_frame, text="Groupes", font=("Montserrat", 16, "bold"),
            bg=self.controller.colors[self.controller.theme]["canvas"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        ).pack(pady=10)

        # Liste des groupes
        self.groups_list = ["Groupe 1", "Groupe 2", "Groupe 3"]
        for group in self.groups_list:
            Button(
                self.group_frame, text=group, font=("Montserrat", 12),
                bg=self.controller.colors[self.controller.theme]["bg"],
                fg=self.controller.colors[self.controller.theme]["fg"],
                command=lambda g=group: self.client_network.join_group(g)
            ).pack(fill="x", pady=5)

        # === SECTION DROITE : MESSAGES DU GROUPE ===
        # Nom du groupe
        self.group_label = Label(
            self, text="Nom du groupe (en attente)", font=("Montserrat", 24, "bold"),
            bg=self.controller.colors[self.controller.theme]["bg"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        )
        self.group_label.grid(column=1, row=0, pady=10, padx=10, sticky="ew")

        # Cadre pour les messages avec un canvas (zone défilante)
        message_frame_container = Frame(self, bg=self.controller.colors[self.controller.theme]["bg"])
        message_frame_container.grid(column=1, row=1, sticky="nsew", pady=10, padx=10)
        message_frame_container.grid_rowconfigure(0, weight=1)
        message_frame_container.grid_columnconfigure(0, weight=1)

        self.message_canvas = Canvas(
            message_frame_container, bg=self.controller.colors[self.controller.theme]["bg"], highlightthickness=0
        )
        self.message_canvas.grid(column=0, row=0, sticky="nsew")

        self.message_scrollbar = Frame(self.message_canvas)
        self.message_canvas.create_window((0, 0), window=self.message_scrollbar, anchor="nw")

        self.message_scrollbar.bind(
            "<Configure>",
            lambda event: self.message_canvas.configure(scrollregion=self.message_canvas.bbox("all"))
        )

        # Champ de saisie pour les messages
        self.entry_message = Entry(
            self, font=("Montserrat", 14),
            bg=self.controller.colors[self.controller.theme]["bg"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        )
        self.entry_message.grid(column=1, row=2, sticky="ew", padx=10, pady=10)

        # Bouton d'envoi
        send_button = Button(
            self, text="Envoyer", command=self.send_message,
            bg=self.controller.colors[self.controller.theme]["button"],
            fg=self.controller.colors[self.controller.theme]["fg"]
        )
        send_button.grid(column=1, row=3, sticky="ew", padx=10, pady=10)

    def display_message(self, content, sender):
        """Affiche un message reçu dans la zone des messages."""
        message_label = Label(
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
        """Gère l'envoi d'un message."""
        message = self.entry_message.get()
        if message.strip() and self.client_network.actual_group:
            self.client_network.send_message(
                entries={"content": message},
                target=self.client_network.actual_group,
            )
            self.display_message(message, "Moi")  # Affiche immédiatement dans l'interface
            self.entry_message.delete(0, "end")

    def update_group(self, group_name):
        """Met à jour le nom du groupe actif."""
        self.group_label.config(text=f"Conversation : {group_name}")


if __name__ == "__main__":
    client_ui = ClientUi()
    client_ui.mainloop()
