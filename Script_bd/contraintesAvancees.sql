/* ============================================================
   CONTRAINTES AVANCÉES - SalleSense
   ============================================================
   Contraintes complexes pour garantir l'intégrité des données
   ============================================================ */

USE Prog3A25_bdSalleSense;
GO

/* ============================================================
   1) Empêcher les réservations qui se chevauchent
   ----------------------------------------------------------
   Un TRIGGER qui vérifie qu'aucune autre réservation n'existe
   pour la même salle aux mêmes dates/heures
   ============================================================ */
IF OBJECT_ID('trg_check_reservation_overlap', 'TR') IS NOT NULL
    DROP TRIGGER trg_check_reservation_overlap;
GO

CREATE TRIGGER trg_check_reservation_overlap
ON Reservation
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Vérifier s'il existe un chevauchement
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Reservation r
            ON r.noSalle = i.noSalle
            AND r.idReservation_PK != i.idReservation_PK
        WHERE (
            -- Cas 1: la nouvelle réservation commence pendant une réservation existante
            (i.heureDebut >= r.heureDebut AND i.heureDebut < r.heureFin)
            OR
            -- Cas 2: la nouvelle réservation se termine pendant une réservation existante
            (i.heureFin > r.heureDebut AND i.heureFin <= r.heureFin)
            OR
            -- Cas 3: la nouvelle réservation englobe complètement une réservation existante
            (i.heureDebut <= r.heureDebut AND i.heureFin >= r.heureFin)
        )
    )
    BEGIN
        RAISERROR('Une réservation existe déjà pour cette salle à ces horaires', 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO


/* ============================================================
   2) Vérifier que le nombre de personnes ne dépasse pas la capacité
   ----------------------------------------------------------
   TRIGGER qui compare nombrePersonne avec capaciteMaximale
   ============================================================ */
IF OBJECT_ID('trg_check_reservation_capacite', 'TR') IS NOT NULL
    DROP TRIGGER trg_check_reservation_capacite;
GO

CREATE TRIGGER trg_check_reservation_capacite
ON Reservation
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Salle s ON s.idSalle_PK = i.noSalle
        WHERE i.nombrePersonne > s.capaciteMaximale
    )
    BEGIN
        DECLARE @capacite INT, @demande INT, @salle NVARCHAR(40);

        SELECT TOP 1
            @capacite = s.capaciteMaximale,
            @demande = i.nombrePersonne,
            @salle = s.numero
        FROM inserted i
        JOIN Salle s ON s.idSalle_PK = i.noSalle
        WHERE i.nombrePersonne > s.capaciteMaximale;

        DECLARE @msg NVARCHAR(200) =
            'Capacité dépassée pour la salle ' + @salle +
            ': demandé ' + CAST(@demande AS NVARCHAR(10)) +
            ' personnes, capacité max ' + CAST(@capacite AS NVARCHAR(10));

        RAISERROR(@msg, 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO


/* ============================================================
   3) Empêcher les utilisateurs de la blacklist de réserver
   ----------------------------------------------------------
   TRIGGER qui vérifie que l'utilisateur n'est pas banni
   ============================================================ */
IF OBJECT_ID('trg_check_blacklist', 'TR') IS NOT NULL
    DROP TRIGGER trg_check_blacklist;
GO

CREATE TRIGGER trg_check_blacklist
ON Reservation
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Blacklist b ON b.idUtilisateur = i.noPersonne
    )
    BEGIN
        DECLARE @pseudo NVARCHAR(80);
        SELECT TOP 1 @pseudo = u.pseudo
        FROM inserted i
        JOIN Utilisateur u ON u.idUtilisateur_PK = i.noPersonne
        JOIN Blacklist b ON b.idUtilisateur = i.noPersonne;

        DECLARE @msgBlacklist NVARCHAR(200) =
            'L''utilisateur ' + @pseudo + ' est banni et ne peut pas réserver';

        RAISERROR(@msgBlacklist, 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO


/* ============================================================
   4) Validation des données capteurs selon le type
   ----------------------------------------------------------
   TRIGGER qui vérifie:
   - MOUVEMENT: pas de mesure numérique, pas de photo
   - BRUIT: mesure obligatoire, pas de photo
   - CAMERA: photo obligatoire, pas de mesure
   ============================================================ */
IF OBJECT_ID('trg_check_donnees_capteur', 'TR') IS NOT NULL
    DROP TRIGGER trg_check_donnees_capteur;
GO

CREATE TRIGGER trg_check_donnees_capteur
ON Donnees
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Vérifier capteur MOUVEMENT
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Capteur c ON c.idCapteur_PK = i.idCapteur
        WHERE c.type = 'MOUVEMENT'
          AND (i.mesure IS NOT NULL OR i.photo IS NOT NULL)
    )
    BEGIN
        RAISERROR('Un capteur MOUVEMENT ne peut pas avoir de mesure ou de photo', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Vérifier capteur BRUIT
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Capteur c ON c.idCapteur_PK = i.idCapteur
        WHERE c.type = 'BRUIT'
          AND (i.mesure IS NULL OR i.photo IS NOT NULL)
    )
    BEGIN
        RAISERROR('Un capteur BRUIT doit avoir une mesure et pas de photo', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Vérifier capteur CAMERA
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Capteur c ON c.idCapteur_PK = i.idCapteur
        WHERE c.type = 'CAMERA'
          AND (i.photo IS NULL OR i.mesure IS NOT NULL)
    )
    BEGIN
        RAISERROR('Un capteur CAMERA doit avoir une photo et pas de mesure', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Vérifier plage de mesure pour capteur BRUIT (0-120 dB)
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Capteur c ON c.idCapteur_PK = i.idCapteur
        WHERE c.type = 'BRUIT'
          AND (i.mesure < 0 OR i.mesure > 120)
    )
    BEGIN
        RAISERROR('La mesure de bruit doit être entre 0 et 120 dB', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END
END;
GO


/* ============================================================
   5) Limiter les réservations aux heures ouvrables
   ----------------------------------------------------------
   CHECK constraint + TRIGGER pour vérifier les horaires
   (7h00 - 22h00, lundi à samedi uniquement)
   ============================================================ */
IF OBJECT_ID('trg_check_business_hours', 'TR') IS NOT NULL
    DROP TRIGGER trg_check_business_hours;
GO

CREATE TRIGGER trg_check_business_hours
ON Reservation
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Vérifier que c'est du lundi au samedi (1-6, où 1=lundi, 7=dimanche)
    IF EXISTS (
        SELECT 1
        FROM inserted
        WHERE DATEPART(WEEKDAY, heureDebut) = 1  -- Dimanche
           OR DATEPART(WEEKDAY, heureFin) = 1
    )
    BEGIN
        RAISERROR('Les réservations ne sont pas autorisées le dimanche', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Vérifier les heures (7h-22h)
    IF EXISTS (
        SELECT 1
        FROM inserted
        WHERE DATEPART(HOUR, heureDebut) < 7
           OR DATEPART(HOUR, heureDebut) >= 22
           OR DATEPART(HOUR, heureFin) < 7
           OR DATEPART(HOUR, heureFin) > 22
    )
    BEGIN
        RAISERROR('Les réservations doivent être entre 7h00 et 22h00', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Vérifier durée maximale (8 heures)
    IF EXISTS (
        SELECT 1
        FROM inserted
        WHERE DATEDIFF(HOUR, heureDebut, heureFin) > 8
    )
    BEGIN
        RAISERROR('Une réservation ne peut pas dépasser 8 heures', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Empêcher les réservations dans le passé
    IF EXISTS (
        SELECT 1
        FROM inserted
        WHERE heureDebut < GETDATE()
    )
    BEGIN
        RAISERROR('Impossible de réserver dans le passé', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END
END;
GO


/* ============================================================
   6) Limiter le nombre de réservations actives par utilisateur
   ----------------------------------------------------------
   Un utilisateur ne peut avoir max 5 réservations futures en même temps
   ============================================================ */
IF OBJECT_ID('trg_check_max_reservations', 'TR') IS NOT NULL
    DROP TRIGGER trg_check_max_reservations;
GO

CREATE TRIGGER trg_check_max_reservations
ON Reservation
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @maxReservations INT = 5;

    IF EXISTS (
        SELECT i.noPersonne
        FROM inserted i
        JOIN Reservation r ON r.noPersonne = i.noPersonne
        WHERE r.heureFin >= GETDATE()
        GROUP BY i.noPersonne
        HAVING COUNT(*) > @maxReservations
    )
    BEGIN
        DECLARE @msgMax NVARCHAR(200) =
            'Un utilisateur ne peut pas avoir plus de ' +
            CAST(@maxReservations AS NVARCHAR(10)) +
            ' réservations actives';

        RAISERROR(@msgMax, 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO


/* ============================================================
   7) Validation format email
   ----------------------------------------------------------
   CHECK constraint pour vérifier le format de l'email
   ============================================================ */
IF EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = 'ck_utilisateur_email_format'
)
BEGIN
    ALTER TABLE Utilisateur DROP CONSTRAINT ck_utilisateur_email_format;
END
GO

ALTER TABLE Utilisateur
ADD CONSTRAINT ck_utilisateur_email_format
CHECK (
    courriel LIKE '%_@_%.__%'
    AND courriel NOT LIKE '%[<>()[\]\\,;:\s]%'
    AND LEN(courriel) >= 6
);
GO


/* ============================================================
   8) Validation format numéro de salle
   ----------------------------------------------------------
   CHECK constraint: format lettre-chiffres (ex: A-101, B-202)
   ============================================================ */
IF EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = 'ck_salle_numero_format'
)
BEGIN
    ALTER TABLE Salle DROP CONSTRAINT ck_salle_numero_format;
END
GO

ALTER TABLE Salle
ADD CONSTRAINT ck_salle_numero_format
CHECK (
    numero LIKE '[A-Z]-[0-9][0-9][0-9]'
    OR numero LIKE '[A-Z][A-Z]-[0-9][0-9][0-9]'
);
GO


/* ======= TESTS DES CONTRAINTES =======

-- Test 1: Chevauchement de réservations
INSERT INTO Reservation (heureDebut, heureFin, noSalle, noPersonne, nombrePersonne)
VALUES ('2025-09-19 10:30:00', '2025-09-19 11:30:00', 1, 1, 2);
-- Devrait échouer si une réservation existe déjà pour la salle 1 à ces heures

-- Test 2: Dépassement de capacité
INSERT INTO Reservation (heureDebut, heureFin, noSalle, noPersonne, nombrePersonne)
VALUES ('2025-09-25 10:00:00', '2025-09-25 12:00:00', 1, 1, 100);
-- Devrait échouer: 100 personnes > capacité de la salle 1 (20)

-- Test 3: Utilisateur banni
INSERT INTO Reservation (heureDebut, heureFin, noSalle, noPersonne, nombrePersonne)
VALUES ('2025-09-25 10:00:00', '2025-09-25 12:00:00', 3, 2, 5);
-- Devrait échouer si l'utilisateur 2 (bob) est dans la blacklist

-- Test 4: Mauvais format email
INSERT INTO Utilisateur (pseudo, courriel, motDePasse)
VALUES ('test', 'email_invalide', 'pwd');
-- Devrait échouer: pas de @

-- Test 5: Mauvais format numéro salle
INSERT INTO Salle (numero, capaciteMaximale)
VALUES ('Salle1', 20);
-- Devrait échouer: ne respecte pas le format A-101

-- Test 6: Capteur BRUIT sans mesure
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle)
VALUES ('2025-09-19 10:00:00', 2, NULL, NULL, 1);
-- Devrait échouer: capteur 2 (BRUIT) doit avoir une mesure

-- Test 7: Réservation le dimanche
INSERT INTO Reservation (heureDebut, heureFin, noSalle, noPersonne, nombrePersonne)
VALUES ('2025-09-21 10:00:00', '2025-09-21 12:00:00', 1, 1, 5);
-- Devrait échouer si le 21/09/2025 est un dimanche

=========================================*/
