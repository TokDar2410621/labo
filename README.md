# SalleSense - Système de Monitoring de Salles

Projet de monitoring de salles avec capteurs IoT (Raspberry Pi) et base de données SQL Server.

## Matériel requis

- Raspberry Pi (testé sur modèle avec GPIO)
- Micro électret (capteur de son)
- Pi Camera Module V2
- Connexion à un serveur SQL Server

## Installation

### 1. Installer les dépendances système

```bash
# Drivers ODBC pour SQL Server
sudo apt-get update
sudo apt-get install -y unixodbc unixodbc-dev

# Driver Microsoft ODBC (optionnel)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Bibliothèques pour la caméra
sudo apt-get install -y python3-picamera2
```

### 2. Configurer l'environnement Python

```bash
# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
pip install -r requirements.txt
```

### 3. Configurer la base de données

Exécutez les scripts SQL dans l'ordre (voir [CLAUDE.md](CLAUDE.md)):

```bash
sqlcmd -i Script_bd/ceration_bd.sql
sqlcmd -i Script_bd/creationTables.sql
sqlcmd -i Script_bd/contrainteSql.sql
sqlcmd -i Script_bd/InsertionSql.sql
sqlcmd -i Script_bd/ProcedureStocke.sql
sqlcmd -i Script_bd/Trigger.sql
```

### 4. Configuration

Modifiez [config.py](config.py) avec vos paramètres:

```python
DB_SERVER = "adresse_de_votre_serveur"
ID_SALLE = 1  # ID de votre salle
SOUND_PIN = 18  # Pin GPIO du micro
```

## Utilisation

### Module de connexion à la base de données

```python
from db_connection import DatabaseConnection

with DatabaseConnection("localhost") as db:
    users = db.execute_query("SELECT * FROM Utilisateur")
    for user in users:
        print(user)
```

### Monitoring des capteurs

```bash
# Activer le venv
source venv/bin/activate

# Lancer le monitoring (nécessite sudo pour GPIO)
sudo venv/bin/python sensor_monitor.py
```

Le script va:
- Mesurer le niveau sonore toutes les 5 secondes
- Capturer une photo toutes les 60 secondes
- Envoyer automatiquement les données vers la base de données
- Créer des événements pour les bruits forts

### Scripts GPIO existants

```bash
# LED control interactif
sudo python3 labo.py

# Monitoring bouton
sudo python3 boutton.py

# Système bouton/LED complet
sudo python3 proto-final.py
```

## Structure du projet

```
labo/
├── Script_bd/              # Scripts SQL
│   ├── ceration_bd.sql     # Création de la BD
│   ├── creationTables.sql  # Tables
│   ├── contrainteSql.sql   # Contraintes
│   └── ...
├── photos/                 # Photos capturées (créé automatiquement)
├── config.py              # Configuration centrale
├── db_connection.py       # Module de connexion BD
├── sensor_monitor.py      # Monitoring des capteurs
├── labo.py               # LED control
├── boutton.py            # Button monitoring
├── proto-final.py        # Button/LED system
└── requirements.txt      # Dépendances Python
```

## Architecture de la base de données

Voir [CLAUDE.md](CLAUDE.md) pour les détails complets.

Tables principales:
- **Utilisateur**: Comptes utilisateurs avec authentification sécurisée
- **Salle**: Salles avec capacité
- **Capteur**: Définition des capteurs (MOUVEMENT, BRUIT, CAMERA)
- **Donnees**: Mesures des capteurs
- **Evenement**: Événements déclenchés
- **Reservation**: Réservations de salles
- **Blacklist**: Utilisateurs bannis

## Notes importantes

- Les scripts GPIO nécessitent `sudo` pour accéder aux pins
- La caméra doit être activée dans `raspi-config`
- Le micro électret nécessite un ADC (MCP3008) pour les mesures analogiques
- Les photos sont sauvegardées localement dans `photos/`

## Troubleshooting

### Erreur `libodbc.so.2: cannot open shared object file`
Installez les drivers ODBC: `sudo apt-get install unixodbc unixodbc-dev`

### Erreur caméra `Failed to open camera`
Activez la caméra: `sudo raspi-config` > Interface Options > Camera

### Permission denied sur GPIO
Utilisez `sudo` ou ajoutez votre utilisateur au groupe gpio:
```bash
sudo usermod -a -G gpio $USER
```
