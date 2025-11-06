/* ============================================================
   CHECK CONSTRAINTS AVANCÉES - SalleSense
   ============================================================
   Contraintes CHECK complexes pour validation des données
   ============================================================ */

USE Prog3A25_bdSalleSense;
GO

/* ============================================================
   UTILISATEUR - Contraintes avancées
   ============================================================ */

-- 1) Pseudo: minimum 3 caractères, pas uniquement des espaces
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_utilisateur_pseudo_valide')
    ALTER TABLE Utilisateur DROP CONSTRAINT ck_utilisateur_pseudo_valide;
GO

ALTER TABLE Utilisateur
ADD CONSTRAINT ck_utilisateur_pseudo_valide
CHECK (
    LEN(LTRIM(RTRIM(pseudo))) >= 3
    AND pseudo NOT LIKE '%  %'  -- Pas de doubles espaces
    AND pseudo = LTRIM(RTRIM(pseudo))  -- Pas d'espaces au début/fin
);
GO

-- 2) Email: format avancé avec validations multiples
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_utilisateur_email_avance')
    ALTER TABLE Utilisateur DROP CONSTRAINT ck_utilisateur_email_avance;
GO

ALTER TABLE Utilisateur
ADD CONSTRAINT ck_utilisateur_email_avance
CHECK (
    -- Contient exactement un @
    LEN(courriel) - LEN(REPLACE(courriel, '@', '')) = 1
    AND
    -- Au moins 2 caractères avant le @
    CHARINDEX('@', courriel) > 2
    AND
    -- Au moins 3 caractères après le @
    LEN(courriel) - CHARINDEX('@', courriel) >= 3
    AND
    -- Contient un point après le @
    CHARINDEX('.', courriel, CHARINDEX('@', courriel)) > 0
    AND
    -- Pas de caractères invalides
    courriel NOT LIKE '%[<>()[\]\\,;:\s"]%'
    AND
    -- Pas d'espaces
    courriel = LTRIM(RTRIM(courriel))
    AND
    -- Longueur raisonnable
    LEN(courriel) BETWEEN 6 AND 120
);
GO

-- 3) Mot de passe: minimum 8 caractères (pour le champ legacy)
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_utilisateur_mdp_longueur')
    ALTER TABLE Utilisateur DROP CONSTRAINT ck_utilisateur_mdp_longueur;
GO

ALTER TABLE Utilisateur
ADD CONSTRAINT ck_utilisateur_mdp_longueur
CHECK (LEN(motDePasse) >= 8);
GO


/* ============================================================
   SALLE - Contraintes avancées
   ============================================================ */

-- 4) Numéro de salle: format strict avec variations
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_salle_numero_avance')
    ALTER TABLE Salle DROP CONSTRAINT ck_salle_numero_avance;
GO

ALTER TABLE Salle
ADD CONSTRAINT ck_salle_numero_avance
CHECK (
    -- Format A-101 ou AB-101
    (
        numero LIKE '[A-Z]-[0-9][0-9][0-9]'
        OR numero LIKE '[A-Z][A-Z]-[0-9][0-9][0-9]'
        OR numero LIKE '[A-Z]-[0-9][0-9][0-9][0-9]'  -- Support 4 chiffres
    )
    AND
    -- Pas d'espaces
    numero = LTRIM(RTRIM(numero))
);
GO

-- 5) Capacité maximale: entre 1 et 500 personnes
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_salle_capacite_range')
    ALTER TABLE Salle DROP CONSTRAINT ck_salle_capacite_range;
GO

ALTER TABLE Salle
ADD CONSTRAINT ck_salle_capacite_range
CHECK (capaciteMaximale BETWEEN 1 AND 500);
GO


/* ============================================================
   RESERVATION - Contraintes avancées
   ============================================================ */

-- 6) Durée minimale: au moins 15 minutes
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_reservation_duree_min')
    ALTER TABLE Reservation DROP CONSTRAINT ck_reservation_duree_min;
GO

ALTER TABLE Reservation
ADD CONSTRAINT ck_reservation_duree_min
CHECK (DATEDIFF(MINUTE, heureDebut, heureFin) >= 15);
GO

-- 7) Durée maximale: maximum 8 heures (480 minutes)
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_reservation_duree_max')
    ALTER TABLE Reservation DROP CONSTRAINT ck_reservation_duree_max;
GO

ALTER TABLE Reservation
ADD CONSTRAINT ck_reservation_duree_max
CHECK (DATEDIFF(MINUTE, heureDebut, heureFin) <= 480);
GO

-- 8) Nombre de personnes: entre 1 et 100
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_reservation_nb_personnes_range')
    ALTER TABLE Reservation DROP CONSTRAINT ck_reservation_nb_personnes_range;
GO

ALTER TABLE Reservation
ADD CONSTRAINT ck_reservation_nb_personnes_range
CHECK (nombrePersonne BETWEEN 1 AND 100);
GO

-- 9) Les réservations doivent être alignées sur des tranches de 15 minutes
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_reservation_horaire_aligne')
    ALTER TABLE Reservation DROP CONSTRAINT ck_reservation_horaire_aligne;
GO

ALTER TABLE Reservation
ADD CONSTRAINT ck_reservation_horaire_aligne
CHECK (
    DATEPART(MINUTE, heureDebut) % 15 = 0
    AND DATEPART(MINUTE, heureFin) % 15 = 0
);
GO


/* ============================================================
   CAPTEUR - Contraintes avancées
   ============================================================ */

-- 10) Nom du capteur: format CODE-NUMERO (ex: PIR-1, MIC-2, CAM-3)
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_capteur_nom_format')
    ALTER TABLE Capteur DROP CONSTRAINT ck_capteur_nom_format;
GO

ALTER TABLE Capteur
ADD CONSTRAINT ck_capteur_nom_format
CHECK (
    nom LIKE '[A-Z][A-Z][A-Z]-[0-9]%'
    AND LEN(nom) BETWEEN 5 AND 20
    AND nom = LTRIM(RTRIM(nom))
);
GO

-- 11) Type de capteur: seulement les valeurs autorisées
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_capteur_type_valide')
    ALTER TABLE Capteur DROP CONSTRAINT ck_capteur_type_valide;
GO

ALTER TABLE Capteur
ADD CONSTRAINT ck_capteur_type_valide
CHECK (
    type IN ('MOUVEMENT', 'BRUIT', 'CAMERA', 'TEMPERATURE', 'HUMIDITE', 'CO2')
);
GO


/* ============================================================
   DONNEES - Contraintes avancées
   ============================================================ */

-- 12) Mesure: plage valide selon type standard (0-200)
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_donnees_mesure_range')
    ALTER TABLE Donnees DROP CONSTRAINT ck_donnees_mesure_range;
GO

ALTER TABLE Donnees
ADD CONSTRAINT ck_donnees_mesure_range
CHECK (
    mesure IS NULL
    OR mesure BETWEEN 0 AND 200
);
GO

-- 13) Photo: format de chemin valide
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_donnees_photo_format')
    ALTER TABLE Donnees DROP CONSTRAINT ck_donnees_photo_format;
GO

ALTER TABLE Donnees
ADD CONSTRAINT ck_donnees_photo_format
CHECK (
    photo IS NULL
    OR (
        -- Format: chemin/fichier.extension
        photo LIKE '%/%'
        AND (
            photo LIKE '%.jpg'
            OR photo LIKE '%.jpeg'
            OR photo LIKE '%.png'
            OR photo LIKE '%.gif'
        )
        AND LEN(photo) BETWEEN 5 AND 255
    )
);
GO

-- 14) Au moins une donnée (mesure OU photo) doit être présente
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_donnees_au_moins_une')
    ALTER TABLE Donnees DROP CONSTRAINT ck_donnees_au_moins_une;
GO

ALTER TABLE Donnees
ADD CONSTRAINT ck_donnees_au_moins_une
CHECK (mesure IS NOT NULL OR photo IS NOT NULL);
GO

-- 15) Date des données ne peut pas être dans le futur
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_donnees_date_valide')
    ALTER TABLE Donnees DROP CONSTRAINT ck_donnees_date_valide;
GO

ALTER TABLE Donnees
ADD CONSTRAINT ck_donnees_date_valide
CHECK (dateHeure <= GETDATE());
GO


/* ============================================================
   EVENEMENT - Contraintes avancées
   ============================================================ */

-- 16) Type d'événement: liste exhaustive
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_evenement_type_valide')
    ALTER TABLE Evenement DROP CONSTRAINT ck_evenement_type_valide;
GO

ALTER TABLE Evenement
ADD CONSTRAINT ck_evenement_type_valide
CHECK (
    type IN (
        'ENTREE',
        'SORTIE',
        'BRUIT_FORT',
        'BRUIT_FAIBLE',
        'CAPTURE',
        'MOUVEMENT_DETECTE',
        'TEMPERATURE_HAUTE',
        'TEMPERATURE_BASSE',
        'ALERTE_CO2',
        'HUMIDITE_ANORMALE'
    )
);
GO

-- 17) Description: longueur minimale si présente
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_evenement_description_longueur')
    ALTER TABLE Evenement DROP CONSTRAINT ck_evenement_description_longueur;
GO

ALTER TABLE Evenement
ADD CONSTRAINT ck_evenement_description_longueur
CHECK (
    description IS NULL
    OR LEN(LTRIM(RTRIM(description))) >= 10
);
GO


/* ============================================================
   BLACKLIST - Contraintes avancées
   ============================================================ */

-- 18) Un utilisateur ne peut être qu'une seule fois dans la blacklist
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'uq_blacklist_utilisateur')
    DROP INDEX uq_blacklist_utilisateur ON Blacklist;
GO

CREATE UNIQUE INDEX uq_blacklist_utilisateur
ON Blacklist(idUtilisateur);
GO


/* ======= TESTS DES CONTRAINTES CHECK =======

-- Test 1: Pseudo trop court
INSERT INTO Utilisateur (pseudo, courriel, motDePasse)
VALUES ('ab', 'test@example.com', 'password123');
-- Devrait échouer: pseudo < 3 caractères

-- Test 2: Email sans point après @
INSERT INTO Utilisateur (pseudo, courriel, motDePasse)
VALUES ('alice', 'test@example', 'password123');
-- Devrait échouer: pas de point après @

-- Test 3: Capacité salle invalide
INSERT INTO Salle (numero, capaciteMaximale)
VALUES ('A-101', 1000);
-- Devrait échouer: capacité > 500

-- Test 4: Réservation trop courte
INSERT INTO Reservation (heureDebut, heureFin, noSalle, noPersonne, nombrePersonne)
VALUES ('2025-09-25 10:00:00', '2025-09-25 10:10:00', 1, 1, 5);
-- Devrait échouer: durée < 15 minutes

-- Test 5: Horaire non aligné
INSERT INTO Reservation (heureDebut, heureFin, noSalle, noPersonne, nombrePersonne)
VALUES ('2025-09-25 10:13:00', '2025-09-25 11:13:00', 1, 1, 5);
-- Devrait échouer: minutes pas multiple de 15

-- Test 6: Nom capteur invalide
INSERT INTO Capteur (nom, type)
VALUES ('capteur1', 'BRUIT');
-- Devrait échouer: format nom incorrect

-- Test 7: Type capteur inconnu
INSERT INTO Capteur (nom, type)
VALUES ('SEN-1', 'LUMIERE');
-- Devrait échouer: type non autorisé

-- Test 8: Photo avec mauvaise extension
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
VALUES ('2025-09-19 10:00:00', 3, NULL, 'photos/image.bmp', 1);
-- Devrait échouer: extension .bmp non autorisée

-- Test 9: Donnée dans le futur
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
VALUES ('2026-12-31 23:59:59', 2, 50.0, NULL, 1);
-- Devrait échouer: date dans le futur

-- Test 10: Type événement invalide
INSERT INTO Evenement (type, idDonnee, description)
VALUES ('INCONNU', 1, 'Test événement');
-- Devrait échouer: type non autorisé

-- Test 11: Description trop courte
INSERT INTO Evenement (type, idDonnee, description)
VALUES ('ENTREE', 1, 'Court');
-- Devrait échouer: description < 10 caractères

-- Test 12: Données sans mesure ni photo
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
VALUES ('2025-09-19 10:00:00', 1, NULL, NULL, 1);
-- Devrait échouer: ni mesure ni photo

=========================================*/


/* ======= RÉSUMÉ DES CONTRAINTES =======

UTILISATEUR:
  - Pseudo: min 3 caractères, pas d'espaces multiples
  - Email: format complet avec validation avancée
  - Mot de passe: min 8 caractères

SALLE:
  - Numéro: format A-101, AB-101, ou A-1001
  - Capacité: entre 1 et 500 personnes

RESERVATION:
  - Durée: entre 15 minutes et 8 heures
  - Nombre personnes: entre 1 et 100
  - Horaires alignés sur 15 minutes (00, 15, 30, 45)

CAPTEUR:
  - Nom: format CODE-NUMERO (ex: PIR-1)
  - Type: liste limitée (MOUVEMENT, BRUIT, CAMERA, etc.)

DONNEES:
  - Mesure: entre 0 et 200 si présente
  - Photo: format chemin/fichier.jpg|png|jpeg|gif
  - Au moins une donnée (mesure OU photo)
  - Date dans le passé uniquement

EVENEMENT:
  - Type: liste exhaustive de 10 types
  - Description: min 10 caractères si présente

BLACKLIST:
  - Un utilisateur maximum une fois

=========================================*/
