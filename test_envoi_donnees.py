"""
Script de test pour envoyer des données de capteurs vers la BD
"""

from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD, ID_SALLE
from datetime import datetime
import time


def test_envoi_bruit():
    """Test d'envoi d'une mesure de bruit"""

    print("=== Test d'envoi de données - Micro Électret ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        return False

    try:
        # Récupérer l'ID du capteur de bruit
        capteur = db.execute_query(
            "SELECT idCapteur_PK FROM Capteur WHERE type = 'BRUIT'"
        )

        if not capteur:
            print("✗ Aucun capteur de type BRUIT trouvé. Lancez d'abord initialiser_bd.py")
            return False

        id_capteur_bruit = capteur[0][0]
        print(f"✓ Capteur BRUIT trouvé - ID: {id_capteur_bruit}")

        # Simuler des mesures de bruit
        print("\n--- Envoi de 3 mesures de bruit ---")

        mesures = [45.2, 68.5, 75.3]  # dB

        for i, niveau in enumerate(mesures, 1):
            print(f"\nMesure #{i}: {niveau} dB")

            # Insérer la donnée
            db.execute_non_query(
                """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
                   VALUES (?, ?, ?, NULL, ?)""",
                (datetime.now(), id_capteur_bruit, niveau, ID_SALLE)
            )

            # Récupérer l'ID de la donnée insérée
            id_donnee = db.execute_query("SELECT @@IDENTITY AS id")[0][0]
            print(f"  ✓ Donnée enregistrée - ID: {id_donnee}")

            # Créer un événement si bruit fort
            if niveau > 70:
                db.execute_non_query(
                    """INSERT INTO Evenement (type, idDonnee, description)
                       VALUES (?, ?, ?)""",
                    ('BRUIT_FORT', id_donnee, f'Niveau sonore élevé: {niveau} dB')
                )
                print(f"  ⚡ Événement BRUIT_FORT créé")

            time.sleep(0.5)  # Pause entre les mesures

        print("\n✓ Test terminé avec succès!")
        return True

    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        return False

    finally:
        db.disconnect()


def test_envoi_photo():
    """Test d'envoi d'une photo (simulé - données binaires)"""

    print("\n=== Test d'envoi de données - Pi Camera ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        return False

    try:
        # Récupérer l'ID du capteur caméra
        capteur = db.execute_query(
            "SELECT idCapteur_PK FROM Capteur WHERE type = 'CAMERA'"
        )

        if not capteur:
            print("✗ Aucun capteur de type CAMERA trouvé. Lancez d'abord initialiser_bd.py")
            return False

        id_capteur_camera = capteur[0][0]
        print(f"✓ Capteur CAMERA trouvé - ID: {id_capteur_camera}")

        # Simuler une capture photo (données binaires)
        print("\n--- Envoi d'une photo ---")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Créer des données binaires simulées (en production, ce serait les bytes de l'image JPEG)
        photo_bytes = b"PHOTO_SIMULEE_" + timestamp.encode()

        print(f"Photo simulée: {len(photo_bytes)} bytes")

        # Insérer la donnée
        db.execute_non_query(
            """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photoBlob, noSalle)
               VALUES (?, ?, NULL, ?, ?)""",
            (datetime.now(), id_capteur_camera, photo_bytes, ID_SALLE)
        )

        # Récupérer l'ID de la donnée insérée
        id_donnee = db.execute_query("SELECT @@IDENTITY AS id")[0][0]
        print(f"✓ Donnée enregistrée - ID: {id_donnee}")

        # Créer un événement
        db.execute_non_query(
            """INSERT INTO Evenement (type, idDonnee, description)
               VALUES (?, ?, ?)""",
            ('CAPTURE', id_donnee, f'Photo capturée à {timestamp}')
        )
        print(f"⚡ Événement CAPTURE créé")

        print("\n✓ Test terminé avec succès!")
        return True

    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        return False

    finally:
        db.disconnect()


def afficher_donnees_recentes():
    """Affiche les dernières données enregistrées"""

    print("\n=== Données récentes dans la BD ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        return

    try:
        # Dernières mesures
        print("--- Dernières mesures (toutes) ---")
        donnees = db.execute_query("""
            SELECT TOP 10
                d.dateHeure,
                c.nom AS capteur,
                c.type,
                d.mesure,
                DATALENGTH(d.photoBlob) AS taille_photo,
                s.numero AS salle
            FROM Donnees d
            JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
            JOIN Salle s ON d.noSalle = s.idSalle_PK
            ORDER BY d.dateHeure DESC
        """)

        for donnee in donnees:
            date = donnee[0]
            capteur = donnee[1]
            type_cap = donnee[2]
            mesure = donnee[3]
            taille_photo = donnee[4]
            salle = donnee[5]

            if type_cap == 'BRUIT':
                print(f"  [{date}] {capteur} - Salle {salle}: {mesure} dB")
            elif type_cap == 'CAMERA':
                taille_kb = taille_photo / 1024 if taille_photo else 0
                print(f"  [{date}] {capteur} - Salle {salle}: Photo {taille_kb:.1f} KB")

        # Derniers événements
        print("\n--- Derniers événements ---")
        events = db.execute_query("""
            SELECT TOP 10
                e.type,
                e.description,
                d.dateHeure,
                s.numero AS salle
            FROM Evenement e
            JOIN Donnees d ON e.idDonnee = d.idDonnee_PK
            JOIN Salle s ON d.noSalle = s.idSalle_PK
            ORDER BY d.dateHeure DESC
        """)

        for event in events:
            type_ev = event[0]
            desc = event[1]
            date = event[2]
            salle = event[3]
            print(f"  [{date}] {type_ev} - Salle {salle}: {desc}")

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        db.disconnect()


if __name__ == "__main__":
    # Test complet
    print("╔═══════════════════════════════════════════════════╗")
    print("║  Test d'envoi de données - Capteurs SalleSense   ║")
    print("╚═══════════════════════════════════════════════════╝\n")

    # 1. Test micro électret
    if test_envoi_bruit():
        time.sleep(1)

        # 2. Test caméra
        if test_envoi_photo():
            time.sleep(1)

            # 3. Afficher les résultats
            afficher_donnees_recentes()
