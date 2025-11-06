"""
Exemple d'utilisation de la fonction get_user_by_id
"""

from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD


def main():
    """Exemple de récupération d'un utilisateur par ID"""

    print("=== Exemple : Récupération d'utilisateur par ID ===\n")

    # Créer la connexion
    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    # Se connecter à la base de données
    if not db.connect():
        print("Impossible de se connecter à la base de données")
        return

    try:
        # Exemple 1: Récupérer l'utilisateur avec ID 1
        print("--- Récupération de l'utilisateur ID 1 ---")
        user = db.get_user_by_id(1)

        if user:
            print(f"\nInformations de l'utilisateur:")
            print(f"  ID:      {user['id']}")
            print(f"  Pseudo:  {user['pseudo']}")
            print(f"  Email:   {user['courriel']}")
            # Note: on n'affiche pas le mot de passe pour des raisons de sécurité

        # Exemple 2: Récupérer un utilisateur inexistant
        print("\n--- Tentative de récupération d'un utilisateur inexistant ---")
        user = db.get_user_by_id(999)

        # Exemple 3: Récupérer plusieurs utilisateurs par leurs IDs
        print("\n--- Récupération de plusieurs utilisateurs ---")
        ids = [1, 2, 3]
        for user_id in ids:
            user = db.get_user_by_id(user_id)
            if user:
                print(f"  [{user['id']}] {user['pseudo']} - {user['courriel']}")

    finally:
        # Toujours fermer la connexion
        db.disconnect()


# Version avec context manager (recommandé)
def main_with_context():
    """Version avec context manager - fermeture automatique"""

    print("\n=== Version avec context manager ===\n")

    with DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD) as db:
        # Récupérer un utilisateur
        user = db.get_user_by_id(1)

        if user:
            print(f"Utilisateur: {user['pseudo']} ({user['courriel']})")


if __name__ == "__main__":
    # Lancer l'exemple
    main()

    # Version alternative avec context manager
    main_with_context()
