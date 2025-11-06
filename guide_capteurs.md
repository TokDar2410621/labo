# Guide des Capteurs - SalleSense

## Types de données selon vos capteurs

### 1. Micro Électret (Capteur de BRUIT)

**Type de capteur**: `BRUIT`

**Données envoyées**:
- `mesure`: Niveau sonore (FLOAT) - peut être en dB ou valeur brute
- `photo`: NULL
- `dateHeure`: Timestamp automatique
- `noSalle`: ID de la salle

**Exemple**:
```python
# Mesure de 52.3 dB dans la salle 1
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
VALUES ('2025-11-06 10:30:00', 2, 52.3, NULL, 1)
```

**Événements déclenchés**:
- `BRUIT_FORT` - Quand le niveau dépasse le seuil (70 dB par défaut)

---

### 2. Pi Camera Module V2 (Capteur CAMERA)

**Type de capteur**: `CAMERA`

**Données envoyées**:
- `mesure`: NULL
- `photo`: Chemin vers la photo (NVARCHAR(255)) - ex: "photos/salle1_20251106_103000.jpg"
- `dateHeure`: Timestamp automatique
- `noSalle`: ID de la salle

**Exemple**:
```python
# Photo capturée dans la salle 1
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
VALUES ('2025-11-06 10:30:00', 3, NULL, 'photos/a101_1.jpg', 1)
```

**Événements déclenchés**:
- `CAPTURE` - À chaque photo prise

---

## Types d'événements possibles

Basé sur les exemples dans la BD:

| Type | Description | Cas d'usage |
|------|-------------|-------------|
| `ENTREE` | Présence détectée | Quand mouvement détecté (si vous ajoutez un capteur PIR) |
| `SORTIE` | Fin de présence | Quand plus de mouvement |
| `BRUIT_FORT` | Niveau sonore élevé | Quand micro > seuil |
| `CAPTURE` | Photo enregistrée | À chaque capture de la caméra |

---

## Structure de la table Donnees

```sql
CREATE TABLE Donnees (
    idDonnee_PK      INT IDENTITY(1,1)  PRIMARY KEY,
    dateHeure        DATETIME2          NOT NULL,     -- Timestamp
    idCapteur        INT                NOT NULL,     -- ID du capteur
    mesure           FLOAT              NULL,         -- Valeur numérique (son, temp, etc.)
    photo            NVARCHAR(255)      NULL,         -- Chemin de la photo
    noSalle          INT                NOT NULL      -- ID de la salle
)
```

**Important**:
- `mesure` et `photo` sont NULL selon le type de capteur
- Micro → `mesure` rempli, `photo` NULL
- Caméra → `photo` rempli, `mesure` NULL

---

## Structure de la table Evenement

```sql
CREATE TABLE Evenement (
    idEvenement_PK   INT IDENTITY(1,1)  PRIMARY KEY,
    type             NVARCHAR(60)       NOT NULL,     -- Type d'événement
    idDonnee         INT                NOT NULL,     -- Lié à une donnée
    description      NVARCHAR(MAX)      NULL          -- Description détaillée
)
```

---

## Exemple complet d'utilisation

### Initialisation (à faire une fois)

```sql
-- Créer la salle
INSERT INTO Salle (numero, capaciteMaximale) VALUES ('A-101', 20);

-- Créer les capteurs
INSERT INTO Capteur (nom, type) VALUES ('MIC-ELECTRET-1', 'BRUIT');
INSERT INTO Capteur (nom, type) VALUES ('PICAM-V2-1', 'CAMERA');
```

### Envoi de données - Micro

```python
from db_connection import DatabaseConnection
from datetime import datetime

db = DatabaseConnection(server, database, username, password)
db.connect()

# Mesure de bruit
niveau_sonore = 65.5
db.execute_non_query(
    """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
       VALUES (?, ?, ?, NULL, ?)""",
    (datetime.now(), 1, niveau_sonore, 1)  # capteur 1, salle 1
)

# Si bruit fort, créer un événement
if niveau_sonore > 70:
    id_donnee = db.execute_query("SELECT @@IDENTITY")[0][0]
    db.execute_non_query(
        """INSERT INTO Evenement (type, idDonnee, description)
           VALUES (?, ?, ?)""",
        ('BRUIT_FORT', id_donnee, f'Niveau sonore: {niveau_sonore} dB')
    )
```

### Envoi de données - Caméra

```python
from picamera2 import Picamera2
import os

# Capturer la photo
camera = Picamera2()
camera.start()
photo_path = "photos/salle1_20251106.jpg"
camera.capture_file(photo_path)
camera.stop()

# Enregistrer dans la BD
db.execute_non_query(
    """INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
       VALUES (?, ?, NULL, ?, ?)""",
    (datetime.now(), 2, photo_path, 1)  # capteur 2, salle 1
)

# Créer un événement
id_donnee = db.execute_query("SELECT @@IDENTITY")[0][0]
db.execute_non_query(
    """INSERT INTO Evenement (type, idDonnee, description)
       VALUES (?, ?, ?)""",
    ('CAPTURE', id_donnee, f'Photo: {photo_path}')
)
```

---

## Récupération des données

### Dernières mesures de bruit

```python
mesures = db.execute_query("""
    SELECT d.dateHeure, d.mesure, s.numero, c.nom
    FROM Donnees d
    JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
    JOIN Salle s ON d.noSalle = s.idSalle_PK
    WHERE c.type = 'BRUIT'
    ORDER BY d.dateHeure DESC
""")
```

### Dernières photos

```python
photos = db.execute_query("""
    SELECT d.dateHeure, d.photo, s.numero
    FROM Donnees d
    JOIN Capteur c ON d.idCapteur = c.idCapteur_PK
    JOIN Salle s ON d.noSalle = s.idSalle_PK
    WHERE c.type = 'CAMERA'
    ORDER BY d.dateHeure DESC
""")
```

### Événements récents

```python
events = db.execute_query("""
    SELECT e.type, e.description, d.dateHeure, s.numero
    FROM Evenement e
    JOIN Donnees d ON e.idDonnee = d.idDonnee_PK
    JOIN Salle s ON d.noSalle = s.idSalle_PK
    ORDER BY d.dateHeure DESC
""")
```
