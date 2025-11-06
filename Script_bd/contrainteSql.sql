-- Unicités
ALTER TABLE Utilisateur
ADD CONSTRAINT uq_utilisateur_courriel UNIQUE (courriel);
GO

ALTER TABLE Salle
ADD CONSTRAINT uq_salle_numero UNIQUE (numero);
GO

-- CHECK: cohérence des dates + nb personnes > 0
ALTER TABLE Reservation
ADD CONSTRAINT ck_reservation_dates
CHECK (heureDebut < heureFin);
GO

ALTER TABLE Reservation
ADD CONSTRAINT ck_reservation_nb
CHECK (nombrePersonne > 0);
GO

-- CHECK: capacité positive
ALTER TABLE Salle
ADD CONSTRAINT ck_salle_capacite
CHECK (capaciteMaximale > 0);
GO

-- CHECK: mesure >= 0 si présente
ALTER TABLE Donnees
ADD CONSTRAINT ck_donnees_mesure
CHECK (mesure IS NULL OR mesure >= 0);
GO

-- CHECK: type non vide (après trim)
ALTER TABLE Evenement
ADD CONSTRAINT ck_evenement_type
CHECK (LEN(LTRIM(RTRIM([type]))) > 0);
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

/* =========================
   Clés étrangères (FK)
   ========================= */

-- Blacklist → Utilisateur
ALTER TABLE Blacklist
ADD CONSTRAINT fk_blacklist_utilisateur
FOREIGN KEY (idUtilisateur)
REFERENCES Utilisateur (idUtilisateur_PK)

GO

-- Reservation → Salle
ALTER TABLE Reservation
ADD CONSTRAINT fk_reservation_salle
FOREIGN KEY (noSalle)
REFERENCES Salle (idSalle_PK)

GO

-- Reservation → Utilisateur (réservant)
ALTER TABLE Reservation
ADD CONSTRAINT fk_reservation_utilisateur
FOREIGN KEY (noPersonne)
REFERENCES Utilisateur (idUtilisateur_PK)

GO

-- Donnees → Capteur
ALTER TABLE Donnees
ADD CONSTRAINT fk_donnees_capteur
FOREIGN KEY (idCapteur)
REFERENCES Capteur (idCapteur_PK)

GO

-- Donnees → Salle
ALTER TABLE Donnees
ADD CONSTRAINT fk_donnees_salle
FOREIGN KEY (noSalle)
REFERENCES Salle (idSalle_PK)

GO

-- Evenement → Donnees
ALTER TABLE Evenement
ADD CONSTRAINT fk_evenement_donnee
FOREIGN KEY (idDonnee)
REFERENCES Donnees (idDonnee_PK)

-- Mettre à jour la contrainte : au moins une donnée (mesure OU photoBlob)
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_donnees_au_moins_une')
    ALTER TABLE Donnees DROP CONSTRAINT ck_donnees_au_moins_une;
GO

ALTER TABLE Donnees
ADD CONSTRAINT ck_donnees_au_moins_une
CHECK (mesure IS NOT NULL OR photoBlob IS NOT NULL);
GO

-- Supprimer l'ancienne contrainte de format de photo si elle existe encore
IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'ck_donnees_photo_format')
    ALTER TABLE Donnees DROP CONSTRAINT ck_donnees_photo_format;
GO
