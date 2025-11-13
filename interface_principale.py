"""
Interface principale moderne avec visualisation des données en temps réel
Design amélioré avec couleurs, cartes, et animations
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
import time
from io import BytesIO
from PIL import Image, ImageTk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class InterfacePrincipaleModerne:
    """Interface principale moderne pour visualiser les données en temps réel"""

    def __init__(self, db_connection, user_info=None):
        self.root = tk.Tk()
        self.root.title("SalleSense")
        self.root.geometry("1400x800")

        # Couleurs modernes (même palette que l'interface de connexion)
        self.colors = {
            'primary': '#2563eb',      # Bleu
            'secondary': '#8b5cf6',    # Violet
            'success': '#10b981',      # Vert
            'danger': '#ef4444',       # Rouge
            'warning': '#f59e0b',      # Orange
            'dark': '#1e293b',         # Gris foncé
            'light': '#f8fafc',        # Blanc cassé
            'gray': '#64748b',         # Gris
            'bg': '#f1f5f9',           # Fond
            'card': '#ffffff',         # Carte blanche
            'border': '#e2e8f0'        # Bordure
        }

        self.root.configure(bg=self.colors['bg'])

        self.db = db_connection
        self.user_info = user_info or {}

        # Variables de contrôle
        self.en_cours = True
        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval = 2000  # ms

        # Données
        self.derniere_mesure_son = None
        self.derniere_photo = None

        # Créer l'interface
        self.creer_interface()

        # Lancer le rafraîchissement automatique
        self.rafraichir_donnees()

        # Gérer la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.fermer)

    def creer_carte(self, parent, title=None):
        """Crée un widget carte avec ombre"""
        # Container principal (ombre simulée par la bordure)
        shadow = tk.Frame(parent, bg='#cbd5e1', relief=tk.RAISED, borderwidth=1)
        shadow.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Carte principale
        card = tk.Frame(shadow, bg=self.colors['card'], relief=tk.FLAT)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        if title:
            header = tk.Frame(card, bg=self.colors['primary'], height=50)
            header.pack(fill=tk.X)
            header.pack_propagate(False)

            tk.Label(header, text=title, font=('Arial', 14, 'bold'),
                    fg='white', bg=self.colors['primary']).pack(pady=12)

        return card

    def creer_interface(self):
        """Crée l'interface graphique moderne"""
        # Header moderne
        header = tk.Frame(self.root, bg=self.colors['primary'], height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Left side - Logo et titre
        left_header = tk.Frame(header, bg=self.colors['primary'])
        left_header.pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(left_header, text='🏢 SalleSense Dashboard',
                font=('Arial', 18, 'bold'),
                fg='white', bg=self.colors['primary']).pack(side=tk.LEFT)

        # Right side - User info et actions
        right_header = tk.Frame(header, bg=self.colors['primary'])
        right_header.pack(side=tk.RIGHT, padx=20, pady=10)

        # User info
        user_frame = tk.Frame(right_header, bg='white', relief=tk.FLAT)
        user_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(user_frame, text=f"👤 {self.user_info.get('pseudo', 'Utilisateur')}",
                font=('Arial', 10, 'bold'),
                fg=self.colors['dark'], bg='white',
                padx=15, pady=8).pack()

        # Bouton rafraîchir moderne
        self.btn_refresh = tk.Button(right_header, text='🔄 Rafraîchir',
                                     font=('Arial', 10, 'bold'),
                                     fg='white',
                                     bg=self.colors['secondary'],
                                     activebackground=self.colors['warning'],
                                     activeforeground='white',
                                     relief=tk.FLAT,
                                     cursor='hand2',
                                     command=self.rafraichir_maintenant,
                                     padx=20, pady=8)
        self.btn_refresh.pack(side=tk.LEFT, padx=5)

        # Effet hover
        self.btn_refresh.bind('<Enter>', lambda e: self.btn_refresh.config(bg=self.colors['warning']))
        self.btn_refresh.bind('<Leave>', lambda e: self.btn_refresh.config(bg=self.colors['secondary']))

        # Bouton déconnexion
        self.btn_deconnexion = tk.Button(right_header, text='🚪 Déconnexion',
                                         font=('Arial', 10),
                                         fg='white',
                                         bg=self.colors['danger'],
                                         activebackground='#dc2626',
                                         activeforeground='white',
                                         relief=tk.FLAT,
                                         cursor='hand2',
                                         command=self.deconnecter,
                                         padx=15, pady=8)
        self.btn_deconnexion.pack(side=tk.LEFT, padx=5)

        self.btn_deconnexion.bind('<Enter>', lambda e: self.btn_deconnexion.config(bg='#dc2626'))
        self.btn_deconnexion.bind('<Leave>', lambda e: self.btn_deconnexion.config(bg=self.colors['danger']))

        # Status bar
        status_bar = tk.Frame(self.root, bg=self.colors['dark'], height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.last_update_label = tk.Label(status_bar,
                                          text="⏰ Dernière mise à jour: --:--:--",
                                          font=('Arial', 9),
                                          fg='white',
                                          bg=self.colors['dark'])
        self.last_update_label.pack(side=tk.RIGHT, padx=15)

        self.status_indicator = tk.Label(status_bar,
                                         text="● Connexion active",
                                         font=('Arial', 9),
                                         fg=self.colors['success'],
                                         bg=self.colors['dark'])
        self.status_indicator.pack(side=tk.LEFT, padx=15)

        # Notebook moderne (onglets)
        style = ttk.Style()
        style.theme_use('default')

        style.configure('Modern.TNotebook', background=self.colors['bg'], borderwidth=0)
        style.configure('Modern.TNotebook.Tab',
                       background=self.colors['card'],
                       foreground=self.colors['dark'],
                       padding=[20, 10],
                       font=('Arial', 11, 'bold'))
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', 'white')])

        self.notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Onglets
        self.creer_onglet_temps_reel()
        self.creer_onglet_graphique()
        self.creer_onglet_galerie()
        self.creer_onglet_historique()
        self.creer_onglet_statistiques()

    def creer_onglet_temps_reel(self):
        """Crée l'onglet de visualisation en temps réel moderne"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="📊 Temps Réel")

        # Top frame - Indicateurs en cartes
        top_frame = tk.Frame(frame, bg=self.colors['bg'])
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Carte 1: Niveau Sonore
        son_card_container = tk.Frame(top_frame, bg=self.colors['bg'])
        son_card_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        son_card = self.creer_carte(son_card_container)

        # Contenu carte son
        son_content = tk.Frame(son_card, bg=self.colors['card'], padx=30, pady=20)
        son_content.pack(fill=tk.BOTH, expand=True)

        tk.Label(son_content, text="🎤 Niveau Sonore",
                font=('Arial', 14, 'bold'),
                fg=self.colors['dark'], bg=self.colors['card']).pack(pady=(0, 10))

        self.son_value_label = tk.Label(son_content, text="-- dB",
                                        font=('Arial', 40, 'bold'),
                                        fg=self.colors['primary'],
                                        bg=self.colors['card'])
        self.son_value_label.pack(pady=10)

        # Barre de progression moderne
        self.son_progress_frame = tk.Frame(son_content, bg=self.colors['border'],
                                          height=30, relief=tk.FLAT)
        self.son_progress_frame.pack(fill=tk.X, pady=10)
        self.son_progress_frame.pack_propagate(False)

        self.son_progress_bar = tk.Frame(self.son_progress_frame,
                                         bg=self.colors['primary'],
                                         width=0)
        self.son_progress_bar.place(x=0, y=0, relheight=1.0)

        self.son_time_label = tk.Label(son_content, text="Aucune donnée",
                                       font=('Arial', 10),
                                       fg=self.colors['gray'],
                                       bg=self.colors['card'])
        self.son_time_label.pack(pady=(10, 0))

        # Carte 2: Média
        media_card_container = tk.Frame(top_frame, bg=self.colors['bg'])
        media_card_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        media_card = self.creer_carte(media_card_container)

        media_content = tk.Frame(media_card, bg=self.colors['card'], padx=30, pady=20)
        media_content.pack(fill=tk.BOTH, expand=True)

        tk.Label(media_content, text="📹 Captures Média",
                font=('Arial', 14, 'bold'),
                fg=self.colors['dark'], bg=self.colors['card']).pack(pady=(0, 10))

        self.media_count_label = tk.Label(media_content, text="0",
                                          font=('Arial', 40, 'bold'),
                                          fg=self.colors['secondary'],
                                          bg=self.colors['card'])
        self.media_count_label.pack(pady=10)

        tk.Label(media_content, text="Photo(s) / Vidéo(s)",
                font=('Arial', 12),
                fg=self.colors['gray'],
                bg=self.colors['card']).pack()

        self.media_time_label = tk.Label(media_content, text="Dernière capture: --",
                                         font=('Arial', 10),
                                         fg=self.colors['gray'],
                                         bg=self.colors['card'])
        self.media_time_label.pack(pady=(15, 0))

        # Carte 3: Événements récents
        events_card_container = tk.Frame(frame, bg=self.colors['bg'])
        events_card_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        events_card = self.creer_carte(events_card_container, "⚡ Événements Récents")

        events_content = tk.Frame(events_card, bg=self.colors['card'], padx=20, pady=10)
        events_content.pack(fill=tk.BOTH, expand=True)

        # Style pour le Treeview moderne
        style = ttk.Style()
        style.configure('Modern.Treeview',
                       background=self.colors['card'],
                       foreground=self.colors['dark'],
                       fieldbackground=self.colors['card'],
                       borderwidth=0,
                       font=('Arial', 10))
        style.configure('Modern.Treeview.Heading',
                       background=self.colors['light'],
                       foreground=self.colors['dark'],
                       borderwidth=0,
                       font=('Arial', 11, 'bold'))
        style.map('Modern.Treeview',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', 'white')])

        # Liste des événements
        columns = ('Type', 'Date', 'Description')
        self.events_tree = ttk.Treeview(events_content, columns=columns,
                                       show='headings', height=12,
                                       style='Modern.Treeview')

        for col in columns:
            self.events_tree.heading(col, text=col)
            if col == 'Type':
                self.events_tree.column(col, width=150)
            elif col == 'Date':
                self.events_tree.column(col, width=180)

        self.events_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar moderne
        scrollbar = ttk.Scrollbar(events_content, orient=tk.VERTICAL,
                                 command=self.events_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_tree.configure(yscrollcommand=scrollbar.set)

    def creer_onglet_historique(self):
        """Crée l'onglet d'historique moderne"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="📜 Historique")

        # Carte pour les contrôles
        controls_container = tk.Frame(frame, bg=self.colors['bg'])
        controls_container.pack(fill=tk.X, padx=15, pady=10)

        controls_card = self.creer_carte(controls_container)
        controls_frame = tk.Frame(controls_card, bg=self.colors['card'], padx=20, pady=15)
        controls_frame.pack(fill=tk.X)

        tk.Label(controls_frame, text="Type de données:",
                font=('Arial', 11, 'bold'),
                fg=self.colors['dark'], bg=self.colors['card']).pack(side=tk.LEFT, padx=10)

        self.hist_type_var = tk.StringVar(value="TOUS")

        # Style moderne pour combobox
        style = ttk.Style()
        style.configure('Modern.TCombobox', fieldbackground=self.colors['light'])

        type_combo = ttk.Combobox(controls_frame, textvariable=self.hist_type_var,
                                 values=["TOUS", "BRUIT", "CAMERA"],
                                 width=15, state='readonly',
                                 font=('Arial', 10),
                                 style='Modern.TCombobox')
        type_combo.pack(side=tk.LEFT, padx=10)

        btn_charger = tk.Button(controls_frame, text="📥 Charger les données",
                               font=('Arial', 10, 'bold'),
                               fg='white',
                               bg=self.colors['success'],
                               activebackground='#059669',
                               activeforeground='white',
                               relief=tk.FLAT,
                               cursor='hand2',
                               command=self.charger_historique,
                               padx=20, pady=8)
        btn_charger.pack(side=tk.LEFT, padx=10)

        btn_charger.bind('<Enter>', lambda e: btn_charger.config(bg='#059669'))
        btn_charger.bind('<Leave>', lambda e: btn_charger.config(bg=self.colors['success']))

        # Carte pour l'historique
        hist_container = tk.Frame(frame, bg=self.colors['bg'])
        hist_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        hist_card = self.creer_carte(hist_container, "📋 Données Historiques")
        hist_content = tk.Frame(hist_card, bg=self.colors['card'], padx=20, pady=10)
        hist_content.pack(fill=tk.BOTH, expand=True)

        # Treeview
        columns = ('ID', 'Date/Heure', 'Capteur', 'Type', 'Mesure', 'Salle')
        self.hist_tree = ttk.Treeview(hist_content, columns=columns,
                                     show='headings', height=20,
                                     style='Modern.Treeview')

        for col in columns:
            self.hist_tree.heading(col, text=col)
            if col == 'ID':
                self.hist_tree.column(col, width=60)
            elif col == 'Mesure':
                self.hist_tree.column(col, width=120)

        self.hist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(hist_content, orient=tk.VERTICAL,
                                 command=self.hist_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hist_tree.configure(yscrollcommand=scrollbar.set)

    def creer_onglet_statistiques(self):
        """Crée l'onglet des statistiques moderne"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="📈 Statistiques")

        # Bouton actualiser en haut
        top_frame = tk.Frame(frame, bg=self.colors['bg'])
        top_frame.pack(fill=tk.X, padx=15, pady=10)

        btn_actualiser = tk.Button(top_frame, text="🔄 Actualiser les statistiques",
                                   font=('Arial', 11, 'bold'),
                                   fg='white',
                                   bg=self.colors['primary'],
                                   activebackground=self.colors['secondary'],
                                   activeforeground='white',
                                   relief=tk.FLAT,
                                   cursor='hand2',
                                   command=self.charger_statistiques,
                                   padx=25, pady=10)
        btn_actualiser.pack()

        btn_actualiser.bind('<Enter>', lambda e: btn_actualiser.config(bg=self.colors['secondary']))
        btn_actualiser.bind('<Leave>', lambda e: btn_actualiser.config(bg=self.colors['primary']))

        # Carte pour les statistiques
        stats_container = tk.Frame(frame, bg=self.colors['bg'])
        stats_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        stats_card = self.creer_carte(stats_container, "📊 Statistiques Générales")
        stats_content = tk.Frame(stats_card, bg=self.colors['card'], padx=30, pady=20)
        stats_content.pack(fill=tk.BOTH, expand=True)

        self.stats_text = tk.Text(stats_content, height=20,
                                 font=('Courier', 11),
                                 bg=self.colors['light'],
                                 fg=self.colors['dark'],
                                 relief=tk.FLAT,
                                 padx=20, pady=20)
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # Charger les stats au démarrage
        self.charger_statistiques()

    def creer_onglet_graphique(self):
        """Crée l'onglet avec graphique du niveau sonore"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="📈 Graphique")

        # Contrôles en haut
        controls_container = tk.Frame(frame, bg=self.colors['bg'])
        controls_container.pack(fill=tk.X, padx=15, pady=10)

        controls_card = self.creer_carte(controls_container)
        controls_frame = tk.Frame(controls_card, bg=self.colors['card'], padx=20, pady=15)
        controls_frame.pack(fill=tk.X)

        tk.Label(controls_frame, text="Période:",
                font=('Arial', 11, 'bold'),
                fg=self.colors['dark'], bg=self.colors['card']).pack(side=tk.LEFT, padx=10)

        self.graph_period_var = tk.StringVar(value="1h")
        period_combo = ttk.Combobox(controls_frame, textvariable=self.graph_period_var,
                                    values=["30min", "1h", "3h", "6h", "12h", "24h"],
                                    width=10, state='readonly',
                                    font=('Arial', 10))
        period_combo.pack(side=tk.LEFT, padx=10)

        btn_refresh_graph = tk.Button(controls_frame, text="🔄 Actualiser",
                                      font=('Arial', 10, 'bold'),
                                      fg='white',
                                      bg=self.colors['primary'],
                                      activebackground=self.colors['secondary'],
                                      activeforeground='white',
                                      relief=tk.FLAT,
                                      cursor='hand2',
                                      command=self.charger_graphique,
                                      padx=20, pady=8)
        btn_refresh_graph.pack(side=tk.LEFT, padx=10)

        btn_refresh_graph.bind('<Enter>', lambda e: btn_refresh_graph.config(bg=self.colors['secondary']))
        btn_refresh_graph.bind('<Leave>', lambda e: btn_refresh_graph.config(bg=self.colors['primary']))

        # Carte pour le graphique
        graph_container = tk.Frame(frame, bg=self.colors['bg'])
        graph_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        graph_card = self.creer_carte(graph_container, "📊 Évolution du Niveau Sonore")
        graph_content = tk.Frame(graph_card, bg=self.colors['card'], padx=20, pady=10)
        graph_content.pack(fill=tk.BOTH, expand=True)

        # Créer la figure matplotlib
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.fig.patch.set_facecolor(self.colors['card'])
        self.ax = self.fig.add_subplot(111)

        self.canvas_graph = FigureCanvasTkAgg(self.fig, graph_content)
        self.canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Charger le graphique initial
        self.charger_graphique()

    def creer_onglet_galerie(self):
        """Crée l'onglet galerie d'images"""
        frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(frame, text="📷 Galerie")

        # Contrôles
        controls_container = tk.Frame(frame, bg=self.colors['bg'])
        controls_container.pack(fill=tk.X, padx=15, pady=10)

        controls_card = self.creer_carte(controls_container)
        controls_frame = tk.Frame(controls_card, bg=self.colors['card'], padx=20, pady=15)
        controls_frame.pack(fill=tk.X)

        tk.Label(controls_frame, text="Dernières photos capturées",
                font=('Arial', 11, 'bold'),
                fg=self.colors['dark'], bg=self.colors['card']).pack(side=tk.LEFT, padx=10)

        btn_refresh_gallery = tk.Button(controls_frame, text="🔄 Actualiser",
                                        font=('Arial', 10, 'bold'),
                                        fg='white',
                                        bg=self.colors['success'],
                                        activebackground='#059669',
                                        activeforeground='white',
                                        relief=tk.FLAT,
                                        cursor='hand2',
                                        command=self.charger_galerie,
                                        padx=20, pady=8)
        btn_refresh_gallery.pack(side=tk.LEFT, padx=10)

        btn_refresh_gallery.bind('<Enter>', lambda e: btn_refresh_gallery.config(bg='#059669'))
        btn_refresh_gallery.bind('<Leave>', lambda e: btn_refresh_gallery.config(bg=self.colors['success']))

        # Carte pour la galerie
        gallery_container = tk.Frame(frame, bg=self.colors['bg'])
        gallery_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        gallery_card = self.creer_carte(gallery_container, "📸 Photos")
        gallery_content = tk.Frame(gallery_card, bg=self.colors['card'], padx=20, pady=10)
        gallery_content.pack(fill=tk.BOTH, expand=True)

        # Frame scrollable simple pour la galerie
        self.gallery_frame = tk.Frame(gallery_content, bg=self.colors['card'])
        self.gallery_frame.pack(fill=tk.BOTH, expand=True)

        # Charger la galerie
        self.charger_galerie()

    def charger_graphique(self):
        """Charge et affiche le graphique du niveau sonore"""
        try:
            # Effacer le graphique précédent
            self.ax.clear()

            # Déterminer la période
            period_str = self.graph_period_var.get()
            hours = {
                "30min": 0.5,
                "1h": 1,
                "3h": 3,
                "6h": 6,
                "12h": 12,
                "24h": 24
            }.get(period_str, 1)

            # Récupérer les données
            date_debut = datetime.now() - timedelta(hours=hours)

            donnees = self.db.execute_query("""
                SELECT d.dateHeure, d.mesure
                FROM Donnees d
                JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
                WHERE c.type = N'BRUIT'
                  AND d.dateHeure >= ?
                ORDER BY d.dateHeure ASC
            """, (date_debut,))

            if donnees:
                dates = [row[0] for row in donnees]
                mesures = [row[1] for row in donnees]

                # Tracer le graphique
                self.ax.plot(dates, mesures, color=self.colors['primary'], linewidth=2, marker='o', markersize=4)

                # Zones de couleur
                self.ax.axhspan(0, 50, facecolor=self.colors['success'], alpha=0.1)
                self.ax.axhspan(50, 70, facecolor=self.colors['warning'], alpha=0.1)
                self.ax.axhspan(70, 100, facecolor=self.colors['danger'], alpha=0.1)

                # Lignes de seuil
                self.ax.axhline(y=50, color=self.colors['success'], linestyle='--', linewidth=1, alpha=0.5)
                self.ax.axhline(y=70, color=self.colors['danger'], linestyle='--', linewidth=1, alpha=0.5)

                self.ax.set_xlabel('Heure', fontsize=10)
                self.ax.set_ylabel('Niveau sonore (dB)', fontsize=10)
                self.ax.set_title(f'Évolution du niveau sonore - Dernières {period_str}', fontsize=12, fontweight='bold')
                self.ax.grid(True, alpha=0.3)
                self.ax.set_facecolor(self.colors['light'])

                # Format des dates
                self.fig.autofmt_xdate()
            else:
                self.ax.text(0.5, 0.5, 'Aucune donnée disponible',
                           ha='center', va='center', fontsize=14, color=self.colors['gray'])

            self.canvas_graph.draw()

        except Exception as e:
            print(f"Erreur chargement graphique: {e}")
            self.ax.text(0.5, 0.5, f'Erreur: {str(e)}',
                       ha='center', va='center', fontsize=12, color=self.colors['danger'])
            self.canvas_graph.draw()

    def charger_galerie(self):
        """Charge les dernières photos dans la galerie"""
        try:
            # Vider la galerie
            for widget in self.gallery_frame.winfo_children():
                widget.destroy()

            # Récupérer les 12 dernières photos
            photos = self.db.execute_query("""
                SELECT TOP 12 d.idDonnee_PK, d.photoBlob, d.dateHeure
                FROM Donnees d
                JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
                WHERE c.type = N'CAMERA' AND d.photoBlob IS NOT NULL
                ORDER BY d.dateHeure DESC
            """)

            if photos:
                row_frame = None
                for idx, (photo_id, photo_blob, date) in enumerate(photos):
                    # Créer une nouvelle ligne tous les 3 éléments
                    if idx % 3 == 0:
                        row_frame = tk.Frame(self.gallery_frame, bg=self.colors['card'])
                        row_frame.pack(fill=tk.X, pady=5)

                    # Container pour la photo
                    photo_container = tk.Frame(row_frame, bg=self.colors['border'],
                                              relief=tk.RAISED, borderwidth=2)
                    photo_container.pack(side=tk.LEFT, padx=10, pady=5)

                    try:
                        # Charger l'image
                        image = Image.open(BytesIO(photo_blob))
                        # Redimensionner
                        image.thumbnail((300, 200), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)

                        # Label pour l'image
                        img_label = tk.Label(photo_container, image=photo, bg=self.colors['card'])
                        img_label.image = photo  # Garder une référence
                        img_label.pack()

                        # Info sous l'image
                        info_frame = tk.Frame(photo_container, bg=self.colors['card'])
                        info_frame.pack(fill=tk.X, padx=5, pady=5)

                        tk.Label(info_frame,
                                text=f"📅 {date.strftime('%Y-%m-%d %H:%M:%S')}",
                                font=('Arial', 9),
                                fg=self.colors['dark'],
                                bg=self.colors['card']).pack()

                    except Exception as e:
                        tk.Label(photo_container,
                                text=f"❌ Erreur\n{str(e)[:20]}",
                                font=('Arial', 10),
                                fg=self.colors['danger'],
                                bg=self.colors['card'],
                                padx=20, pady=20).pack()
            else:
                tk.Label(self.gallery_frame,
                        text="Aucune photo disponible",
                        font=('Arial', 14),
                        fg=self.colors['gray'],
                        bg=self.colors['card']).pack(pady=50)

        except Exception as e:
            print(f"Erreur chargement galerie: {e}")
            tk.Label(self.gallery_frame,
                    text=f"Erreur: {str(e)}",
                    font=('Arial', 12),
                    fg=self.colors['danger'],
                    bg=self.colors['card']).pack(pady=50)

    def rafraichir_donnees(self):
        """Rafraîchit les données affichées"""
        if not self.en_cours:
            return

        if self.auto_refresh.get():
            try:
                # Dernière mesure de son
                son = self.db.execute_query("""
                    SELECT TOP 1 d.mesure, d.dateHeure
                    FROM Donnees d
                    JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
                    WHERE c.type = N'BRUIT'
                    ORDER BY d.dateHeure DESC
                """)

                if son:
                    niveau = son[0][0]
                    date = son[0][1]

                    self.son_value_label.config(text=f"{niveau:.1f} dB")
                    self.son_time_label.config(text=f"Dernière mesure: {date.strftime('%H:%M:%S')}")

                    # Animer la barre de progression
                    progress_width = min(100, niveau)
                    total_width = self.son_progress_frame.winfo_width()
                    bar_width = int((progress_width / 100) * total_width)

                    self.son_progress_bar.config(width=bar_width)

                    # Couleur selon le niveau
                    if niveau > 70:
                        self.son_value_label.config(fg=self.colors['danger'])
                        self.son_progress_bar.config(bg=self.colors['danger'])
                    elif niveau > 50:
                        self.son_value_label.config(fg=self.colors['warning'])
                        self.son_progress_bar.config(bg=self.colors['warning'])
                    else:
                        self.son_value_label.config(fg=self.colors['success'])
                        self.son_progress_bar.config(bg=self.colors['success'])

                # Compter les médias
                media_count = self.db.execute_query("""
                    SELECT COUNT(*)
                    FROM Donnees d
                    JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
                    WHERE c.type = N'CAMERA' AND d.photoBlob IS NOT NULL
                """)

                if media_count:
                    self.media_count_label.config(text=str(media_count[0][0]))

                # Dernière capture
                last_media = self.db.execute_query("""
                    SELECT TOP 1 d.dateHeure
                    FROM Donnees d
                    JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
                    WHERE c.type = N'CAMERA' AND d.photoBlob IS NOT NULL
                    ORDER BY d.dateHeure DESC
                """)

                if last_media:
                    self.media_time_label.config(
                        text=f"Dernière capture: {last_media[0][0].strftime('%H:%M:%S')}")

                # Derniers événements
                self.charger_evenements_recents()

                # Mettre à jour le label de dernière mise à jour
                self.last_update_label.config(
                    text=f"⏰ Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")

                self.status_indicator.config(text="● Connexion active", fg=self.colors['success'])

            except Exception as e:
                print(f"Erreur rafraîchissement: {e}")
                self.status_indicator.config(text="● Erreur connexion", fg=self.colors['danger'])

        # Programmer le prochain rafraîchissement
        if self.en_cours:
            self.root.after(self.refresh_interval, self.rafraichir_donnees)

    def charger_evenements_recents(self):
        """Charge les événements récents"""
        try:
            # Vider la liste
            for item in self.events_tree.get_children():
                self.events_tree.delete(item)

            # Charger les derniers événements
            events = self.db.execute_query("""
                SELECT TOP 20
                    e.type,
                    d.dateHeure,
                    e.description
                FROM Evenement e
                JOIN Donnees d ON e.idDonnee = d.idDonnee_PK
                ORDER BY d.dateHeure DESC
            """)

            for event in events:
                type_event = event[0]
                date = event[1].strftime('%Y-%m-%d %H:%M:%S') if event[1] else ''
                desc = event[2] if event[2] else ''

                # Tronquer la description si trop longue
                if len(desc) > 100:
                    desc = desc[:97] + "..."

                self.events_tree.insert('', tk.END, values=(type_event, date, desc))

        except Exception as e:
            print(f"Erreur chargement événements: {e}")

    def rafraichir_maintenant(self):
        """Force un rafraîchissement immédiat"""
        self.rafraichir_donnees()

    def charger_historique(self):
        """Charge l'historique selon le type sélectionné"""
        try:
            # Vider la liste
            for item in self.hist_tree.get_children():
                self.hist_tree.delete(item)

            type_filtre = self.hist_type_var.get()

            # Construire la requête
            if type_filtre == "TOUS":
                where_clause = ""
            else:
                where_clause = f"WHERE c.type = N'{type_filtre}'"

            query = f"""
                SELECT TOP 100
                    d.idDonnee_PK,
                    d.dateHeure,
                    c.nom,
                    c.type,
                    CASE
                        WHEN c.type = N'BRUIT' THEN CAST(d.mesure AS NVARCHAR) + ' dB'
                        WHEN c.type = N'CAMERA' THEN
                            CAST(DATALENGTH(d.photoBlob)/1024.0 AS NVARCHAR) + ' KB'
                        ELSE 'N/A'
                    END AS mesure,
                    s.numero
                FROM Donnees d
                JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
                JOIN Salle s ON d.noSalle = s.idSalle_PK
                {where_clause}
                ORDER BY d.dateHeure DESC
            """

            donnees = self.db.execute_query(query)

            for data in donnees:
                id_donnee = data[0]
                date = data[1].strftime('%Y-%m-%d %H:%M:%S') if data[1] else ''
                capteur = data[2]
                type_cap = data[3]
                mesure = data[4]
                salle = data[5]

                self.hist_tree.insert('', tk.END,
                                    values=(id_donnee, date, capteur, type_cap, mesure, salle))

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur chargement historique:\n{str(e)}")

    def charger_statistiques(self):
        """Charge et affiche les statistiques"""
        try:
            self.stats_text.delete('1.0', tk.END)

            # Stats générales
            stats = []
            stats.append("=" * 60)
            stats.append("STATISTIQUES GÉNÉRALES - SalleSense")
            stats.append("=" * 60)
            stats.append("")

            # Nombre total de données
            count = self.db.execute_query("SELECT COUNT(*) FROM Donnees")
            stats.append(f"📊 Nombre total de mesures: {count[0][0]:,}")
            stats.append("")

            # Par type de capteur
            by_type = self.db.execute_query("""
                SELECT c.type, COUNT(*) AS nb
                FROM Donnees d
                JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
                GROUP BY c.type
            """)

            stats.append("📌 Répartition par type de capteur:")
            stats.append("-" * 40)
            for row in by_type:
                stats.append(f"  • {row[0]:15} : {row[1]:,} mesures")
            stats.append("")

            # Événements
            events_count = self.db.execute_query("""
                SELECT type, COUNT(*) AS nb
                FROM Evenement
                GROUP BY type
                ORDER BY nb DESC
            """)

            stats.append("⚡ Événements détectés:")
            stats.append("-" * 40)
            for row in events_count:
                stats.append(f"  • {row[0]:15} : {row[1]:,} événements")
            stats.append("")

            # Niveau sonore moyen/max
            son_stats = self.db.execute_query("""
                SELECT
                    AVG(d.mesure) AS moyenne,
                    MAX(d.mesure) AS maximum,
                    MIN(d.mesure) AS minimum
                FROM Donnees d
                JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
                WHERE c.type = N'BRUIT'
            """)

            if son_stats and son_stats[0][0]:
                stats.append("🎤 Analyse niveau sonore:")
                stats.append("-" * 40)
                stats.append(f"  • Moyenne    : {son_stats[0][0]:6.1f} dB")
                stats.append(f"  • Maximum    : {son_stats[0][1]:6.1f} dB")
                stats.append(f"  • Minimum    : {son_stats[0][2]:6.1f} dB")
                stats.append("")

            stats.append("=" * 60)
            stats.append(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            stats.append("=" * 60)

            # Afficher
            self.stats_text.insert('1.0', '\n'.join(stats))

        except Exception as e:
            self.stats_text.insert('1.0', f"❌ Erreur chargement statistiques:\n{str(e)}")

    def deconnecter(self):
        """Se déconnecte et retourne à l'écran de connexion"""
        if messagebox.askyesno("Déconnexion", "Voulez-vous vraiment vous déconnecter ?"):
            self.fermer(ouvrir_connexion=True)

    def fermer(self, ouvrir_connexion=False):
        """Ferme l'application"""
        self.en_cours = False
        self.root.destroy()

        if ouvrir_connexion:
            from interface_connexion import InterfaceConnexionModerne
            app = InterfaceConnexionModerne()
            app.run()

    def run(self):
        """Lance l'application"""
        self.root.mainloop()


if __name__ == "__main__":
    # Pour tester directement
    from db_connection import DatabaseConnection
    from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)
    if db.connect():
        app = InterfacePrincipaleModerne(db, {'pseudo': 'Test'})
        app.run()
