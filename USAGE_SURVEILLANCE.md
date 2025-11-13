## 🎬 Guide d'utilisation - Surveillance Intelligente avec Vidéo

## Concept

**Surveillance intelligente automatique** :
1. 🎤 Mesure du son en continu (toutes les secondes)
2. 🚨 Détection de bruit fort (> seuil)
3. 🎬 **Enregistrement automatique d'une vidéo de 10 secondes**
4. 💾 Stockage dans la base de données
5. 🔗 Lien entre l'événement sonore et la vidéo

---

## 📋 Programme principal : surveillance_intelligente.py

### Fonctionnement

```
┌─────────────────────────────────────────────────────┐
│  1. Mesure du son (micro électret + MCP3008)       │
│     ↓                                               │
│  2. Niveau > seuil ?                                │
│     ├─ NON → Continuer surveillance                 │
│     └─ OUI → Déclencher événement + vidéo           │
│           ↓                                         │
│        3. Créer événement BRUIT_FORT en BD          │
│           ↓                                         │
│        4. Lancer enregistrement vidéo (10s)         │
│           ↓                                         │
│        5. Sauvegarder vidéo en BD                   │
│           ↓                                         │
│        6. Créer événement CAPTURE (lien avec BRUIT) │
└─────────────────────────────────────────────────────┘
```

### Caractéristiques

- ✅ Surveillance audio continue (1 mesure/seconde)
- ✅ Enregistrement vidéo **automatique** lors de bruit fort
- ✅ Vidéo de 10 secondes (configurable)
- ✅ Enregistrement en **thread séparé** (ne bloque pas la surveillance)
- ✅ Format H.264 (720p, 1280x720)
- ✅ Stockage direct en BD (VARBINARY)
- ✅ Lien entre événement sonore et vidéo

---

## 🚀 Installation et configuration

### Prérequis

```bash
source venv/bin/activate
pip install pyodbc picamera2 RPi.GPIO spidev
```

### Activer SPI et Caméra

```bash
sudo raspi-config
```

1. `Interface Options` → `SPI` → `Enable`
2. `Interface Options` → `Camera` → `Enable`
3. `sudo reboot`

### Configuration

Dans [config.py](config.py) :
```python
ID_SALLE = 1  # ID de la salle
```

Dans [surveillance_intelligente.py](surveillance_intelligente.py:312) :
```python
surveillance = SurveillanceIntelligente(
    db, ID_SALLE,
    intervalle=1,          # Secondes entre mesures
    seuil_bruit_fort=50.0, # Seuil déclenchement (dB)
    duree_video=10         # Durée vidéo (secondes)
)
```

---

## 🎯 Utilisation

### Lancer la surveillance

```bash
source venv/bin/activate

# Avec sudo pour accès caméra
sudo venv/bin/python surveillance_intelligente.py
```

### Sortie attendue

```
╔═══════════════════════════════════════════════════════════╗
║         Surveillance Intelligente - SalleSense           ║
╚═══════════════════════════════════════════════════════════╝

🎤 Intervalle mesures: 1s
🏢 Salle: 1
📊 Seuil déclenchement: 50.0 dB
🎬 Durée vidéo: 10s
💾 Stockage: Base de données

=== Configuration du système de surveillance intelligente ===

✓ Capteur BRUIT trouvé - ID: 1
✓ Capteur CAMERA trouvé - ID: 2
✓ MCP3008 initialisé (SPI 0.0)
⏳ Calibration audio... (2 secondes)
✓ Calibration audio - Valeur repos: 521
✓ Pi Camera initialisée (720p)

✓ Configuration terminée

───────────────────────────────────────────────────────────────
[10:30:15] Son #   1 | Niveau:  42.3 dB | Amplitude:   43 | ID: 100
[10:30:16] Son #   2 | Niveau:  38.1 dB | Amplitude:   39 | ID: 101
[10:30:17] Son #   3 | Niveau:  65.8 dB | Amplitude:   67 | ID: 102
         ⚠ BRUIT_FORT détecté! (Event ID: 50)

         🎬 ENREGISTREMENT VIDÉO DÉCLENCHÉ!
         📹 Durée: 10s | Déclencheur: 65.8 dB
         ⏱ 8s restantes...
         ⏱ 6s restantes...
         ⏱ 4s restantes...
         ⏱ 2s restantes...
         ✓ Vidéo capturée (2.4 MB)
         ✓ Vidéo enregistrée en BD - ID: 103

[10:30:28] Son #   4 | Niveau:  40.2 dB | Amplitude:   41 | ID: 104
[10:30:29] Son #   5 | Niveau:  45.6 dB | Amplitude:   47 | ID: 105
...
```

### Arrêter

**Ctrl+C** pour arrêt propre avec statistiques :

```
📊 Statistiques de session:
   • Mesures audio: 125
   • Vidéos enregistrées: 3

✓ Arrêt demandé - Programme terminé
```

---

## 📹 Visualiser les vidéos

### Lancer le visualiseur

```bash
python visualiser_videos.py
```

### Menu

```
╔═══════════════════════════════════════════════════════════╗
║        Visualiseur de Vidéos - SalleSense                ║
╚═══════════════════════════════════════════════════════════╝

1. Lister toutes les vidéos
2. Extraire une vidéo (par ID)
3. Extraire toutes les vidéos
4. Afficher historique des événements avec vidéos
5. Quitter
```

### Option 1 : Lister les vidéos

```
=== Vidéos stockées dans la base de données ===

Total: 3 vidéo(s)

──────────────────────────────────────────────────────────────────────────────────────
   ID | Date/Heure          | Capteur         | Salle    |     Taille | Description
──────────────────────────────────────────────────────────────────────────────────────
  103 | 2025-11-13 10:30:27 | PICAM-V2-1      | A-101    |    2.40 MB | Vidéo 10s - Déclenchée par BRUIT_FOR...
  108 | 2025-11-13 10:35:15 | PICAM-V2-1      | A-101    |    2.38 MB | Vidéo 10s - Déclenchée par BRUIT_FOR...
  115 | 2025-11-13 10:42:30 | PICAM-V2-1      | A-101    |    2.42 MB | Vidéo 10s - Déclenchée par BRUIT_FOR...
──────────────────────────────────────────────────────────────────────────────────────
```

### Option 2 : Extraire une vidéo

```
Votre choix: 2

ID de la vidéo à extraire: 103

✓ Vidéo extraite: videos_extraites/video_103_20251113_103027.h264 (2.40 MB)

📹 Pour lire la vidéo H.264:
   vlc videos_extraites/video_103_20251113_103027.h264
   # ou
   ffplay videos_extraites/video_103_20251113_103027.h264

🔄 Pour convertir en MP4:
   ffmpeg -i videos_extraites/video_103_20251113_103027.h264 -c copy video_103.mp4
```

### Option 4 : Historique avec liens

```
=== Historique des événements avec vidéos ===

Total: 3 événement(s)

────────────────────────────────────────────────────────────────────────────────────────────────
🔊 Event #50 | 2025-11-13 10:30:17.123456
   Niveau sonore élevé: 65.8 dB (amplitude: 67)
   🎬 Vidéo associée: ID 103 (2.40 MB)
      Pour extraire: python visualiser_videos.py (option 2, ID 103)

🔊 Event #55 | 2025-11-13 10:35:10.234567
   Niveau sonore élevé: 72.3 dB (amplitude: 74)
   🎬 Vidéo associée: ID 108 (2.38 MB)
      Pour extraire: python visualiser_videos.py (option 2, ID 108)

🔊 Event #60 | 2025-11-13 10:42:25.345678
   Niveau sonore élevé: 68.9 dB (amplitude: 70)
   🎬 Vidéo associée: ID 115 (2.42 MB)
      Pour extraire: python visualiser_videos.py (option 2, ID 115)

────────────────────────────────────────────────────────────────────────────────────────────────
```

---

## 🎥 Lire les vidéos

### Avec VLC

```bash
cd videos_extraites
vlc video_103_20251113_103027.h264
```

### Avec ffplay

```bash
ffplay videos_extraites/video_103_20251113_103027.h264
```

### Convertir en MP4

```bash
# Une vidéo
ffmpeg -i videos_extraites/video_103.h264 -c copy video_103.mp4

# Toutes les vidéos
cd videos_extraites
for f in *.h264; do
    ffmpeg -i "$f" -c copy "${f%.h264}.mp4"
done
```

---

## 📊 Structure de la base de données

### Table Donnees

Contient à la fois les **mesures audio** et les **vidéos** :

**Mesure audio** :
```sql
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photoBlob, noSalle)
VALUES ('2025-11-13 10:30:17', 1, 65.8, NULL, 1)
-- idCapteur=1 (BRUIT), mesure=65.8 dB, photoBlob=NULL
```

**Vidéo** :
```sql
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photoBlob, noSalle)
VALUES ('2025-11-13 10:30:27', 2, NULL, <video_bytes>, 1)
-- idCapteur=2 (CAMERA), mesure=NULL, photoBlob=vidéo H.264
```

### Table Evenement

**Événement BRUIT_FORT** (lié à la mesure audio) :
```sql
INSERT INTO Evenement (type, idDonnee, description)
VALUES ('BRUIT_FORT', 102, 'Niveau sonore élevé: 65.8 dB (amplitude: 67)')
-- idDonnee=102 pointe vers la mesure audio
```

**Événement CAPTURE** (lié à la vidéo) :
```sql
INSERT INTO Evenement (type, idDonnee, description)
VALUES ('CAPTURE', 103, 'Vidéo 10s - Déclenchée par BRUIT_FORT (65.8 dB) - Event ID: 50')
-- idDonnee=103 pointe vers la vidéo
-- La description contient "Event ID: 50" pour faire le lien avec BRUIT_FORT
```

### Lien entre événements

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Evenement #50  │────→│  Donnees #102    │     │  Evenement      │
│  BRUIT_FORT     │     │  (mesure audio)  │     │  CAPTURE        │
│                 │     └──────────────────┘     │  "Event ID: 50" │
└─────────────────┘                              └────────┬────────┘
                                                          │
                                                          ↓
                                                 ┌──────────────────┐
                                                 │  Donnees #103    │
                                                 │  (vidéo H.264)   │
                                                 └──────────────────┘
```

---

## ⚙️ Paramètres ajustables

### Fréquence des mesures

```python
intervalle=1  # 1 mesure par seconde
intervalle=2  # 1 mesure toutes les 2 secondes
```

**Impact** :
- Intervalle court = détection plus rapide, plus de données
- Intervalle long = moins de stockage, risque de manquer des événements

### Seuil de déclenchement

```python
seuil_bruit_fort=50.0  # Standard
seuil_bruit_fort=30.0  # Plus sensible (bibliothèque)
seuil_bruit_fort=70.0  # Moins sensible (atelier bruyant)
```

### Durée des vidéos

```python
duree_video=10  # 10 secondes (~2-3 MB)
duree_video=5   # 5 secondes (~1-1.5 MB)
duree_video=30  # 30 secondes (~6-8 MB)
```

**Important** : Plus la durée est longue, plus le stockage augmente !

---

## 📈 Stockage et performance

### Taille des données

**Audio** : ~8 bytes par mesure
- 1 mesure/seconde = 60/min = 3600/heure
- Stockage: ~28 KB/heure, ~700 KB/jour

**Vidéo** : ~2.4 MB par vidéo de 10s (720p H.264)
- Dépend du nombre d'événements BRUIT_FORT

### Exemple sur 24h

Scénario : 10 bruits forts par jour
- Audio: 700 KB
- Vidéos: 10 × 2.4 MB = 24 MB
- **Total: ~25 MB/jour**

---

## 🚀 Automatisation

### Lancer au démarrage (systemd)

Créer `/etc/systemd/system/sallesense-surveillance.service` :

```ini
[Unit]
Description=SalleSense Surveillance Intelligente
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/etu24/labo
ExecStart=/home/etu24/labo/venv/bin/python /home/etu24/labo/surveillance_intelligente.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activer :
```bash
sudo systemctl enable sallesense-surveillance.service
sudo systemctl start sallesense-surveillance.service
sudo systemctl status sallesense-surveillance.service
```

### Logs

```bash
# Voir les logs en temps réel
sudo journalctl -u sallesense-surveillance.service -f

# Voir les dernières 100 lignes
sudo journalctl -u sallesense-surveillance.service -n 100
```

---

## 🐛 Dépannage

### Problème: Vidéos de 0 bytes ou très petites

**Cause**: Caméra non détectée ou picamera2 en mode simulation

**Solution**:
```bash
# Vérifier que la caméra est détectée
vcgencmd get_camera

# Devrait afficher: supported=1 detected=1

# Si pas détecté, vérifier le câble et activer dans raspi-config
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

### Problème: "Permission denied" pour la caméra

**Solution**: Utiliser `sudo`
```bash
sudo venv/bin/python surveillance_intelligente.py
```

### Problème: Trop de vidéos enregistrées

**Cause**: Seuil trop bas pour l'environnement

**Solution**: Augmenter le seuil
```python
seuil_bruit_fort=70.0  # Au lieu de 50.0
```

### Problème: Aucune vidéo enregistrée

**Cause**: Seuil trop élevé

**Solution**: Diminuer le seuil ou faire du bruit près du micro
```python
seuil_bruit_fort=30.0  # Au lieu de 50.0
```

---

## 📝 Requêtes SQL utiles

### Compter les événements par type

```sql
SELECT type, COUNT(*) AS nombre
FROM Evenement
GROUP BY type
ORDER BY nombre DESC
```

### Vidéos avec leur événement déclencheur

```sql
SELECT
    e_capture.idEvenement_PK AS id_capture,
    d_video.idDonnee_PK AS id_video,
    d_video.dateHeure AS date_video,
    e_bruit.idEvenement_PK AS id_bruit,
    d_son.mesure AS niveau_db,
    DATALENGTH(d_video.photoBlob) / 1024.0 / 1024.0 AS taille_mb
FROM Evenement e_capture
JOIN Donnees d_video ON e_capture.idDonnee = d_video.idDonnee_PK
CROSS APPLY (
    SELECT CAST(value AS INT) AS event_id
    FROM STRING_SPLIT(e_capture.description, 'Event ID: ')
    WHERE value LIKE '%[0-9]%'
) AS extracted
JOIN Evenement e_bruit ON e_bruit.idEvenement_PK = extracted.event_id
JOIN Donnees d_son ON e_bruit.idDonnee = d_son.idDonnee_PK
WHERE e_capture.type = 'CAPTURE'
ORDER BY d_video.dateHeure DESC
```

---

## 🎯 Cas d'usage

### Surveillance de salle de classe
- Détecter les moments de forte activité
- Enregistrer pour analyse pédagogique
- Durée recommandée: 5-10s

### Sécurité d'un local
- Détecter les intrusions bruyantes
- Enregistrement automatique comme preuve
- Durée recommandée: 15-30s

### Monitoring d'atelier
- Détecter les incidents (chutes, alarmes)
- Documentation automatique
- Durée recommandée: 10-20s

### Laboratoire silencieux
- Détection ultra-sensible (seuil bas)
- Enregistrement de toute anomalie
- Durée recommandée: 5-10s
