"""
Script pour visualiser les photos stockées dans la base de données
"""

from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD
from datetime import datetime
import os


def lister_photos():
    """Liste toutes les photos dans la base de données"""

    print("\n=== Photos stockées dans la base de données ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("✗ Impossible de se connecter à la base de données")
        return

    try:
        # Récupérer toutes les photos
        photos = db.execute_query("""
            SELECT
                d.idDonnee_PK,
                d.dateHeure,
                c.nom AS capteur,
                s.numero AS salle,
                DATALENGTH(d.photoBlob) AS taille_bytes
            FROM Donnees d
            JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
            JOIN Salle s ON d.noSalle = s.idSalle_PK
            WHERE d.photoBlob IS NOT NULL
            ORDER BY d.dateHeure DESC
        """)

        if not photos:
            print("Aucune photo trouvée dans la base de données")
            return

        print(f"Total: {len(photos)} photo(s)\n")
        print("─" * 80)

        for photo in photos:
            id_donnee = photo[0]
            date_heure = photo[1]
            capteur = photo[2]
            salle = photo[3]
            taille_bytes = photo[4]
            taille_kb = taille_bytes / 1024 if taille_bytes else 0

            print(f"ID: {id_donnee:4d} | {date_heure} | {capteur:15s} | Salle {salle:6s} | {taille_kb:7.1f} KB")

        print("─" * 80)

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        db.disconnect()


def extraire_photo(id_donnee: int, nom_fichier: str = None):
    """
    Extrait une photo de la BD et la sauvegarde en fichier

    Args:
        id_donnee: ID de la donnée contenant la photo
        nom_fichier: Nom du fichier de sortie (optionnel)
    """

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("✗ Impossible de se connecter à la base de données")
        return

    try:
        # Récupérer la photo
        result = db.execute_query(
            """SELECT photoBlob, dateHeure
               FROM Donnees
               WHERE idDonnee_PK = ?""",
            (id_donnee,)
        )

        if not result or not result[0][0]:
            print(f"✗ Aucune photo trouvée avec l'ID {id_donnee}")
            return

        photo_bytes = result[0][0]
        date_heure = result[0][1]

        # Générer le nom de fichier si non fourni
        if not nom_fichier:
            timestamp = date_heure.strftime("%Y%m%d_%H%M%S")
            nom_fichier = f"photo_{id_donnee}_{timestamp}.jpg"

        # Créer le dossier photos_extraites s'il n'existe pas
        os.makedirs("photos_extraites", exist_ok=True)
        chemin_complet = os.path.join("photos_extraites", nom_fichier)

        # Sauvegarder la photo
        with open(chemin_complet, 'wb') as f:
            f.write(photo_bytes)

        taille_kb = len(photo_bytes) / 1024
        print(f"✓ Photo extraite: {chemin_complet} ({taille_kb:.1f} KB)")

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        db.disconnect()


def extraire_toutes_photos():
    """Extrait toutes les photos de la BD"""

    print("\n=== Extraction de toutes les photos ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("✗ Impossible de se connecter à la base de données")
        return

    try:
        # Récupérer toutes les photos
        photos = db.execute_query("""
            SELECT
                d.idDonnee_PK,
                d.photoBlob,
                d.dateHeure
            FROM Donnees d
            WHERE d.photoBlob IS NOT NULL
            ORDER BY d.dateHeure DESC
        """)

        if not photos:
            print("Aucune photo trouvée")
            return

        # Créer le dossier
        os.makedirs("photos_extraites", exist_ok=True)

        print(f"Extraction de {len(photos)} photo(s)...\n")

        for photo in photos:
            id_donnee = photo[0]
            photo_bytes = photo[1]
            date_heure = photo[2]

            timestamp = date_heure.strftime("%Y%m%d_%H%M%S")
            nom_fichier = f"photo_{id_donnee}_{timestamp}.jpg"
            chemin_complet = os.path.join("photos_extraites", nom_fichier)

            with open(chemin_complet, 'wb') as f:
                f.write(photo_bytes)

            taille_kb = len(photo_bytes) / 1024
            print(f"  ✓ {nom_fichier} ({taille_kb:.1f} KB)")

        print(f"\n✓ {len(photos)} photo(s) extraite(s) dans le dossier 'photos_extraites/'")

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        db.disconnect()


def menu():
    """Menu interactif"""
    while True:
        print("\n╔═══════════════════════════════════════════════════════════╗")
        print("║          Visualiseur de Photos - SalleSense              ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print("\n1. Lister toutes les photos")
        print("2. Extraire une photo (par ID)")
        print("3. Extraire toutes les photos")
        print("4. Quitter")
        print()

        choix = input("Votre choix: ").strip()

        if choix == "1":
            lister_photos()

        elif choix == "2":
            try:
                id_donnee = int(input("\nID de la photo à extraire: "))
                extraire_photo(id_donnee)
            except ValueError:
                print("✗ ID invalide")

        elif choix == "3":
            extraire_toutes_photos()

        elif choix == "4":
            print("\nAu revoir!\n")
            break

        else:
            print("\n✗ Choix invalide")


if __name__ == "__main__":
    menu()
