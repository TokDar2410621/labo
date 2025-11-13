"""
Interface Tkinter moderne pour la connexion à la base de données
Design amélioré avec couleurs, icônes et animations
"""

import tkinter as tk
from tkinter import ttk, messagebox
from db_connection import DatabaseConnection
import json
import os


class InterfaceConnexionModerne:
    """Interface graphique moderne pour se connecter à la base de données"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SalleSense")
        self.root.geometry("600x700")
        self.root.resizable(False, False)

        # Couleurs modernes
        self.colors = {
            'primary': '#2563eb',      # Bleu
            'secondary': '#8b5cf6',    # Violet
            'success': '#10b981',      # Vert
            'danger': '#ef4444',       # Rouge
            'warning': '#f59e0b',      # Orange
            'dark': '#1e293b',         # Gris foncé
            'light': '#f8fafc',        # Blanc cassé
            'gray': '#64748b',         # Gris
            'bg': '#f1f5f9'           # Fond
        }

        self.root.configure(bg=self.colors['bg'])

        # Variables
        self.server_var = tk.StringVar(value="DICJWIN01.cegepjonquiere.ca")
        self.database_var = tk.StringVar(value="Prog3A25_bdSalleSense")
        self.db_username_var = tk.StringVar(value="prog3e09")
        self.db_password_var = tk.StringVar(value="colonne42")
        self.email_var = tk.StringVar(value="")
        self.password_var = tk.StringVar(value="")

        self.db = None
        self.user_info = None

        # Charger config
        self.charger_config()

        # Créer l'interface
        self.creer_interface()

        # Centrer la fenêtre
        self.centrer_fenetre()

    def centrer_fenetre(self):
        """Centre la fenêtre sur l'écran"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def charger_config(self):
        """Charge la configuration"""
        if os.path.exists("db_config.json"):
            try:
                with open("db_config.json", 'r') as f:
                    config = json.load(f)
                    self.email_var.set(config.get('email', ''))
            except:
                pass

    def sauvegarder_config(self):
        """Sauvegarde la configuration"""
        config = {
            'server': self.server_var.get(),
            'database': self.database_var.get(),
            'db_username': self.db_username_var.get(),
            'email': self.email_var.get()
        }
        try:
            with open("db_config.json", 'w') as f:
                json.dump(config, f, indent=2)
        except:
            pass

    def creer_interface(self):
        """Crée l'interface graphique moderne"""
        # Frame de fond
        bg_frame = tk.Frame(self.root, bg=self.colors['bg'])
        bg_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        # Frame principal avec effet de carte
        main_frame = tk.Frame(bg_frame, bg='white', relief=tk.RAISED, borderwidth=2)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header avec gradient (simulé)
        header = tk.Frame(main_frame, bg=self.colors['primary'], height=150)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Logo/Icône
        logo_frame = tk.Frame(header, bg=self.colors['primary'])
        logo_frame.pack(expand=True)

        tk.Label(logo_frame, text='🏢', font=('Arial', 48),
                bg=self.colors['primary'], fg='white').pack()

        # Titre
        titre = tk.Label(header, text='SalleSense',
                        font=('Arial', 24, 'bold'),
                        fg='white', bg=self.colors['primary'])
        titre.pack()

        sous_titre = tk.Label(header, text='Système de Surveillance Intelligente',
                             font=('Arial', 11),
                             fg='#e0e7ff', bg=self.colors['primary'])
        sous_titre.pack(pady=(0, 10))

        # Contenu
        content = tk.Frame(main_frame, bg='white', padx=40, pady=30)
        content.pack(fill=tk.BOTH, expand=True)

        # Section Email
        email_label = tk.Label(content, text='Adresse Email',
                              font=('Arial', 10, 'bold'),
                              fg=self.colors['dark'], bg='white',
                              anchor=tk.W)
        email_label.pack(fill=tk.X, pady=(0, 5))

        email_frame = tk.Frame(content, bg='white')
        email_frame.pack(fill=tk.X, pady=(0, 20))

        # Icône email
        email_icon = tk.Label(email_frame, text='📧',
                             font=('Arial', 16),
                             bg='white')
        email_icon.pack(side=tk.LEFT, padx=(0, 10))

        # Entry avec style
        email_entry = tk.Entry(email_frame, textvariable=self.email_var,
                              font=('Arial', 12),
                              relief=tk.FLAT,
                              bg='#f8fafc',
                              fg=self.colors['dark'],
                              insertbackground=self.colors['primary'])
        email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)

        # Bordure inférieure
        email_border = tk.Frame(email_frame, height=2, bg=self.colors['primary'])
        email_border.pack(fill=tk.X)

        # Section Mot de passe
        pwd_label = tk.Label(content, text='Mot de passe',
                            font=('Arial', 10, 'bold'),
                            fg=self.colors['dark'], bg='white',
                            anchor=tk.W)
        pwd_label.pack(fill=tk.X, pady=(0, 5))

        pwd_frame = tk.Frame(content, bg='white')
        pwd_frame.pack(fill=tk.X, pady=(0, 30))

        # Icône mot de passe
        pwd_icon = tk.Label(pwd_frame, text='🔒',
                           font=('Arial', 16),
                           bg='white')
        pwd_icon.pack(side=tk.LEFT, padx=(0, 10))

        # Entry mot de passe
        pwd_entry = tk.Entry(pwd_frame, textvariable=self.password_var,
                            font=('Arial', 12),
                            relief=tk.FLAT,
                            bg='#f8fafc',
                            fg=self.colors['dark'],
                            show='●',
                            insertbackground=self.colors['primary'])
        pwd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)

        # Bordure
        pwd_border = tk.Frame(pwd_frame, height=2, bg=self.colors['primary'])
        pwd_border.pack(fill=tk.X)

        # Bouton de connexion moderne
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(fill=tk.X, pady=(0, 20))

        self.btn_connexion = tk.Button(btn_frame, text='Se Connecter',
                                       font=('Arial', 12, 'bold'),
                                       fg='white',
                                       bg=self.colors['primary'],
                                       activebackground=self.colors['secondary'],
                                       activeforeground='white',
                                       relief=tk.FLAT,
                                       cursor='hand2',
                                       command=self.se_connecter)
        self.btn_connexion.pack(fill=tk.X, ipady=12)

        # Effet hover
        self.btn_connexion.bind('<Enter>', lambda e: self.btn_connexion.config(bg=self.colors['secondary']))
        self.btn_connexion.bind('<Leave>', lambda e: self.btn_connexion.config(bg=self.colors['primary']))

        # Status label avec style
        self.status_frame = tk.Frame(content, bg='white')
        self.status_frame.pack(fill=tk.X)

        self.status_label = tk.Label(self.status_frame, text='',
                                     font=('Arial', 10),
                                     bg='white',
                                     fg=self.colors['gray'])
        self.status_label.pack()

        # Footer
        footer = tk.Frame(content, bg='white')
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        info = tk.Label(footer,
                       text='🔐 Authentification sécurisée avec SHA2-256',
                       font=('Arial', 8),
                       fg=self.colors['gray'],
                       bg='white')
        info.pack()

        version = tk.Label(footer,
                          text='Version 1.0 | © 2025 SalleSense',
                          font=('Arial', 8),
                          fg='#cbd5e1',
                          bg='white')
        version.pack(pady=(5, 0))

        # Bind Enter
        self.root.bind('<Return>', lambda e: self.se_connecter())

    def afficher_status(self, message, type_msg='info'):
        """Affiche un message de status stylisé"""
        colors = {
            'info': ('#60a5fa', '#dbeafe'),
            'success': (self.colors['success'], '#d1fae5'),
            'error': (self.colors['danger'], '#fee2e2'),
            'warning': (self.colors['warning'], '#fef3c7')
        }

        icons = {
            'info': '⏳',
            'success': '✓',
            'error': '✗',
            'warning': '⚠'
        }

        fg, bg = colors.get(type_msg, colors['info'])
        icon = icons.get(type_msg, 'ℹ')

        self.status_frame.config(bg=bg)
        self.status_label.config(text=f'{icon} {message}', fg=fg, bg=bg)

    def se_connecter(self):
        """Connexion avec animation"""
        email = self.email_var.get().strip()
        password = self.password_var.get()

        if not email or not password:
            self.afficher_status('Veuillez remplir tous les champs', 'error')
            return

        # Désactiver le bouton
        self.btn_connexion.config(state=tk.DISABLED, text='Connexion...')
        self.afficher_status('Connexion en cours...', 'info')
        self.root.update()

        try:
            # Connexion BD
            server = self.server_var.get().strip()
            database = self.database_var.get().strip()
            db_username = self.db_username_var.get().strip()
            db_password = self.db_password_var.get()

            self.db = DatabaseConnection(server, database, db_username, db_password)

            if not self.db.connect():
                self.afficher_status('Échec de connexion au serveur', 'error')
                self.btn_connexion.config(state=tk.NORMAL, text='Se Connecter')
                return

            # Authentification
            self.afficher_status('Authentification...', 'info')
            self.root.update()

            user_id = self.db.login_user(email, password)

            if user_id > 0:
                self.afficher_status('Connexion réussie!', 'success')

                # Récupérer infos utilisateur
                user = self.db.get_user_by_id(user_id)
                if user:
                    self.user_info = user
                else:
                    self.user_info = {
                        'id': user_id,
                        'pseudo': email.split('@')[0],
                        'courriel': email
                    }

                self.sauvegarder_config()

                # Ouvrir interface principale après 500ms
                self.root.after(500, self.ouvrir_interface_principale)
            else:
                self.afficher_status('Email ou mot de passe incorrect', 'error')
                self.btn_connexion.config(state=tk.NORMAL, text='Se Connecter')

        except Exception as e:
            self.afficher_status(f'Erreur: {str(e)[:30]}', 'error')
            self.btn_connexion.config(state=tk.NORMAL, text='Se Connecter')

    def ouvrir_interface_principale(self):
        """Ouvre l'interface principale"""
        self.root.destroy()
        from interface_principale import InterfacePrincipaleModerne
        app = InterfacePrincipaleModerne(self.db, self.user_info)
        app.run()

    def run(self):
        """Lance l'application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = InterfaceConnexionModerne()
    app.run()
