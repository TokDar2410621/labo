# Guide d'utilisation - Interface Graphique SalleSense

## 🖥️ Interface Tkinter Moderne avec authentification sécurisée

L'interface graphique permet de :
- ✅ Se connecter avec la procédure stockée `usp_Utilisateur_Login`
- ✅ Visualiser les données en temps réel avec design moderne
- ✅ Consulter l'historique des mesures
- ✅ Afficher les statistiques
- ✨ Interface moderne avec couleurs, cartes et animations

---

## 🚀 Lancement

```bash
source venv/bin/activate
python lancer_interface.py
```

Ou directement :
```bash
source venv/bin/activate
python interface_connexion.py
```

---

## 🔐 Écran de Connexion

### Champs requis

**Email** : L'email de votre compte utilisateur (ex: `tokamdaruis@gmail.com`)
**Mot de passe** : Votre mot de passe

### Fonctionnement

1. L'interface se connecte d'abord au serveur SQL avec les credentials système (prog3e09/colonne42)
2. Elle utilise ensuite la procédure stockée `dbo.usp_Utilisateur_Login` pour authentifier l'utilisateur
3. Si l'authentification réussit, l'interface principale s'ouvre

### Procédure stockée utilisée

```sql
EXEC dbo.usp_Utilisateur_Login
    @Courriel = 'votre_email@example.com',
    @MotDePasse = 'votre_mot_de_passe',
    @UserId OUTPUT;
```

- Retourne l'ID utilisateur si succès
- Retourne -1 si échec (email ou mot de passe incorrect)
- Utilise SHA2_256 avec salt pour la sécurité

---

## 📊 Interface Principale

### Onglet 1 : Temps Réel

**Indicateurs en direct** :
- 🎤 **Niveau Sonore**
  - Valeur en dB
  - Barre de progression
  - Couleur selon le niveau (vert < 50, orange < 70, rouge ≥ 70)
  - Heure de la dernière mesure

- 📹 **Médias**
  - Nombre total de photos/vidéos
  - Dernière capture

- ⚡ **Événements Récents**
  - Liste des 20 derniers événements
  - Type, date et description

**Rafraîchissement** :
- Automatique toutes les 2 secondes (configurable)
- Bouton "🔄 Rafraîchir" pour forcer la mise à jour
- Case à cocher pour activer/désactiver le rafraîchissement auto

### Onglet 2 : Historique

**Filtres** :
- TOUS : Toutes les données
- BRUIT : Mesures audio uniquement
- CAMERA : Photos/vidéos uniquement

**Colonnes affichées** :
- ID, Date/Heure, Capteur, Type, Mesure, Salle

**Actions** :
- Bouton "Charger" pour afficher les 100 dernières données
- Tri par date décroissante

### Onglet 3 : Statistiques

**Informations affichées** :
- Nombre total de mesures
- Répartition par type de capteur
- Nombre d'événements par type
- Niveau sonore : moyenne, maximum, minimum

**Actions** :
- Bouton "Actualiser les statistiques" pour recharger

---

## 📋 Menu

### Menu Fichier

- **Déconnexion** : Se déconnecter et retourner à l'écran de connexion
- **Quitter** : Fermer l'application

### Menu Affichage

- **Rafraîchissement auto** : Cocher/décocher pour activer/désactiver

---

## 🔧 Configuration

### Fichier `db_config.json`

Les dernières informations de connexion sont sauvegardées :
```json
{
  "server": "DICJWIN01.cegepjonquiere.ca",
  "database": "Prog3A25_bdSalleSense",
  "db_username": "prog3e09",
  "email": "tokamdaruis@gmail.com"
}
```

**Note** : Les mots de passe ne sont jamais sauvegardés pour des raisons de sécurité.

---

## 👥 Créer un nouvel utilisateur

Pour créer un nouvel utilisateur dans la base de données :

```python
from db_connection import DatabaseConnection

db = DatabaseConnection("DICJWIN01.cegepjonquiere.ca",
                       "Prog3A25_bdSalleSense",
                       "prog3e09", "colonne42")

if db.connect():
    # Créer un utilisateur
    user_id = db.create_user(
        pseudo="nouveau_user",
        courriel="nouveau@example.com",
        mot_de_passe="mon_mot_de_passe"
    )

    if user_id > 0:
        print(f"✓ Utilisateur créé avec l'ID: {user_id}")
    else:
        print("✗ Erreur: Email déjà existant")

    db.disconnect()
```

Ou via SQL :
```sql
DECLARE @UserId INT;

EXEC dbo.usp_Utilisateur_Create
    @Pseudo = 'nouveau_user',
    @Courriel = 'nouveau@example.com',
    @MotDePasse = 'mon_mot_de_passe',
    @UserId = @UserId OUTPUT;

SELECT @UserId AS UserId;
-- Retourne l'ID si succès, -1 si email déjà existant
```

---

## 🎨 Personnalisation

### Modifier l'intervalle de rafraîchissement

Dans `interface_principale.py` ligne 22 :
```python
self.refresh_interval = 2000  # ms (2 secondes)
```

Valeurs suggérées :
- 1000 ms (1 seconde) : Très réactif
- 2000 ms (2 secondes) : Équilibré (défaut)
- 5000 ms (5 secondes) : Économise les ressources

### Modifier le nombre d'événements affichés

Dans `interface_principale.py` ligne 269 :
```python
SELECT TOP 20  -- Changer 20 par le nombre désiré
```

---

## 🐛 Dépannage

### Erreur "No module named 'tkinter'"

Tkinter devrait être installé par défaut. Si ce n'est pas le cas :
```bash
sudo apt-get install python3-tk
```

### Erreur de connexion au serveur

Vérifiez :
1. Les credentials SQL système dans le code (prog3e09/colonne42)
2. La connexion réseau au serveur DICJWIN01.cegepjonquiere.ca
3. Le port SQL Server (1433 par défaut)

### Erreur "Email ou mot de passe incorrect"

Vérifiez :
1. L'email existe bien dans la table `Utilisateur`
2. Le mot de passe correspond (sensible à la casse)
3. L'utilisateur a été créé avec `usp_Utilisateur_Create` (utilise le hash)

### Interface ne se rafraîchit pas

1. Vérifiez que le rafraîchissement auto est activé (Menu Affichage)
2. Vérifiez la connexion à la BD
3. Cliquez sur "🔄 Rafraîchir" manuellement

---

## 📸 Captures d'écran

### Écran de connexion

```
┌─────────────────────────────────────────────┐
│        🔐 Connexion SalleSense              │
│─────────────────────────────────────────────│
│                                             │
│  Configuration Serveur                      │
│                                             │
│  Email:         [tokamdaruis@gmail.com]     │
│  Mot de passe:  [****************]          │
│                                             │
│             [  Se Connecter  ]              │
│                                             │
│  Note: La connexion utilise la procédure    │
│  stockée usp_Utilisateur_Login              │
└─────────────────────────────────────────────┘
```

### Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│ Fichier  Affichage                                           │
│──────────────────────────────────────────────────────────────│
│ 👤 Connecté: leroi     [🔄 Rafraîchir]  ⏰ 10:30:15         │
│──────────────────────────────────────────────────────────────│
│ [📊 Temps Réel] [📜 Historique] [📈 Statistiques]           │
│                                                              │
│  Dernières Mesures                                           │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  🎤 Niveau Sonore│  │   📹 Média       │                 │
│  │     65.8 dB      │  │  3 média(s)      │                 │
│  │  [██████████░░░] │  │  10:29:45        │                 │
│  │  10:30:15        │  │                  │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                                              │
│  ⚡ Événements Récents                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Type        │ Date               │ Description         │ │
│  ├────────────────────────────────────────────────────────│ │
│  │ BRUIT_FORT  │ 2025-11-13 10:30  │ Niveau: 65.8 dB    │ │
│  │ CAPTURE     │ 2025-11-13 10:29  │ Vidéo 10s          │ │
│  │ BRUIT_FORT  │ 2025-11-13 10:25  │ Niveau: 72.3 dB    │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔒 Sécurité

### Authentification

- ✅ Les mots de passe sont hashés avec SHA2_256 + salt
- ✅ Aucun mot de passe n'est stocké en clair
- ✅ La procédure stockée gère l'authentification côté serveur
- ✅ Les mots de passe ne sont jamais sauvegardés dans les fichiers de config

### Recommandations

1. Changez régulièrement vos mots de passe
2. Utilisez des mots de passe forts (min 8 caractères, majuscules, chiffres)
3. Ne partagez pas vos identifiants
4. Déconnectez-vous après utilisation

---

## 🎨 Interface Moderne - Nouvelles Fonctionnalités

### Design
- ✨ **Palette de couleurs moderne**: Bleu primaire (#2563eb), violet secondaire (#8b5cf6)
- 🎴 **Cartes avec ombres**: Effet de profondeur pour chaque section
- 🖌️ **Header moderne**: Barre supérieure avec logo, user info et boutons stylisés
- 📊 **Barre de progression animée**: Visualisation du niveau sonore avec couleurs dynamiques
- 🎯 **Effets hover**: Boutons interactifs qui changent de couleur au survol
- 📈 **Status bar en bas**: Indicateur de connexion et dernière mise à jour

### Couleurs dynamiques
- 🟢 **Vert** (< 50 dB): Niveau sonore normal
- 🟠 **Orange** (50-70 dB): Niveau sonore modéré
- 🔴 **Rouge** (> 70 dB): Niveau sonore élevé

### Organisation
- 📌 **Cartes séparées**: Niveau sonore, médias, événements dans des cartes distinctes
- 🗂️ **Onglets stylisés**: Navigation améliorée avec onglets modernes
- 📊 **Statistiques formatées**: Présentation claire avec séparateurs et icônes
- 🎯 **Meilleure lisibilité**: Polices plus grandes, espacement optimisé

### Fichiers de l'interface moderne
- `interface_connexion_moderne.py`: Écran de connexion moderne
- `interface_principale_moderne.py`: Dashboard moderne
- `lancer_interface_moderne.py`: Lanceur pour la version moderne

---

## 🚀 Prochaines fonctionnalités possibles

- 📊 Graphiques en temps réel (matplotlib)
- 📧 Notifications par email pour événements
- 📱 Export des données (CSV, Excel)
- 🎥 Lecture des vidéos dans l'interface
- 📷 Affichage des photos dans l'interface
- 🔔 Alertes sonores pour bruits forts
- 📈 Graphiques d'évolution sur 24h
- 👥 Gestion des utilisateurs (admin)
- 🌙 Mode sombre / Mode clair
- 📱 Interface responsive
