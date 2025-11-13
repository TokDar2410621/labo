"""
Système de surveillance intelligente
Capture du son en continu + enregistrement vidéo lors de bruit fort
"""

import spidev
import time
from datetime import datetime
from io import BytesIO
from threading import Thread, Event
from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD, ID_SALLE

try:
    import spidev
    SPI_AVAILABLE = True
except ImportError:
    print("⚠ spidev non disponible - mode simulation")
    SPI_AVAILABLE = False

try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import FileOutput
    CAMERA_AVAILABLE = True
except ImportError:
    print("⚠ picamera2 non disponible - mode simulation")
    CAMERA_AVAILABLE = False


class SurveillanceIntelligente:
    """
    Surveillance intelligente avec détection de bruit et enregistrement vidéo automatique
    """

    def __init__(self, db_connection: DatabaseConnection, id_salle: int,
                 intervalle: int = 1, seuil_bruit_fort: float = 50.0,
                 duree_video: int = 10):
        """
        Initialise le système de surveillance

        Args:
            db_connection: Connexion à la base de données
            id_salle: ID de la salle à monitorer
            intervalle: Intervalle en secondes entre mesures son (défaut: 1)
            seuil_bruit_fort: Seuil pour déclencher vidéo (défaut: 50.0)
            duree_video: Durée de la vidéo en secondes (défaut: 10)
        """
        self.db = db_connection
        self.id_salle = id_salle
        self.intervalle = intervalle
        self.seuil_bruit_fort = seuil_bruit_fort
        self.duree_video = duree_video

        # Composants
        self.spi = None
        self.camera = None
        self.id_capteur_bruit = None
        self.id_capteur_camera = None

        # Statistiques
        self.compteur_mesures = 0
        self.compteur_videos = 0

        # Paramètres MCP3008
        self.adc_channel = 0
        self.spi_bus = 0
        self.spi_device = 0
        self.spi_speed = 1350000
        self.valeur_repos = None

        # État d'enregistrement
        self.en_enregistrement = False
        self.stop_event = Event()

    def setup(self):
        """Configure tous les capteurs"""
        print("=== Configuration du système de surveillance intelligente ===\n")

        # 1. Récupérer les IDs des capteurs
        try:
            # Capteur BRUIT
            capteur_bruit = self.db.execute_query(
                "SELECT idCapteur_PK FROM Capteur WHERE type = 'BRUIT'"
            )
            if not capteur_bruit:
                print("✗ Aucun capteur BRUIT trouvé")
                return False
            self.id_capteur_bruit = capteur_bruit[0][0]
            print(f"✓ Capteur BRUIT trouvé - ID: {self.id_capteur_bruit}")

            # Capteur CAMERA
            capteur_camera = self.db.execute_query(
                "SELECT idCapteur_PK FROM Capteur WHERE type = 'CAMERA'"
            )
            if not capteur_camera:
                print("✗ Aucun capteur CAMERA trouvé")
                return False
            self.id_capteur_camera = capteur_camera[0][0]
            print(f"✓ Capteur CAMERA trouvé - ID: {self.id_capteur_camera}")

        except Exception as e:
            print(f"✗ Erreur récupération capteurs: {e}")
            return False

        # 2. Initialiser MCP3008
        if SPI_AVAILABLE:
            try:
                self.spi = spidev.SpiDev()
                self.spi.open(self.spi_bus, self.spi_device)
                self.spi.max_speed_hz = self.spi_speed
                print(f"✓ MCP3008 initialisé (SPI {self.spi_bus}.{self.spi_device})")

                # Calibration
                if self.calibrer():
                    print(f"✓ Calibration audio - Valeur repos: {self.valeur_repos}")
                else:
                    self.valeur_repos = 512
                    print("⚠ Calibration par défaut")

            except Exception as e:
                print(f"✗ Erreur MCP3008: {e}")
                return False
        else:
            print("⚠ Mode simulation - Pas de vrai MCP3008")
            self.valeur_repos = 512

        # 3. Initialiser caméra
        if CAMERA_AVAILABLE:
            try:
                self.camera = Picamera2()
                # Configuration vidéo
                video_config = self.camera.create_video_configuration(
                    main={"size": (1280, 720)},  # 720p
                    buffer_count=4
                )
                self.camera.configure(video_config)
                print("✓ Pi Camera initialisée (720p)")

            except Exception as e:
                print(f"✗ Erreur caméra: {e}")
                self.camera = None
        else:
            print("⚠ Mode simulation - Pas de vraie caméra")

        print("\n✓ Configuration terminée\n")
        return True

    def read_adc(self, channel: int) -> int:
        """Lit une valeur du MCP3008"""
        if not SPI_AVAILABLE or self.spi is None:
            import random
            return random.randint(480, 550)

        if channel < 0 or channel > 7:
            return -1

        try:
            adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
            data = ((adc[1] & 3) << 8) + adc[2]
            return data
        except Exception as e:
            return -1

    def calibrer(self) -> bool:
        """Calibre le micro"""
        print("⏳ Calibration audio... (2 secondes)")
        try:
            valeurs = []
            for _ in range(20):
                valeur = self.read_adc(self.adc_channel)
                if valeur >= 0:
                    valeurs.append(valeur)
                time.sleep(0.1)

            if valeurs:
                self.valeur_repos = sum(valeurs) // len(valeurs)
                return True
            return False
        except:
            return False

    def mesurer_son(self) -> dict:
        """Mesure le niveau sonore"""
        nb_echantillons = 10
        valeurs = []

        for _ in range(nb_echantillons):
            valeur = self.read_adc(self.adc_channel)
            if valeur >= 0:
                valeurs.append(valeur)
            time.sleep(0.01)

        if not valeurs:
            return None

        valeur_moyenne = sum(valeurs) // len(valeurs)
        valeur_max = max(valeurs)
        valeur_min = min(valeurs)
        amplitude = valeur_max - valeur_min

        voltage = (valeur_moyenne * 3.3) / 1023
        difference = abs(valeur_moyenne - self.valeur_repos) if self.valeur_repos else 0
        niveau_db = min(100, (amplitude / 10.23) * 10)

        return {
            'valeur_brute': valeur_moyenne,
            'amplitude': amplitude,
            'voltage': voltage,
            'difference': difference,
            'niveau_db': niveau_db
        }

    def enregistrer_video(self, id_evenement: int, niveau_db: float):
        """
        Enregistre une vidéo et l'envoie vers la BD

        Args:
            id_evenement: ID de l'événement qui a déclenché l'enregistrement
            niveau_db: Niveau sonore qui a déclenché
        """
        if self.en_enregistrement:
            print("         ⚠ Enregistrement déjà en cours, ignoré")
            return

        self.en_enregistrement = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"\n         🎬 ENREGISTREMENT VIDÉO DÉCLENCHÉ!")
        print(f"         📹 Durée: {self.duree_video}s | Déclencheur: {niveau_db:.1f} dB")

        try:
            if CAMERA_AVAILABLE and self.camera:
                # Enregistrer en mémoire (BytesIO)
                video_buffer = BytesIO()

                # Démarrer l'enregistrement
                self.camera.start_recording(
                    encoder=H264Encoder(),
                    output=FileOutput(video_buffer)
                )

                # Enregistrer pendant la durée spécifiée
                debut = time.time()
                while time.time() - debut < self.duree_video:
                    temps_restant = int(self.duree_video - (time.time() - debut))
                    if temps_restant > 0 and temps_restant % 2 == 0:
                        print(f"         ⏱ {temps_restant}s restantes...", end='\r')
                    time.sleep(0.5)

                # Arrêter l'enregistrement
                self.camera.stop_recording()

                # Récupérer les bytes de la vidéo
                video_bytes = video_buffer.getvalue()
                video_buffer.close()

                print(f"         ✓ Vidéo capturée ({len(video_bytes)/1024:.1f} KB)      ")

            else:
                # Mode simulation
                video_bytes = b"VIDEO_SIMULEE_" + timestamp.encode() + b"_" + str(self.duree_video).encode() + b"s"
                time.sleep(2)  # Simuler un enregistrement
                print(f"         ✓ Vidéo simulée ({len(video_bytes)} bytes)")

            # Envoyer vers la BD
            date_heure = datetime.now()
            self.db.execute_non_query(
                """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photoBlob, noSalle)
                   VALUES (?, ?, NULL, ?, ?)""",
                (date_heure, self.id_capteur_camera, video_bytes, self.id_salle)
            )

            id_donnee = self.db.execute_query("SELECT @@IDENTITY AS id")[0][0]
            self.compteur_videos += 1

            # Créer un événement
            self.db.execute_non_query(
                """INSERT INTO Evenement (type, idDonnee, description)
                   VALUES (?, ?, ?)""",
                ('CAPTURE', id_donnee,
                 f'Vidéo {self.duree_video}s - Déclenchée par BRUIT_FORT ({niveau_db:.1f} dB) - Event ID: {id_evenement}')
            )

            print(f"         ✓ Vidéo enregistrée en BD - ID: {id_donnee}")
            print()

        except Exception as e:
            print(f"         ✗ Erreur enregistrement vidéo: {e}\n")

        finally:
            self.en_enregistrement = False

    def surveiller_en_continu(self):
        """Boucle principale de surveillance"""
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║         Surveillance Intelligente - SalleSense           ║")
        print("╚═══════════════════════════════════════════════════════════╝\n")
        print(f"🎤 Intervalle mesures: {self.intervalle}s")
        print(f"🏢 Salle: {self.id_salle}")
        print(f"📊 Seuil déclenchement: {self.seuil_bruit_fort} dB")
        print(f"🎬 Durée vidéo: {self.duree_video}s")
        print(f"💾 Stockage: Base de données")
        print("\nAppuyez sur Ctrl+C pour arrêter\n")
        print("─" * 63)

        try:
            while not self.stop_event.is_set():
                # Mesurer le son
                mesure = self.mesurer_son()

                if mesure:
                    date_heure = datetime.now()
                    niveau_db = mesure['niveau_db']

                    # Enregistrer la mesure de son
                    self.db.execute_non_query(
                        """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photoBlob, noSalle)
                           VALUES (?, ?, ?, NULL, ?)""",
                        (date_heure, self.id_capteur_bruit, niveau_db, self.id_salle)
                    )

                    id_donnee = self.db.execute_query("SELECT @@IDENTITY AS id")[0][0]
                    self.compteur_mesures += 1

                    # Affichage
                    heure = date_heure.strftime('%H:%M:%S')
                    print(f"[{heure}] Son #{self.compteur_mesures:4d} | "
                          f"Niveau: {niveau_db:5.1f} dB | "
                          f"Amplitude: {mesure['amplitude']:4d} | "
                          f"ID: {id_donnee}")

                    # Si bruit fort : créer événement + déclencher vidéo
                    if niveau_db > self.seuil_bruit_fort:
                        # Créer événement BRUIT_FORT
                        self.db.execute_non_query(
                            """INSERT INTO Evenement (type, idDonnee, description)
                               VALUES (?, ?, ?)""",
                            ('BRUIT_FORT', id_donnee,
                             f'Niveau sonore élevé: {niveau_db:.1f} dB (amplitude: {mesure["amplitude"]})')
                        )
                        id_evenement = self.db.execute_query("SELECT @@IDENTITY AS id")[0][0]

                        print(f"         ⚠ BRUIT_FORT détecté! (Event ID: {id_evenement})")

                        # Lancer l'enregistrement vidéo dans un thread séparé
                        # pour ne pas bloquer la surveillance audio
                        video_thread = Thread(
                            target=self.enregistrer_video,
                            args=(id_evenement, niveau_db)
                        )
                        video_thread.daemon = True
                        video_thread.start()

                else:
                    print("✗ Échec mesure son")

                # Attendre avant la prochaine mesure
                time.sleep(self.intervalle)

        except KeyboardInterrupt:
            print("\n\n─" * 63)
            print(f"\n📊 Statistiques de session:")
            print(f"   • Mesures audio: {self.compteur_mesures}")
            print(f"   • Vidéos enregistrées: {self.compteur_videos}")
            print("\n✓ Arrêt demandé - Programme terminé")

    def cleanup(self):
        """Nettoie les ressources"""
        self.stop_event.set()

        if self.spi:
            try:
                self.spi.close()
                print("✓ SPI fermé")
            except:
                pass

        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                print("✓ Caméra fermée")
            except:
                pass


def main():
    """Fonction principale"""
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║    SalleSense - Surveillance Intelligente avec Vidéo     ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    # Connexion BD
    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("\n✗ Impossible de se connecter à la base de données")
        return 1

    # Créer le système de surveillance
    # Paramètres: intervalle=1s, seuil=50dB, durée_vidéo=10s
    surveillance = SurveillanceIntelligente(
        db, ID_SALLE,
        intervalle=1,
        seuil_bruit_fort=50.0,
        duree_video=10
    )

    # Configuration
    if not surveillance.setup():
        db.disconnect()
        return 1

    try:
        # Lancer la surveillance
        surveillance.surveiller_en_continu()

    finally:
        # Nettoyage
        surveillance.cleanup()
        db.disconnect()
        print("✓ Connexion BD fermée\n")

    return 0


if __name__ == "__main__":
    exit(main())
