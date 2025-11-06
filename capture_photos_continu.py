"""
Script de capture continue de photos avec la Pi Camera
Les photos sont prises toutes les 5 secondes et envoyées vers la BD
"""

import time
from datetime import datetime
from io import BytesIO
from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD, ID_SALLE

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    print("⚠ picamera2 non disponible - mode simulation")
    CAMERA_AVAILABLE = False


class CapturePhotosContinu:
    """Capture des photos en continu et les envoie vers la BD"""

    def __init__(self, db_connection: DatabaseConnection, id_salle: int, intervalle: int = 5):
        """
        Initialise le système de capture

        Args:
            db_connection: Connexion à la base de données
            id_salle: ID de la salle à monitorer
            intervalle: Intervalle en secondes entre chaque photo (défaut: 5)
        """
        self.db = db_connection
        self.id_salle = id_salle
        self.intervalle = intervalle
        self.camera = None
        self.id_capteur_camera = None
        self.compteur_photos = 0

    def setup(self):
        """Configure la caméra et récupère l'ID du capteur"""
        print("=== Configuration du système de capture ===\n")

        # 1. Récupérer l'ID du capteur caméra
        try:
            capteur = self.db.execute_query(
                "SELECT idCapteur_PK FROM Capteur WHERE type = 'CAMERA'"
            )

            if not capteur:
                print("✗ Aucun capteur CAMERA trouvé dans la BD")
                print("   Lancez d'abord: python initialiser_bd.py")
                return False

            self.id_capteur_camera = capteur[0][0]
            print(f"✓ Capteur CAMERA trouvé - ID: {self.id_capteur_camera}")

        except Exception as e:
            print(f"✗ Erreur lors de la récupération du capteur: {e}")
            return False

        # 2. Initialiser la caméra
        if CAMERA_AVAILABLE:
            try:
                self.camera = Picamera2()

                # Configuration pour capture d'images JPEG
                config = self.camera.create_still_configuration(
                    main={"size": (1920, 1080)},  # Résolution Full HD
                    buffer_count=2
                )
                self.camera.configure(config)
                self.camera.start()

                print("✓ Pi Camera initialisée (1920x1080)")

                # Temps de stabilisation de la caméra
                print("⏳ Stabilisation de la caméra (2 secondes)...")
                time.sleep(2)

            except Exception as e:
                print(f"✗ Erreur lors de l'initialisation de la caméra: {e}")
                print("   Vérifiez que la caméra est connectée et activée (raspi-config)")
                return False
        else:
            print("⚠ Mode simulation - Pas de vraie caméra")

        print("\n✓ Configuration terminée\n")
        return True

    def capturer_photo(self) -> bytes:
        """
        Capture une photo et la retourne sous forme de bytes (JPEG)

        Returns:
            Données binaires de la photo (JPEG)
        """
        if CAMERA_AVAILABLE and self.camera:
            try:
                # Capturer l'image en mémoire (format JPEG)
                buffer = BytesIO()
                self.camera.capture_file(buffer, format='jpeg')
                photo_bytes = buffer.getvalue()
                buffer.close()

                return photo_bytes

            except Exception as e:
                print(f"✗ Erreur lors de la capture: {e}")
                return None
        else:
            # Mode simulation - Créer des données factices
            return b"PHOTO_SIMULEE_" + str(datetime.now()).encode()

    def envoyer_photo_bd(self, photo_bytes: bytes) -> bool:
        """
        Envoie la photo vers la base de données

        Args:
            photo_bytes: Données binaires de la photo

        Returns:
            True si succès, False sinon
        """
        try:
            date_heure = datetime.now()

            # Insérer la photo dans la BD
            self.db.execute_non_query(
                """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photoBlob, noSalle)
                   VALUES (?, ?, NULL, ?, ?)""",
                (date_heure, self.id_capteur_camera, photo_bytes, self.id_salle)
            )

            # Récupérer l'ID de la donnée insérée
            id_donnee = self.db.execute_query("SELECT @@IDENTITY AS id")[0][0]

            # Créer un événement
            self.db.execute_non_query(
                """INSERT INTO Evenement (type, idDonnee, description)
                   VALUES (?, ?, ?)""",
                ('CAPTURE', id_donnee, f'Photo capturée à {date_heure.strftime("%H:%M:%S")}')
            )

            self.compteur_photos += 1
            taille_kb = len(photo_bytes) / 1024

            print(f"[{date_heure.strftime('%H:%M:%S')}] Photo #{self.compteur_photos} envoyée "
                  f"({taille_kb:.1f} KB) - ID: {id_donnee}")

            return True

        except Exception as e:
            print(f"✗ Erreur lors de l'envoi: {e}")
            return False

    def capturer_en_continu(self):
        """Boucle principale de capture continue"""
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║      Capture de photos en continu - Pi Camera V2         ║")
        print("╚═══════════════════════════════════════════════════════════╝\n")
        print(f"📷 Intervalle: {self.intervalle} secondes")
        print(f"🏢 Salle: {self.id_salle}")
        print(f"💾 Stockage: Base de données (VARBINARY)")
        print("\nAppuyez sur Ctrl+C pour arrêter\n")
        print("─" * 63)

        try:
            while True:
                # Capturer la photo
                photo_bytes = self.capturer_photo()

                if photo_bytes:
                    # Envoyer vers la BD
                    self.envoyer_photo_bd(photo_bytes)
                else:
                    print("✗ Échec de la capture")

                # Attendre avant la prochaine capture
                time.sleep(self.intervalle)

        except KeyboardInterrupt:
            print("\n\n─" * 63)
            print(f"\n✓ Arrêt demandé - {self.compteur_photos} photos capturées")
            print("✓ Programme terminé")

    def cleanup(self):
        """Nettoie les ressources (caméra)"""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                print("✓ Caméra fermée proprement")
            except:
                pass


def main():
    """Fonction principale"""
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║        SalleSense - Capture Photos en Continu            ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    # Connexion à la base de données
    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("\n✗ Impossible de se connecter à la base de données")
        return 1

    # Créer le système de capture
    capture_system = CapturePhotosContinu(db, ID_SALLE, intervalle=5)

    # Configuration
    if not capture_system.setup():
        db.disconnect()
        return 1

    try:
        # Lancer la capture continue
        capture_system.capturer_en_continu()

    finally:
        # Nettoyage
        capture_system.cleanup()
        db.disconnect()
        print("✓ Connexion BD fermée\n")

    return 0


if __name__ == "__main__":
    exit(main())
