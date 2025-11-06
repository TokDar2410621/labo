"""
Module de connexion à la base de données SalleSense
Nécessite: pip install pyodbc
"""

import pyodbc
from typing import Optional, Tuple


class DatabaseConnection:
    """Gère la connexion à la base de données Prog3A25_bdSalleSense"""

    def __init__(self, server: str, database: str = "Prog3A25_bdSalleSense",
                 username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialise la connexion à la base de données

        Args:
            server: Adresse du serveur SQL Server (ex: 'localhost' ou 'localhost\\SQLEXPRESS')
            database: Nom de la base de données (défaut: Prog3A25_bdSalleSense)
            username: Nom d'utilisateur SQL (None pour Windows Authentication)
            password: Mot de passe SQL (None pour Windows Authentication)
        """
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """
        Établit la connexion à la base de données

        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            if self.username and self.password:
                # Authentification SQL Server
                connection_string = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                    f"TrustServerCertificate=yes;"
                )
            else:
                # Authentification Windows
                connection_string = (
                    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes;"
                )

            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()
            print(f"✓ Connexion établie à la base de données '{self.database}'")
            return True

        except pyodbc.Error as e:
            print(f"✗ Erreur de connexion: {e}")
            return False

    def disconnect(self):
        """Ferme la connexion à la base de données"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✓ Connexion fermée")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """
        Exécute une requête SELECT

        Args:
            query: Requête SQL à exécuter
            params: Paramètres de la requête (optionnel)

        Returns:
            Liste des résultats
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            results = self.cursor.fetchall()
            return results

        except pyodbc.Error as e:
            print(f"✗ Erreur lors de l'exécution de la requête: {e}")
            return []

    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Exécute une requête INSERT, UPDATE ou DELETE

        Args:
            query: Requête SQL à exécuter
            params: Paramètres de la requête (optionnel)

        Returns:
            True si succès, False sinon
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            self.connection.commit()
            print(f"✓ Requête exécutée avec succès ({self.cursor.rowcount} ligne(s) affectée(s))")
            return True

        except pyodbc.Error as e:
            print(f"✗ Erreur lors de l'exécution de la requête: {e}")
            self.connection.rollback()
            return False

    def create_user(self, pseudo: str, courriel: str, mot_de_passe: str) -> int:
        """
        Crée un nouvel utilisateur via la procédure stockée

        Args:
            pseudo: Pseudonyme de l'utilisateur
            courriel: Email de l'utilisateur
            mot_de_passe: Mot de passe en clair (sera hashé par la procédure)

        Returns:
            ID de l'utilisateur créé, ou -1 si erreur
        """
        try:
            # Paramètre OUTPUT
            user_id = self.cursor.execute(
                "DECLARE @id INT; "
                "EXEC dbo.usp_Utilisateur_Create @Pseudo=?, @Courriel=?, @MotDePasse=?, @UserId=@id OUTPUT; "
                "SELECT @id;",
                pseudo, courriel, mot_de_passe
            ).fetchval()

            self.connection.commit()

            if user_id == -1:
                print(f"✗ Erreur: l'email '{courriel}' existe déjà")
            else:
                print(f"✓ Utilisateur créé avec l'ID: {user_id}")

            return user_id

        except pyodbc.Error as e:
            print(f"✗ Erreur lors de la création de l'utilisateur: {e}")
            self.connection.rollback()
            return -1

    def login_user(self, courriel: str, mot_de_passe: str) -> int:
        """
        Authentifie un utilisateur via la procédure stockée

        Args:
            courriel: Email de l'utilisateur
            mot_de_passe: Mot de passe en clair

        Returns:
            ID de l'utilisateur si succès, -1 si échec
        """
        try:
            user_id = self.cursor.execute(
                "DECLARE @id INT; "
                "EXEC dbo.usp_Utilisateur_Login @Courriel=?, @MotDePasse=?, @UserId=@id OUTPUT; "
                "SELECT @id;",
                courriel, mot_de_passe
            ).fetchval()

            if user_id == -1:
                print("✗ Échec de l'authentification (email ou mot de passe incorrect)")
            else:
                print(f"✓ Authentification réussie - ID utilisateur: {user_id}")

            return user_id

        except pyodbc.Error as e:
            print(f"✗ Erreur lors de l'authentification: {e}")
            return -1

    def get_user_by_id(self, id_utilisateur: int) -> Optional[dict]:
        """
        Récupère un utilisateur par son ID

        Args:
            id_utilisateur: ID de l'utilisateur à récupérer

        Returns:
            Dictionnaire contenant les informations de l'utilisateur, ou None si non trouvé
        """
        try:
            result = self.cursor.execute(
                """SELECT idUtilisateur_PK, pseudo, courriel
                   FROM Utilisateur
                   WHERE idUtilisateur_PK = ?""",
                id_utilisateur
            ).fetchone()

            if result is None:
                print(f"✗ Aucun utilisateur trouvé avec l'ID: {id_utilisateur}")
                return None

            # Créer un dictionnaire avec les informations de l'utilisateur
            user = {
                'id': result[0],
                'pseudo': result[1],
                'courriel': result[2]
            }

            print(f"✓ Utilisateur trouvé: {user['pseudo']} ({user['courriel']})")
            return user

        except pyodbc.Error as e:
            print(f"✗ Erreur lors de la récupération de l'utilisateur: {e}")
            return None

    def __enter__(self):
        """Support du context manager (with statement)"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme automatiquement la connexion à la sortie du context manager"""
        self.disconnect()


# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration de connexion (à adapter selon votre environnement)
    SERVER = "DICJWIN01.cegepjonquiere.ca"
    DATABASE = "Prog3A25_bdSalleSense"
    USERNAME = "prog3e09"
    PASSWORD = "colonne42"

    # Option 1: Avec context manager (recommandé)
    print("=== Test de connexion avec context manager ===")
    with DatabaseConnection(SERVER, DATABASE, USERNAME, PASSWORD) as db:
        # Test: Lister tous les utilisateurs
        print("\n--- Liste des utilisateurs ---")
        users = db.execute_query("SELECT idUtilisateur_PK, pseudo, courriel FROM Utilisateur")
        for user in users:
            print(f"ID: {user[0]}, Pseudo: {user[1]}, Email: {user[2]}")

        # Test: Lister toutes les salles
        print("\n--- Liste des salles ---")
        salles = db.execute_query("SELECT idSalle_PK, numero, capaciteMaximale FROM Salle")
        for salle in salles:
            print(f"ID: {salle[0]}, Numéro: {salle[1]}, Capacité: {salle[2]}")

    print("\n=== Test des fonctions d'authentification ===")
    # Option 2: Connexion manuelle
    db = DatabaseConnection(SERVER, DATABASE, USERNAME, PASSWORD)

    if db.connect():
        # Test: Créer un nouvel utilisateur
        print("\n--- Création d'utilisateur ---")
        new_user_id = db.create_user("testuser", "test@example.com", "motdepasse123")

        # Test: Authentification
        print("\n--- Test de login ---")
        user_id = db.login_user("alice@example.com", "pwdAlice")

        # Test: Login échoué
        print("\n--- Test de login échoué ---")
        user_id = db.login_user("alice@example.com", "mauvais_mdp")

        # Test: Récupérer un utilisateur par ID
        print("\n--- Récupération d'utilisateur par ID ---")
        user = db.get_user_by_id(1)
        if user:
            print(f"  ID: {user['id']}")
            print(f"  Pseudo: {user['pseudo']}")
            print(f"  Email: {user['courriel']}")

        # Test: Utilisateur inexistant
        print("\n--- Test utilisateur inexistant ---")
        user = db.get_user_by_id(999)

        db.disconnect()
