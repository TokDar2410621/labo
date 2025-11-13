"""
Script pour visualiser et extraire les vidéos stockées dans la base de données
"""

from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD
import os


def lister_videos():
    """Liste toutes les vidéos dans la base de données"""

    print("\n=== Vidéos stockées dans la base de données ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("✗ Impossible de se connecter à la base de données")
        return

    try:
        # Récupérer toutes les vidéos (données du capteur CAMERA avec taille > 100 bytes)
        videos = db.execute_query("""
            SELECT
                d.idDonnee_PK,
                d.dateHeure,
                c.nom AS capteur,
                s.numero AS salle,
                DATALENGTH(d.photoBlob) AS taille_bytes,
                e.description
            FROM Donnees d
            JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
            JOIN Salle s ON d.noSalle = s.idSalle_PK
            LEFT JOIN Evenement e ON e.idDonnee = d.idDonnee_PK
            WHERE d.photoBlob IS NOT NULL
              AND c.type = N'CAMERA'
              AND DATALENGTH(d.photoBlob) > 100
            ORDER BY d.dateHeure DESC
        """)

        if not videos:
            print("Aucune vidéo trouvée dans la base de données")
            print("(Seules les vidéos > 100 bytes sont affichées)")
            return

        print(f"Total: {len(videos)} vidéo(s)\n")
        print("─" * 90)
        print(f"{'ID':>5} | {'Date/Heure':<19} | {'Capteur':<15} | {'Salle':<8} | {'Taille':>10} | Description")
        print("─" * 90)

        for video in videos:
            id_donnee = video[0]
            date_heure = video[1]
            capteur = video[2]
            salle = video[3]
            taille_bytes = video[4]
            description = video[5] if video[5] else "N/A"

            taille_kb = taille_bytes / 1024 if taille_bytes else 0
            taille_mb = taille_kb / 1024

            if taille_mb > 1:
                taille_str = f"{taille_mb:.2f} MB"
            else:
                taille_str = f"{taille_kb:.1f} KB"

            # Tronquer la description
            desc_short = description[:40] + "..." if len(description) > 40 else description

            print(f"{id_donnee:5d} | {date_heure} | {capteur:<15} | {salle:<8} | {taille_str:>10} | {desc_short}")

        print("─" * 90)

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        db.disconnect()


def extraire_video(id_donnee: int, nom_fichier: str = None):
    """
    Extrait une vidéo de la BD et la sauvegarde en fichier

    Args:
        id_donnee: ID de la donnée contenant la vidéo
        nom_fichier: Nom du fichier de sortie (optionnel)
    """

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("✗ Impossible de se connecter à la base de données")
        return

    try:
        # Récupérer la vidéo
        result = db.execute_query(
            """SELECT photoBlob, dateHeure
               FROM Donnees
               WHERE idDonnee_PK = ?""",
            (id_donnee,)
        )

        if not result or not result[0][0]:
            print(f"✗ Aucune vidéo trouvée avec l'ID {id_donnee}")
            return

        video_bytes = result[0][0]
        date_heure = result[0][1]

        # Vérifier la taille
        if len(video_bytes) < 100:
            print(f"⚠ Attention: fichier très petit ({len(video_bytes)} bytes)")
            print("  Cela pourrait être une simulation, pas une vraie vidéo")

        # Générer le nom de fichier si non fourni
        if not nom_fichier:
            timestamp = date_heure.strftime("%Y%m%d_%H%M%S")
            nom_fichier = f"video_{id_donnee}_{timestamp}.h264"

        # Créer le dossier videos_extraites s'il n'existe pas
        os.makedirs("videos_extraites", exist_ok=True)
        chemin_complet = os.path.join("videos_extraites", nom_fichier)

        # Sauvegarder la vidéo
        with open(chemin_complet, 'wb') as f:
            f.write(video_bytes)

        taille_kb = len(video_bytes) / 1024
        taille_mb = taille_kb / 1024

        if taille_mb > 1:
            taille_str = f"{taille_mb:.2f} MB"
        else:
            taille_str = f"{taille_kb:.1f} KB"

        print(f"✓ Vidéo extraite: {chemin_complet} ({taille_str})")

        # Si c'est un vrai fichier H.264, donner des instructions
        if len(video_bytes) > 1000:
            print("\n📹 Pour lire la vidéo H.264:")
            print(f"   vlc {chemin_complet}")
            print(f"   # ou")
            print(f"   ffplay {chemin_complet}")
            print(f"\n🔄 Pour convertir en MP4:")
            print(f"   ffmpeg -i {chemin_complet} -c copy video_{id_donnee}.mp4")

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        db.disconnect()


def extraire_toutes_videos():
    """Extrait toutes les vidéos de la BD"""

    print("\n=== Extraction de toutes les vidéos ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("✗ Impossible de se connecter à la base de données")
        return

    try:
        # Récupérer toutes les vidéos
        videos = db.execute_query("""
            SELECT
                d.idDonnee_PK,
                d.photoBlob,
                d.dateHeure
            FROM Donnees d
            JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
            WHERE d.photoBlob IS NOT NULL
              AND c.type = N'CAMERA'
              AND DATALENGTH(d.photoBlob) > 100
            ORDER BY d.dateHeure DESC
        """)

        if not videos:
            print("Aucune vidéo trouvée")
            return

        # Créer le dossier
        os.makedirs("videos_extraites", exist_ok=True)

        print(f"Extraction de {len(videos)} vidéo(s)...\n")

        for video in videos:
            id_donnee = video[0]
            video_bytes = video[1]
            date_heure = video[2]

            timestamp = date_heure.strftime("%Y%m%d_%H%M%S")
            nom_fichier = f"video_{id_donnee}_{timestamp}.h264"
            chemin_complet = os.path.join("videos_extraites", nom_fichier)

            with open(chemin_complet, 'wb') as f:
                f.write(video_bytes)

            taille_kb = len(video_bytes) / 1024
            taille_mb = taille_kb / 1024

            if taille_mb > 1:
                taille_str = f"{taille_mb:.2f} MB"
            else:
                taille_str = f"{taille_kb:.1f} KB"

            print(f"  ✓ {nom_fichier} ({taille_str})")

        print(f"\n✓ {len(videos)} vidéo(s) extraite(s) dans 'videos_extraites/'")

        # Instructions
        print("\n📹 Pour lire les vidéos:")
        print("   cd videos_extraites")
        print("   vlc video_*.h264")
        print("\n🔄 Pour convertir en MP4:")
        print("   cd videos_extraites")
        print("   for f in *.h264; do ffmpeg -i \"$f\" -c copy \"${f%.h264}.mp4\"; done")

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        db.disconnect()


def afficher_historique_evenements():
    """Affiche l'historique des événements BRUIT_FORT avec leurs vidéos associées"""

    print("\n=== Historique des événements avec vidéos ===\n")

    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("✗ Impossible de se connecter à la base de données")
        return

    try:
        # Récupérer les événements BRUIT_FORT et leurs vidéos associées
        historique = db.execute_query("""
            SELECT
                e1.idEvenement_PK,
                d1.dateHeure AS date_bruit,
                e1.description AS desc_bruit,
                e2.idEvenement_PK AS id_event_video,
                d2.idDonnee_PK AS id_video,
                DATALENGTH(d2.photoBlob) AS taille_video
            FROM Evenement e1
            JOIN Donnees d1 ON e1.idDonnee = d1.idDonnee_PK
            LEFT JOIN Evenement e2 ON e2.type = N'CAPTURE'
                AND e2.description LIKE '%Event ID: ' + CAST(e1.idEvenement_PK AS NVARCHAR) + '%'
            LEFT JOIN Donnees d2 ON e2.idDonnee = d2.idDonnee_PK
            WHERE e1.type = N'BRUIT_FORT'
            ORDER BY d1.dateHeure DESC
        """)

        if not historique:
            print("Aucun événement BRUIT_FORT trouvé")
            return

        print(f"Total: {len(historique)} événement(s)\n")
        print("─" * 100)

        for event in historique:
            id_event = event[0]
            date_bruit = event[1]
            desc_bruit = event[2]
            id_event_video = event[3]
            id_video = event[4]
            taille_video = event[5]

            print(f"🔊 Event #{id_event} | {date_bruit}")
            print(f"   {desc_bruit}")

            if id_video:
                taille_mb = (taille_video / 1024 / 1024) if taille_video else 0
                print(f"   🎬 Vidéo associée: ID {id_video} ({taille_mb:.2f} MB)")
                print(f"      Pour extraire: python visualiser_videos.py (option 2, ID {id_video})")
            else:
                print(f"   ⚠ Aucune vidéo associée")

            print()

        print("─" * 100)

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        db.disconnect()


def menu():
    """Menu interactif"""
    while True:
        print("\n╔═══════════════════════════════════════════════════════════╗")
        print("║        Visualiseur de Vidéos - SalleSense                ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print("\n1. Lister toutes les vidéos")
        print("2. Extraire une vidéo (par ID)")
        print("3. Extraire toutes les vidéos")
        print("4. Afficher historique des événements avec vidéos")
        print("5. Quitter")
        print()

        choix = input("Votre choix: ").strip()

        if choix == "1":
            lister_videos()

        elif choix == "2":
            try:
                id_donnee = int(input("\nID de la vidéo à extraire: "))
                extraire_video(id_donnee)
            except ValueError:
                print("✗ ID invalide")

        elif choix == "3":
            extraire_toutes_videos()

        elif choix == "4":
            afficher_historique_evenements()

        elif choix == "5":
            print("\nAu revoir!\n")
            break

        else:
            print("\n✗ Choix invalide")


if __name__ == "__main__":
    menu()
