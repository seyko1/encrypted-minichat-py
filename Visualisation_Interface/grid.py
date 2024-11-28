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


# Interface utilisateur principale
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

        # Conteneur principal
        window = Frame(self)
        window.pack(side="top", fill="both", expand=True)
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)

        # Création des différentes pages
        self.frames = {}
        for F in (LoginPage, LandingPage, TextingPage):
            frame = F(window, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LandingPage)

    def show_frame(self, page):
        """Affiche la page demandée."""
        frame = self.frames[page]
        frame.tkraise()

    def toggle_theme(self):
        """Bascule entre mode clair et mode sombre."""
        self.theme = "dark" if self.theme == "light" else "light"
        for frame in self.frames.values():
            frame.update_theme()


# Classes pour les différentes pages
class ThemedFrame(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.update_theme()

    def update_theme(self):
        colors = self.controller.colors[self.controller.theme]
        self.configure(bg=colors["bg"])
        for widget in self.winfo_children():
            if isinstance(widget, (Label, Button, Entry)):
                widget.configure(bg=colors["bg"], fg=colors["fg"])
            elif isinstance(widget, Canvas):
                widget.configure(bg=colors["canvas"])


class LoginPage(ThemedFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)

        Label(self, text="Connexion", font=("Montserrat", 32, "bold"), bg="#E2D0F8", fg ="#317874").grid(column=0, row=1)
        Label(self, text="Pseudo", font=("Montserrat", 16, "bold"), bg="#E2D0F8", fg ="#317874").grid(column=0, row=3, sticky="w", padx=100)
        self.nickname_entry_image = PhotoImage(file="assets/frame0/nickname_entry.png")
        Label(self,image=self.nickname_entry_image).grid(column=0, row=4)
        user_entry = Entry(self,bd=0, highlightthickness=0, bg="#317874", fg="#ffffff")
        user_entry.grid(column=0, row=4, sticky="nsew", padx=110, pady=50)

        button_image_path = "assets/frame0/entry_button.png"
        self.button_entry_image = PhotoImage(file=button_image_path) if os.path.exists(button_image_path) else None
        Button(
            self, image=self.button_entry_image, relief="flat", highlightthickness=0, bd=0,
            command=lambda: [print(f"{user_entry.get()}"), controller.show_frame(LandingPage)]
        ).grid(column=0, row=7)

        canvas = Canvas(self, width=400, height=1024, bg="#317874", highlightthickness=0)
        canvas.grid(column=1, row=0, rowspan=10, sticky="nswe")
        Label(self, text="RSCHAT", font=("Montserrat", 32, "bold"), fg="#E2D0F8", bg="#317874").grid(column=1, row=3)


class LandingPage(ThemedFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)

        # Boutons d'action
        self.theme_switch_clair_image = PhotoImage(file="assets/frame1/theme_switch_clair.png")
        self.group_create_clair_image = PhotoImage(file="assets/frame1/group_create_clair.png")
        Button(self, image=self.theme_switch_clair_image, command=controller.toggle_theme, relief="flat", bd=0).grid(column=0, row=1)
        Button(self, image=self.group_create_clair_image, 
               command=lambda: controller.show_frame(TextingPage), relief="flat", bd=0).grid(column=0, row=2)

        # Rectangle bleu/alternatif
        canvas1 = Canvas(self, bg="#317874", highlightthickness=0)
        canvas1.grid(column=1, row=0, rowspan=10, sticky="nsew")

        # Toggle button groups
        self.toggle_button_groups_clair_image = PhotoImage(file="assets/frame1/groups_button_clair.png")
        toggle_button_groups = Button(self, image=self.toggle_button_groups_clair_image,bd = 0, relief="flat",
                                      command=lambda: print("On switch vers la page de people"))
        toggle_button_groups.grid(column=1, row=0)

        # Affichage des groupes en ligne
        self.groupchat_button_image = PhotoImage(file="assets/frame1/groupchat_button_clair.png")
        groupchat_button = Button(self, image=self.groupchat_button_image, relief="flat", 
                                  command=lambda: print("On entre dans ce groupe"))
        groupchat_button.grid(column=1, row=1)

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
