"""
Script pour initialiser la base de données avec les capteurs et salles
"""

from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD


def initialiser_bd():
    """Initialise la base de données avec les capteurs et salles de base"""

    print("=== Initialisation de la base de données ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("Impossible de se connecter à la base de données")
        return False

    try:
        # 1. Créer une salle si elle n'existe pas
        print("--- Création de la salle ---")
        salles_existantes = db.execute_query("SELECT idSalle_PK FROM Salle WHERE numero = 'A-101'")

        if not salles_existantes:
            db.execute_non_query(
                "INSERT INTO Salle (numero, capaciteMaximale) VALUES (?, ?)",
                ('A-101', 20)
            )
            print("✓ Salle A-101 créée")
        else:
            print("✓ Salle A-101 existe déjà")

        # 2. Créer le capteur de bruit (micro électret)
        print("\n--- Création du capteur de bruit ---")
        mic_existant = db.execute_query("SELECT idCapteur_PK FROM Capteur WHERE nom = 'MIC-ELECTRET-1'")

        if not mic_existant:
            db.execute_non_query(
                "INSERT INTO Capteur (nom, type) VALUES (?, ?)",
                ('MIC-ELECTRET-1', 'BRUIT')
            )
            print("✓ Capteur MIC-ELECTRET-1 créé")
        else:
            print("✓ Capteur MIC-ELECTRET-1 existe déjà")

        # 3. Créer le capteur caméra
        print("\n--- Création du capteur caméra ---")
        cam_existante = db.execute_query("SELECT idCapteur_PK FROM Capteur WHERE nom = 'PICAM-V2-1'")

        if not cam_existante:
            db.execute_non_query(
                "INSERT INTO Capteur (nom, type) VALUES (?, ?)",
                ('PICAM-V2-1', 'CAMERA')
            )
            print("✓ Capteur PICAM-V2-1 créé")
        else:
            print("✓ Capteur PICAM-V2-1 existe déjà")

        # 4. Afficher un résumé
        print("\n=== Résumé de la configuration ===")

        print("\n--- Salles ---")
        salles = db.execute_query("SELECT idSalle_PK, numero, capaciteMaximale FROM Salle")
        for salle in salles:
            print(f"  ID: {salle[0]}, Numéro: {salle[1]}, Capacité: {salle[2]}")

        print("\n--- Capteurs ---")
        capteurs = db.execute_query("SELECT idCapteur_PK, nom, type FROM Capteur")
        for capteur in capteurs:
            print(f"  ID: {capteur[0]}, Nom: {capteur[1]}, Type: {capteur[2]}")

        print("\n✓ Initialisation terminée avec succès!")
        return True

    except Exception as e:
        print(f"\n✗ Erreur lors de l'initialisation: {e}")
        return False

    finally:
        db.disconnect()


if __name__ == "__main__":
    initialiser_bd()
