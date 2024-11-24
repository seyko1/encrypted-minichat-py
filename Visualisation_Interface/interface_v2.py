from tkinter import Tk, Frame, Label, Entry, Button, PhotoImage, Canvas

class ClientUi(Tk):
    def __init__(self):
        super().__init__()
    # On utilise des frames pour plus de responsivité
        window = Frame(self)
        self.geometry("1400x1024")
        window.pack(side="top", fill="both", expand=True)
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)

    #On creer un diictionnaire pour stocker les differentes pages
        self.frames = {}

        for F in (LoginPage, LandingPage, TextingPage):
            frame = F(window, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginPage)

    def show_frame(self, window):
        frame = self.frames[window]
        frame.tkraise() #push la page en avant

class LoginPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        
        self.configure(bg="#E2D0F8")
    #Configuration de la grille
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        for i in range(10):
            self.grid_rowconfigure(i, weight=1)
        

    #Colonne gauche
        # Connexion
        label_connexion = Label(self, text="CONNEXION", bg="#E2D0F8", fg="#317874", font=("Montserrat", 32, "bold"))
        label_connexion.grid(column=0, row=1)

        # Pseudo
        label_pseudo = Label(self, text='Pseudo', bg="#E2D0F8", fg="#317874", font=("Montserrat", 16, "bold"))
        label_pseudo.grid(column=0, row=3,  sticky='w', padx= 100)

        # Entrée utilisateur
        user_entry = Entry(self, bd=0, bg="#B5A8A8", fg="#000716", highlightthickness=0)
        user_entry.grid(column=0, row=4, sticky='nswe', padx=100)

        # Bouton de connexion
        self.button_entry_image = PhotoImage(file="assets/frame0/entry_button.png")
        button_entry = Button(self, image=self.button_entry_image, relief="flat", 
                              command=lambda: print(f"{user_entry.get()}"))
        button_entry.grid(column=0, row=7)

    # Colonne droite
        # Rectangle bleu
        canvas = Canvas(self, width=400, height=1024, bg="#317874", highlightthickness=0)
        canvas.grid(column=1, row=0, rowspan=10, sticky="nswe")
        
        #RSCHAT
        label_rschat = Label(self, text='RSCHAT',bg="#317874", fg="#E2D0F8", font=("Montserrat", 32, "bold"))
        label_rschat.grid(column=1, row=4)

        # Boutons de navigation pour les autres pages 
        button_landing = Button(self, text="Landing", command=lambda: controller.show_frame(LandingPage))
        button_landing.grid(column=0, row=4, pady=10)

        button_texting = Button(self, text="Texting", command=lambda: controller.show_frame(TextingPage))
        button_texting.grid(column=0, row=5, pady=10)

class LandingPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        label = Label(self, text="Page One")
        label.pack(pady=10, padx=10)
    #On créer deux frames, une pour les convos de groupes et une autre pour les convos persos
    #Groupchats
        
        # Toggle button

        # button1 = Button(self, text="Login", command=lambda: controller.show_frame(LoginPage))
        # button1.pack()

        # button2 = Button(self, text="Texting", command=lambda: controller.show_frame(TextingPage))
        # button2.pack()

class TextingPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        label = Label(self, text="Page Two")
        label.pack(pady=10, padx=10)

        button1 = Button(self, text="Login", command=lambda: controller.show_frame(LoginPage))
        button1.pack()

        button2 = Button(self, text="Landing", command=lambda: controller.show_frame(LandingPage))
        button2.pack()

if __name__ == "__main__":
    client_ui = ClientUi()
    client_ui.mainloop()
