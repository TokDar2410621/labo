"""
Configuration centrale pour le projet SalleSense
"""

# Configuration base de données
DB_SERVER = "DICJWIN01.cegepjonquiere.ca"
DB_NAME = "Prog3A25_bdSalleSense"
DB_USERNAME = "prog3e09"
DB_PASSWORD = "colonne42" # À définir si nécessaire

# Configuration salle
ID_SALLE = 1  # ID de la salle à monitorer (doit exister dans la table Salle)

# Configuration GPIO - Micro électret
SOUND_PIN = 18  # Pin GPIO pour le module micro (sortie digitale)
# Si vous utilisez un ADC (MCP3008), configurez aussi:
ADC_CHANNEL = 0  # Canal ADC pour le micro
SPI_BUS = 0
SPI_DEVICE = 0

# Configuration capteurs
SEUIL_BRUIT_FORT = 70.0  # Seuil en dB (ou valeur arbitraire) pour déclencher un événement

# Configuration monitoring
INTERVALLE_BRUIT = 5   # Secondes entre chaque mesure de bruit
INTERVALLE_PHOTO = 60  # Secondes entre chaque capture photo

# Configuration photos
PHOTO_DIR = "photos"  # Dossier où sauvegarder les photos
PHOTO_WIDTH = 1920    # Largeur des photos (pixels)
PHOTO_HEIGHT = 1080   # Hauteur des photos (pixels)
