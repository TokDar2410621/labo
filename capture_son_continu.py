"""
Script de capture continue du son avec micro électret + MCP3008
Les mesures sont prises toutes les secondes et envoyées vers la BD
"""

import spidev
import time
from datetime import datetime
from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD, ID_SALLE

try:
    import spidev
    SPI_AVAILABLE = True
except ImportError:
    print("⚠ spidev non disponible - mode simulation")
    SPI_AVAILABLE = False


class CaptureSonContinu:
    """Capture du son en continu avec micro électret + MCP3008"""

    def __init__(self, db_connection: DatabaseConnection, id_salle: int,
                 intervalle: int = 1, seuil_bruit_fort: float = 50.0):
        """
        Initialise le système de capture audio

        Args:
            db_connection: Connexion à la base de données
            id_salle: ID de la salle à monitorer
            intervalle: Intervalle en secondes entre chaque mesure (défaut: 1)
            seuil_bruit_fort: Seuil pour déclencher événement BRUIT_FORT (défaut: 50.0)
        """
        self.db = db_connection
        self.id_salle = id_salle
        self.intervalle = intervalle
        self.seuil_bruit_fort = seuil_bruit_fort

        self.spi = None
        self.id_capteur_bruit = None
        self.compteur_mesures = 0

        # Paramètres ADC MCP3008
        self.adc_channel = 0  # Canal 0 pour le micro
        self.spi_bus = 0
        self.spi_device = 0
        self.spi_speed = 1350000

        # Calibration
        self.valeur_repos = None
        self.est_calibre = False

    def setup(self):
        """Configure le MCP3008 et récupère l'ID du capteur"""
        print("=== Configuration du système de capture audio ===\n")

        # 1. Récupérer l'ID du capteur de bruit
        try:
            capteur = self.db.execute_query(
                "SELECT idCapteur_PK FROM Capteur WHERE type = 'BRUIT'"
            )

            if not capteur:
                print("✗ Aucun capteur BRUIT trouvé dans la BD")
                print("   Lancez d'abord: python initialiser_bd.py")
                return False

            self.id_capteur_bruit = capteur[0][0]
            print(f"✓ Capteur BRUIT trouvé - ID: {self.id_capteur_bruit}")

        except Exception as e:
            print(f"✗ Erreur lors de la récupération du capteur: {e}")
            return False

        # 2. Initialiser le SPI et MCP3008
        if SPI_AVAILABLE:
            try:
                self.spi = spidev.SpiDev()
                self.spi.open(self.spi_bus, self.spi_device)
                self.spi.max_speed_hz = self.spi_speed
                print(f"✓ MCP3008 initialisé (SPI {self.spi_bus}.{self.spi_device})")

                # Calibration
                if self.calibrer():
                    print(f"✓ Calibration terminée - Valeur repos: {self.valeur_repos}")
                else:
                    print("⚠ Calibration échouée - Utilisation de valeur par défaut")
                    self.valeur_repos = 512
                    self.est_calibre = False

            except Exception as e:
                print(f"✗ Erreur lors de l'initialisation du MCP3008: {e}")
                print("   Vérifiez que le SPI est activé (raspi-config)")
                return False
        else:
            print("⚠ Mode simulation - Pas de vrai MCP3008")
            self.valeur_repos = 512

        print("\n✓ Configuration terminée\n")
        return True

    def read_adc(self, channel: int) -> int:
        """
        Lit une valeur du MCP3008

        Args:
            channel: Canal à lire (0-7)

        Returns:
            Valeur brute (0-1023)
        """
        if not SPI_AVAILABLE or self.spi is None:
            # Mode simulation
            import random
            return random.randint(480, 550)

        if channel < 0 or channel > 7:
            return -1

        try:
            # Commande SPI pour lire le canal
            adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
            data = ((adc[1] & 3) << 8) + adc[2]
            return data
        except Exception as e:
            print(f"✗ Erreur lecture ADC: {e}")
            return -1

    def calibrer(self) -> bool:
        """
        Calibre le micro en mesurant la valeur au repos

        Returns:
            True si succès, False sinon
        """
        print("⏳ Calibration... (silence pendant 2 secondes)")

        try:
            valeurs_repos = []
            for i in range(20):
                valeur = self.read_adc(self.adc_channel)
                if valeur >= 0:
                    valeurs_repos.append(valeur)
                time.sleep(0.1)

            if len(valeurs_repos) > 0:
                self.valeur_repos = sum(valeurs_repos) // len(valeurs_repos)
                self.est_calibre = True
                return True
            else:
                return False

        except Exception as e:
            print(f"✗ Erreur calibration: {e}")
            return False

    def mesurer_son(self) -> dict:
        """
        Mesure le niveau sonore

        Returns:
            Dictionnaire avec valeur_brute, voltage, difference, niveau_db
        """
        # Lire plusieurs échantillons pour lisser
        nb_echantillons = 10
        valeurs = []

        for _ in range(nb_echantillons):
            valeur = self.read_adc(self.adc_channel)
            if valeur >= 0:
                valeurs.append(valeur)
            time.sleep(0.01)

        if not valeurs:
            return None

        # Calculer la moyenne et le pic
        valeur_moyenne = sum(valeurs) // len(valeurs)
        valeur_max = max(valeurs)
        valeur_min = min(valeurs)
        amplitude = valeur_max - valeur_min

        # Convertir en voltage (0-3.3V pour le Raspberry Pi)
        voltage = (valeur_moyenne * 3.3) / 1023

        # Différence par rapport au repos
        difference = abs(valeur_moyenne - self.valeur_repos) if self.valeur_repos else 0

        # Conversion approximative en dB
        # Formule simplifiée : dB = 20 * log10(amplitude / ref)
        # Ici on utilise une échelle arbitraire 0-100
        niveau_db = min(100, (amplitude / 10.23) * 10)  # Échelle 0-100

        return {
            'valeur_brute': valeur_moyenne,
            'amplitude': amplitude,
            'voltage': voltage,
            'difference': difference,
            'niveau_db': niveau_db
        }

    def envoyer_mesure_bd(self, mesure: dict) -> bool:
        """
        Envoie la mesure vers la base de données

        Args:
            mesure: Dictionnaire contenant les données de mesure

        Returns:
            True si succès, False sinon
        """
        try:
            date_heure = datetime.now()
            niveau_db = mesure['niveau_db']

            # Insérer la mesure
            self.db.execute_non_query(
                """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photoBlob, noSalle)
                   VALUES (?, ?, ?, NULL, ?)""",
                (date_heure, self.id_capteur_bruit, niveau_db, self.id_salle)
            )

            # Récupérer l'ID de la donnée insérée
            id_donnee = self.db.execute_query("SELECT @@IDENTITY AS id")[0][0]

            self.compteur_mesures += 1

            # Affichage
            heure = date_heure.strftime('%H:%M:%S')
            print(f"[{heure}] Mesure #{self.compteur_mesures:4d} | "
                  f"Niveau: {niveau_db:5.1f} dB | "
                  f"Amplitude: {mesure['amplitude']:4d} | "
                  f"ID: {id_donnee}")

            # Créer un événement si bruit fort
            if niveau_db > self.seuil_bruit_fort:
                self.db.execute_non_query(
                    """INSERT INTO Evenement (type, idDonnee, description)
                       VALUES (?, ?, ?)""",
                    ('BRUIT_FORT', id_donnee,
                     f'Niveau sonore élevé: {niveau_db:.1f} dB (amplitude: {mesure["amplitude"]})')
                )
                print(f"         ⚠ BRUIT_FORT détecté!")

            return True

        except Exception as e:
            print(f"✗ Erreur lors de l'envoi: {e}")
            return False

    def capturer_en_continu(self):
        """Boucle principale de capture continue"""
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║    Capture de son en continu - Micro Électret MCP3008    ║")
        print("╚═══════════════════════════════════════════════════════════╝\n")
        print(f"🎤 Intervalle: {self.intervalle} seconde(s)")
        print(f"🏢 Salle: {self.id_salle}")
        print(f"📊 Seuil bruit fort: {self.seuil_bruit_fort} dB")
        print(f"💾 Stockage: Base de données")
        print("\nAppuyez sur Ctrl+C pour arrêter\n")
        print("─" * 63)

        try:
            while True:
                # Mesurer le son
                mesure = self.mesurer_son()

                if mesure:
                    # Envoyer vers la BD
                    self.envoyer_mesure_bd(mesure)
                else:
                    print("✗ Échec de la mesure")

                # Attendre avant la prochaine mesure
                time.sleep(self.intervalle)

        except KeyboardInterrupt:
            print("\n\n─" * 63)
            print(f"\n✓ Arrêt demandé - {self.compteur_mesures} mesures capturées")
            print("✓ Programme terminé")

    def cleanup(self):
        """Nettoie les ressources (SPI)"""
        if self.spi:
            try:
                self.spi.close()
                print("✓ SPI fermé proprement")
            except:
                pass


def main():
    """Fonction principale"""
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║        SalleSense - Capture Son en Continu               ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    # Connexion à la base de données
    db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)

    if not db.connect():
        print("\n✗ Impossible de se connecter à la base de données")
        return 1

    # Créer le système de capture
    # Paramètres : intervalle=1s, seuil_bruit_fort=50dB
    capture_system = CaptureSonContinu(db, ID_SALLE, intervalle=1, seuil_bruit_fort=50.0)

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
