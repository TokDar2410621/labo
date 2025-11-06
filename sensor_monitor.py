"""
Module de monitoring des capteurs pour SalleSense
Capteur de son (micro électret) et Pi Camera Module V2
"""

import time
import os
from datetime import datetime
from typing import Optional
import RPi.GPIO as GPIO

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    print("⚠ picamera2 non disponible - mode simulation pour la caméra")
    CAMERA_AVAILABLE = False

from db_connection import DatabaseConnection


class SensorMonitor:
    """Gère le monitoring des capteurs et l'envoi des données vers la BD"""

    def __init__(self, db_connection: DatabaseConnection, id_salle: int):
        """
        Initialise le moniteur de capteurs

        Args:
            db_connection: Instance de connexion à la base de données
            id_salle: ID de la salle à monitorer
        """
        self.db = db_connection
        self.id_salle = id_salle

        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)

        # Configuration micro électret (pin analogique via ADC)
        # Note: Le Raspberry Pi n'a pas d'entrée analogique native
        # Il faut utiliser un ADC comme le MCP3008
        self.adc_channel = 0  # Canal ADC pour le micro
        self.sound_pin = 18   # Pin digital si vous utilisez un module avec sortie digitale

        # Configuration caméra
        self.camera = None
        self.photo_dir = "photos"

        # IDs des capteurs (à récupérer de la BD)
        self.id_capteur_bruit = None
        self.id_capteur_camera = None

        # Seuils
        self.seuil_bruit_fort = 70.0  # dB ou valeur arbitraire

    def setup(self):
        """Configure les capteurs et vérifie leur présence dans la BD"""
        print("=== Configuration des capteurs ===")

        # Créer le dossier photos s'il n'existe pas
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)
            print(f"✓ Dossier '{self.photo_dir}/' créé")

        # Récupérer les IDs des capteurs depuis la BD
        try:
            capteurs = self.db.execute_query(
                "SELECT idCapteur_PK, nom, type FROM Capteur WHERE type IN ('BRUIT', 'CAMERA')"
            )

            for capteur in capteurs:
                if capteur[2] == 'BRUIT':
                    self.id_capteur_bruit = capteur[0]
                    print(f"✓ Capteur BRUIT trouvé - ID: {capteur[0]}, Nom: {capteur[1]}")
                elif capteur[2] == 'CAMERA':
                    self.id_capteur_camera = capteur[0]
                    print(f"✓ Capteur CAMERA trouvé - ID: {capteur[0]}, Nom: {capteur[1]}")

            # Si les capteurs n'existent pas, les créer
            if self.id_capteur_bruit is None:
                self.db.execute_non_query(
                    "INSERT INTO Capteur (nom, type) VALUES (?, ?)",
                    ('MIC-ELECTRET-1', 'BRUIT')
                )
                result = self.db.execute_query("SELECT @@IDENTITY AS id")
                self.id_capteur_bruit = result[0][0]
                print(f"✓ Capteur BRUIT créé - ID: {self.id_capteur_bruit}")

            if self.id_capteur_camera is None:
                self.db.execute_non_query(
                    "INSERT INTO Capteur (nom, type) VALUES (?, ?)",
                    ('PICAM-V2-1', 'CAMERA')
                )
                result = self.db.execute_query("SELECT @@IDENTITY AS id")
                self.id_capteur_camera = result[0][0]
                print(f"✓ Capteur CAMERA créé - ID: {self.id_capteur_camera}")

        except Exception as e:
            print(f"✗ Erreur lors de la configuration des capteurs: {e}")
            return False

        # Initialiser la caméra si disponible
        if CAMERA_AVAILABLE:
            try:
                self.camera = Picamera2()
                camera_config = self.camera.create_still_configuration()
                self.camera.configure(camera_config)
                print("✓ Pi Camera initialisée")
            except Exception as e:
                print(f"✗ Erreur d'initialisation de la caméra: {e}")
                self.camera = None

        print("✓ Configuration terminée\n")
        return True

    def read_sound_level(self) -> float:
        """
        Lit le niveau sonore du micro électret

        Returns:
            Niveau sonore (en dB ou valeur arbitraire)
        """
        # MÉTHODE 1: Si vous utilisez un ADC (MCP3008)
        # Vous devrez installer spidev: pip install spidev
        # et implémenter la lecture SPI

        # MÉTHODE 2: Si vous utilisez un module avec sortie digitale
        # GPIO.setup(self.sound_pin, GPIO.IN)
        # digital_value = GPIO.input(self.sound_pin)

        # Pour l'instant, simulation avec une valeur aléatoire
        import random
        sound_level = random.uniform(40.0, 80.0)

        # TODO: Remplacer par la vraie lecture de votre capteur
        # Exemple avec ADC:
        # sound_level = self.read_adc(self.adc_channel)
        # sound_level = self.convert_to_db(sound_level)

        return sound_level

    def capture_photo(self) -> Optional[str]:
        """
        Capture une photo avec la Pi Camera

        Returns:
            Chemin de la photo capturée, ou None si erreur
        """
        if not CAMERA_AVAILABLE or self.camera is None:
            print("⚠ Caméra non disponible")
            return None

        try:
            # Générer un nom de fichier unique avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"salle{self.id_salle}_{timestamp}.jpg"
            filepath = os.path.join(self.photo_dir, filename)

            # Capturer la photo
            self.camera.start()
            time.sleep(2)  # Laisser le temps à la caméra de s'ajuster
            self.camera.capture_file(filepath)
            self.camera.stop()

            print(f"✓ Photo capturée: {filepath}")
            return filepath

        except Exception as e:
            print(f"✗ Erreur lors de la capture photo: {e}")
            return None

    def envoyer_donnee_bruit(self, niveau_sonore: float) -> Optional[int]:
        """
        Envoie une mesure de bruit vers la base de données

        Args:
            niveau_sonore: Niveau sonore mesuré

        Returns:
            ID de la donnée insérée, ou None si erreur
        """
        try:
            date_heure = datetime.now()

            # Insérer la donnée
            self.db.execute_non_query(
                """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
                   VALUES (?, ?, ?, NULL, ?)""",
                (date_heure, self.id_capteur_bruit, niveau_sonore, self.id_salle)
            )

            # Récupérer l'ID de la donnée insérée
            result = self.db.execute_query("SELECT @@IDENTITY AS id")
            id_donnee = result[0][0]

            print(f"📊 Bruit enregistré: {niveau_sonore:.1f} dB - ID: {id_donnee}")

            # Créer un événement si bruit fort
            if niveau_sonore > self.seuil_bruit_fort:
                self.creer_evenement('BRUIT_FORT', id_donnee,
                                    f"Niveau sonore élevé: {niveau_sonore:.1f} dB")

            return id_donnee

        except Exception as e:
            print(f"✗ Erreur lors de l'envoi de la donnée de bruit: {e}")
            return None

    def envoyer_donnee_photo(self, chemin_photo: str) -> Optional[int]:
        """
        Envoie une photo vers la base de données

        Args:
            chemin_photo: Chemin de la photo capturée

        Returns:
            ID de la donnée insérée, ou None si erreur
        """
        try:
            date_heure = datetime.now()

            # Insérer la donnée
            self.db.execute_non_query(
                """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
                   VALUES (?, ?, NULL, ?, ?)""",
                (date_heure, self.id_capteur_camera, chemin_photo, self.id_salle)
            )

            # Récupérer l'ID de la donnée insérée
            result = self.db.execute_query("SELECT @@IDENTITY AS id")
            id_donnee = result[0][0]

            print(f"📷 Photo enregistrée: {chemin_photo} - ID: {id_donnee}")

            # Créer un événement
            self.creer_evenement('CAPTURE', id_donnee,
                                f"Photo enregistrée: {chemin_photo}")

            return id_donnee

        except Exception as e:
            print(f"✗ Erreur lors de l'envoi de la photo: {e}")
            return None

    def creer_evenement(self, type_event: str, id_donnee: int, description: str):
        """
        Crée un événement dans la base de données

        Args:
            type_event: Type d'événement (BRUIT_FORT, CAPTURE, etc.)
            id_donnee: ID de la donnée associée
            description: Description de l'événement
        """
        try:
            self.db.execute_non_query(
                """INSERT INTO Evenement (type, idDonnee, description)
                   VALUES (?, ?, ?)""",
                (type_event, id_donnee, description)
            )
            print(f"⚡ Événement créé: {type_event}")

        except Exception as e:
            print(f"✗ Erreur lors de la création de l'événement: {e}")

    def monitorer_continu(self, intervalle_bruit: int = 5, intervalle_photo: int = 60):
        """
        Boucle de monitoring continue des capteurs

        Args:
            intervalle_bruit: Intervalle en secondes entre les mesures de bruit
            intervalle_photo: Intervalle en secondes entre les captures photo
        """
        print("=== Démarrage du monitoring continu ===")
        print(f"Intervalle mesure bruit: {intervalle_bruit}s")
        print(f"Intervalle capture photo: {intervalle_photo}s")
        print("Appuyez sur Ctrl+C pour arrêter\n")

        dernier_temps_photo = time.time()

        try:
            while True:
                # Mesurer le niveau sonore
                niveau_sonore = self.read_sound_level()
                self.envoyer_donnee_bruit(niveau_sonore)

                # Capturer une photo si l'intervalle est écoulé
                temps_actuel = time.time()
                if temps_actuel - dernier_temps_photo >= intervalle_photo:
                    chemin_photo = self.capture_photo()
                    if chemin_photo:
                        self.envoyer_donnee_photo(chemin_photo)
                    dernier_temps_photo = temps_actuel

                # Attendre avant la prochaine mesure
                time.sleep(intervalle_bruit)

        except KeyboardInterrupt:
            print("\n\n=== Arrêt du monitoring ===")
        finally:
            self.cleanup()

    def cleanup(self):
        """Nettoie les ressources (GPIO, caméra)"""
        GPIO.cleanup()
        if self.camera:
            self.camera.close()
        print("✓ Ressources libérées")


# Script principal
if __name__ == "__main__":
    # Importer la configuration
    from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD, ID_SALLE

    SERVER = DB_SERVER
    DATABASE = DB_NAME
    USERNAME = DB_USERNAME
    PASSWORD = DB_PASSWORD

    print("=== SalleSense - Monitoring des capteurs ===\n")

    # Connexion à la base de données
    db = DatabaseConnection(SERVER, DATABASE, USERNAME, PASSWORD)

    if not db.connect():
        print("Impossible de se connecter à la base de données")
        exit(1)

    # Initialiser le moniteur
    monitor = SensorMonitor(db, ID_SALLE)

    if not monitor.setup():
        print("Échec de la configuration des capteurs")
        db.disconnect()
        exit(1)

    # Lancer le monitoring continu
    try:
        monitor.monitorer_continu(intervalle_bruit=5, intervalle_photo=60)
    finally:
        db.disconnect()
