# Guide d'utilisation - Capture de photos avec Pi Camera V2

## 📷 Programme principal : capture_photos_continu.py

Ce programme capture des photos **toutes les 5 secondes** avec la Pi Camera V2 et les envoie vers la base de données.

### Caractéristiques

- ✓ Capture automatique toutes les 5 secondes (configurable)
- ✓ Stockage direct en base de données (VARBINARY)
- ✓ Résolution Full HD (1920x1080)
- ✓ Création automatique d'événements
- ✓ Affichage en temps réel des captures
- ✓ Arrêt propre avec Ctrl+C

### Installation

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer picamera2 (si pas déjà fait)
sudo apt-get install -y python3-picamera2

# OU via pip (si disponible)
pip install picamera2
```

### Activation de la caméra

Si c'est la première fois que vous utilisez la caméra :

```bash
sudo raspi-config
```

Puis : `Interface Options` → `Camera` → `Enable`

Redémarrer après activation :
```bash
sudo reboot
```

### Utilisation

#### Lancer la capture continue

```bash
source venv/bin/activate

# Avec sudo pour accès à la caméra
sudo venv/bin/python capture_photos_continu.py
```

**Sortie attendue** :
```
╔═══════════════════════════════════════════════════════════╗
║      Capture de photos en continu - Pi Camera V2         ║
╚═══════════════════════════════════════════════════════════╝

📷 Intervalle: 5 secondes
🏢 Salle: 1
💾 Stockage: Base de données (VARBINARY)

Appuyez sur Ctrl+C pour arrêter

───────────────────────────────────────────────────────────
[10:30:15] Photo #1 envoyée (245.3 KB) - ID: 12
[10:30:20] Photo #2 envoyée (247.8 KB) - ID: 13
[10:30:25] Photo #3 envoyée (244.1 KB) - ID: 14
...
```

#### Arrêter la capture

Appuyez sur **Ctrl+C** pour arrêter proprement.

### Configuration

Vous pouvez modifier l'intervalle de capture dans [config.py](config.py) :

```python
# Configuration photos
INTERVALLE_PHOTO = 5  # Secondes entre chaque capture
```

Ou directement dans le code [capture_photos_continu.py](capture_photos_continu.py:312) :

```python
capture_system = CapturePhotosContinu(db, ID_SALLE, intervalle=5)  # Changer 5 par la valeur désirée
```

---

## 👁️ Visualiseur de photos : visualiser_photos.py

Ce programme permet de lister et extraire les photos stockées dans la base de données.

### Utilisation

```bash
source venv/bin/activate
python visualiser_photos.py
```

### Menu interactif

```
╔═══════════════════════════════════════════════════════════╗
║          Visualiseur de Photos - SalleSense              ║
╚═══════════════════════════════════════════════════════════╝

1. Lister toutes les photos
2. Extraire une photo (par ID)
3. Extraire toutes les photos
4. Quitter
```

#### Option 1 : Lister toutes les photos

Affiche toutes les photos avec leur ID, date, taille :

```
=== Photos stockées dans la base de données ===

Total: 15 photo(s)

────────────────────────────────────────────────────────────────────────────────
ID:   15 | 2025-11-06 10:35:45.123456 | PICAM-V2-1      | Salle A-101  |  245.3 KB
ID:   14 | 2025-11-06 10:35:40.123456 | PICAM-V2-1      | Salle A-101  |  247.8 KB
...
```

#### Option 2 : Extraire une photo

Extrait une photo spécifique par son ID :

```bash
Votre choix: 2
ID de la photo à extraire: 15

✓ Photo extraite: photos_extraites/photo_15_20251106_103545.jpg (245.3 KB)
```

#### Option 3 : Extraire toutes les photos

Extrait toutes les photos dans le dossier `photos_extraites/` :

```
=== Extraction de toutes les photos ===

Extraction de 15 photo(s)...

  ✓ photo_15_20251106_103545.jpg (245.3 KB)
  ✓ photo_14_20251106_103540.jpg (247.8 KB)
  ...

✓ 15 photo(s) extraite(s) dans le dossier 'photos_extraites/'
```

---

## 🔧 Fonctionnement technique

### Structure de stockage

Les photos sont stockées dans la table `Donnees` :

```sql
CREATE TABLE Donnees (
    idDonnee_PK      INT IDENTITY(1,1)  PRIMARY KEY,
    dateHeure        DATETIME2          NOT NULL,
    idCapteur        INT                NOT NULL,      -- ID du capteur caméra
    mesure           FLOAT              NULL,          -- NULL pour les photos
    photoBlob        VARBINARY(MAX)     NULL,          -- Données binaires de la photo
    noSalle          INT                NOT NULL       -- ID de la salle
)
```

### Événements créés

À chaque capture, un événement est créé dans la table `Evenement` :

```sql
INSERT INTO Evenement (type, idDonnee, description)
VALUES ('CAPTURE', id_donnee, 'Photo capturée à HH:MM:SS')
```

### Format des photos

- **Format** : JPEG
- **Résolution** : 1920x1080 (Full HD)
- **Taille moyenne** : 200-300 KB par photo
- **Stockage** : VARBINARY(MAX) dans SQL Server

---

## 📊 Statistiques et requêtes

### Nombre de photos par jour

```python
from db_connection import DatabaseConnection

db = DatabaseConnection(server, database, username, password)
db.connect()

stats = db.execute_query("""
    SELECT
        CAST(dateHeure AS DATE) AS jour,
        COUNT(*) AS nb_photos,
        SUM(DATALENGTH(photoBlob)) / 1024.0 / 1024.0 AS taille_mb
    FROM Donnees
    WHERE photoBlob IS NOT NULL
    GROUP BY CAST(dateHeure AS DATE)
    ORDER BY jour DESC
""")

for stat in stats:
    print(f"{stat[0]}: {stat[1]} photos ({stat[2]:.2f} MB)")

db.disconnect()
```

### Photos par salle

```python
photos_salle = db.execute_query("""
    SELECT
        s.numero AS salle,
        COUNT(*) AS nb_photos
    FROM Donnees d
    JOIN Salle s ON d.noSalle = s.idSalle_PK
    WHERE d.photoBlob IS NOT NULL
    GROUP BY s.numero
""")
```

---

## ⚠️ Notes importantes

1. **Stockage** : Les photos sont stockées dans la base de données. Avec 1 photo toutes les 5 secondes, cela représente :
   - 12 photos/minute
   - 720 photos/heure
   - ~17 000 photos/jour
   - Environ **5 GB/jour** de stockage

2. **Performance** : Pour un stockage long terme, considérez :
   - Augmenter l'intervalle (ex: 10-30 secondes)
   - Réduire la résolution
   - Archiver/supprimer les vieilles photos

3. **Permissions** : Le script nécessite `sudo` pour accéder à la caméra

4. **Mode simulation** : Si picamera2 n'est pas disponible, le script fonctionne en mode simulation avec des données factices

---

## 🚀 Exemples d'utilisation

### Surveillance 24/7

```bash
# Lancer en arrière-plan
sudo venv/bin/python capture_photos_continu.py > logs_camera.txt 2>&1 &

# Voir les logs
tail -f logs_camera.txt

# Arrêter
pkill -f capture_photos_continu
```

### Capture pendant 1 heure

```bash
# Avec timeout (3600s = 1h)
timeout 3600 sudo venv/bin/python capture_photos_continu.py
```

### Automatisation au démarrage

Créer un service systemd : `/etc/systemd/system/sallesense-camera.service`

```ini
[Unit]
Description=SalleSense Camera Capture
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/etu24/labo
ExecStart=/home/etu24/labo/venv/bin/python /home/etu24/labo/capture_photos_continu.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Puis :
```bash
sudo systemctl enable sallesense-camera.service
sudo systemctl start sallesense-camera.service
sudo systemctl status sallesense-camera.service
```
