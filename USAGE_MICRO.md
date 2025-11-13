# Guide d'utilisation - Capture du son avec Micro Électret + MCP3008

## 🎤 Programme principal : capture_son_continu.py

Ce programme capture le niveau sonore avec votre micro électret + MCP3008 et envoie les mesures vers la base de données.

### Caractéristiques

- ✓ Mesure automatique toutes les secondes (configurable)
- ✓ Calibration automatique au démarrage
- ✓ Détection de bruit fort avec seuil
- ✓ Stockage direct en base de données
- ✓ Calcul d'amplitude et niveau dB
- ✓ Affichage en temps réel des mesures
- ✓ Arrêt propre avec Ctrl+C

### Configuration matérielle détectée

Basé sur vos scripts dans [lecture-micro/](lecture-micro/) :

**Matériel** :
- Micro électret (sortie analogique)
- ADC MCP3008 (8 canaux, 10 bits)
- SPI Bus 0, Device 0
- Canal 0 du MCP3008 pour le micro
- Vitesse SPI : 1.35 MHz

**Branchement MCP3008** :
```
MCP3008          Raspberry Pi
────────         ─────────────
VDD     ──────→  3.3V (Pin 1)
VREF    ──────→  3.3V (Pin 1)
AGND    ──────→  GND  (Pin 6)
CLK     ──────→  GPIO 11 (SCLK)
DOUT    ──────→  GPIO 9  (MISO)
DIN     ──────→  GPIO 10 (MOSI)
CS/SHDN ──────→  GPIO 8  (CE0)
DGND    ──────→  GND  (Pin 6)

CH0     ──────→  Sortie micro électret
```

### Installation

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer spidev (déjà fait)
pip install spidev
```

### Activation du SPI

Si c'est la première fois que vous utilisez le SPI :

```bash
sudo raspi-config
```

Puis : `Interface Options` → `SPI` → `Enable`

Vérifier que le SPI est activé :
```bash
ls /dev/spi*
# Devrait afficher : /dev/spidev0.0  /dev/spidev0.1
```

### Utilisation

#### Lancer la capture continue

```bash
source venv/bin/activate
python capture_son_continu.py
```

**Sortie attendue** :
```
╔═══════════════════════════════════════════════════════════╗
║    Capture de son en continu - Micro Électret MCP3008    ║
╚═══════════════════════════════════════════════════════════╝

🎤 Intervalle: 1 seconde(s)
🏢 Salle: 1
📊 Seuil bruit fort: 50.0 dB
💾 Stockage: Base de données

=== Configuration du système de capture audio ===

✓ Capteur BRUIT trouvé - ID: 1
✓ MCP3008 initialisé (SPI 0.0)
⏳ Calibration... (silence pendant 2 secondes)
✓ Calibration terminée - Valeur repos: 521

✓ Configuration terminée

───────────────────────────────────────────────────────────────
[10:30:15] Mesure #   1 | Niveau:  45.3 dB | Amplitude:   46 | ID: 12
[10:30:16] Mesure #   2 | Niveau:  52.8 dB | Amplitude:   54 | ID: 13
         ⚠ BRUIT_FORT détecté!
[10:30:17] Mesure #   3 | Niveau:  38.1 dB | Amplitude:   39 | ID: 14
...
```

#### Arrêter la capture

Appuyez sur **Ctrl+C** pour arrêter proprement.

### Configuration

#### Dans config.py

```python
# Configuration GPIO - Micro électret
SOUND_PIN = 18  # Pin GPIO (non utilisé avec MCP3008)
ADC_CHANNEL = 0  # Canal ADC pour le micro (0-7)
SPI_BUS = 0
SPI_DEVICE = 0
```

#### Dans capture_son_continu.py

**Intervalle de capture** :
```python
# Ligne 312
capture_system = CaptureSonContinu(db, ID_SALLE,
                                   intervalle=1,  # Secondes
                                   seuil_bruit_fort=50.0)  # dB
```

**Seuil de bruit fort** :
- Valeur par défaut : 50 dB
- Ajustez selon votre environnement
- Les valeurs sont calculées sur une échelle 0-100

---

## 📊 Fonctionnement technique

### Calibration

Au démarrage, le système :
1. Lit 20 échantillons sur 2 secondes
2. Calcule la valeur moyenne au repos
3. Utilise cette valeur comme référence

**Important** : Gardez le silence pendant la calibration !

### Mesure du son

Pour chaque mesure :
1. Lit 10 échantillons rapides (100ms total)
2. Calcule la moyenne, le min et le max
3. Détermine l'amplitude (max - min)
4. Convertit en niveau dB (échelle 0-100)

**Formule** :
```python
niveau_db = (amplitude / 10.23) * 10  # Échelle 0-100
```

### Données stockées

**Table Donnees** :
- `mesure` : Niveau sonore en dB (0-100)
- `photoBlob` : NULL pour les mesures de son
- `dateHeure` : Timestamp de la mesure
- `idCapteur` : ID du capteur BRUIT (1)
- `noSalle` : ID de la salle (1)

**Événements** :
- Type : `BRUIT_FORT`
- Créé quand : niveau > seuil (50 dB par défaut)
- Description : Niveau et amplitude

---

## 🔧 Comprendre les valeurs

### Valeur brute ADC

- **Range** : 0-1023 (10 bits)
- **Repos typique** : ~512 (milieu de la plage)
- **Variation** : ±100 selon le bruit ambiant

### Amplitude

- **Calcul** : max - min sur 10 échantillons
- **Faible** : < 30 (silence)
- **Moyen** : 30-60 (conversation)
- **Fort** : > 60 (bruit fort)

### Niveau dB

- **Échelle** : 0-100 (arbitraire, pas des vrais dB)
- **Silence** : < 30
- **Normal** : 30-50
- **Bruit fort** : > 50

---

## 📈 Statistiques

### Nombre de mesures par heure

Avec intervalle de 1 seconde :
- 60 mesures/minute
- 3 600 mesures/heure
- 86 400 mesures/jour

**Stockage** : ~8 bytes par mesure (FLOAT) = ~700 KB/jour

### Visualiser les données

```python
from db_connection import DatabaseConnection

db = DatabaseConnection(server, database, username, password)
db.connect()

# Dernières mesures
mesures = db.execute_query("""
    SELECT TOP 100
        d.dateHeure,
        d.mesure AS niveau_db
    FROM Donnees d
    JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
    WHERE c.type = N'BRUIT'
    ORDER BY d.dateHeure DESC
""")

for mesure in mesures:
    print(f"{mesure[0]}: {mesure[1]:.1f} dB")

db.disconnect()
```

### Statistiques par période

```python
# Niveau moyen par heure
stats = db.execute_query("""
    SELECT
        DATEPART(HOUR, dateHeure) AS heure,
        AVG(mesure) AS niveau_moyen,
        MAX(mesure) AS niveau_max,
        COUNT(*) AS nb_mesures
    FROM Donnees d
    JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
    WHERE c.type = N'BRUIT'
        AND CAST(dateHeure AS DATE) = CAST(GETDATE() AS DATE)
    GROUP BY DATEPART(HOUR, dateHeure)
    ORDER BY heure
""")
```

---

## 🚀 Exemples d'utilisation

### Surveillance 24/7

```bash
# Lancer en arrière-plan
nohup python capture_son_continu.py > logs_micro.txt 2>&1 &

# Voir les logs
tail -f logs_micro.txt

# Arrêter
pkill -f capture_son_continu
```

### Capture pendant 1 heure

```bash
# Avec timeout (3600s = 1h)
timeout 3600 python capture_son_continu.py
```

### Test rapide (10 mesures)

```bash
python -c "
from capture_son_continu import CaptureSonContinu
from db_connection import DatabaseConnection
from config import DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD, ID_SALLE
import time

db = DatabaseConnection(DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD)
if db.connect():
    capture = CaptureSonContinu(db, ID_SALLE)
    if capture.setup():
        for i in range(10):
            mesure = capture.mesurer_son()
            if mesure:
                capture.envoyer_mesure_bd(mesure)
            time.sleep(1)
    capture.cleanup()
    db.disconnect()
"
```

---

## ⚙️ Ajustements selon votre environnement

### Environnement bruyant (bureau, atelier)

```python
# Augmenter le seuil
capture_system = CaptureSonContinu(db, ID_SALLE,
                                   intervalle=1,
                                   seuil_bruit_fort=70.0)  # Plus élevé
```

### Environnement silencieux (bibliothèque)

```python
# Diminuer le seuil
capture_system = CaptureSonContinu(db, ID_SALLE,
                                   intervalle=1,
                                   seuil_bruit_fort=30.0)  # Plus bas
```

### Économie de stockage

```python
# Augmenter l'intervalle
capture_system = CaptureSonContinu(db, ID_SALLE,
                                   intervalle=5,  # Toutes les 5 secondes
                                   seuil_bruit_fort=50.0)
```

---

## 🐛 Dépannage

### Erreur "No module named 'spidev'"

```bash
source venv/bin/activate
pip install spidev
```

### Erreur "No such file or directory: '/dev/spidev0.0'"

Le SPI n'est pas activé :
```bash
sudo raspi-config
# Interface Options → SPI → Enable
sudo reboot
```

### Valeurs toujours à 0 ou 1023

- Vérifiez le branchement du micro au CH0 du MCP3008
- Vérifiez l'alimentation 3.3V du MCP3008
- Vérifiez que le micro électret a une alimentation

### Calibration échoue

- Assurez-vous qu'il y a du silence pendant 2 secondes
- Vérifiez que le micro est bien branché
- Testez avec [lecture-micro/testLecture.py](lecture-micro/testLecture.py)

---

## 📝 Scripts de test existants

Vos scripts dans [lecture-micro/](lecture-micro/) :

- **testLecture.py** : Test de lecture brute du MCP3008
- **testDtection.py** : Test de détection avec calibration
- **01.py** : Test GPIO

Vous pouvez les utiliser pour tester votre matériel avant d'utiliser le programme complet.
