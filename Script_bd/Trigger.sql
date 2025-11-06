USE Prog3A25_bdSalleSense;
GO
CREATE OR ALTER TRIGGER trg_pasDeChevauchement
ON dbo.Reservation
AFTER INSERT, UPDATE
AS
BEGIN
  SET NOCOUNT ON;
  IF EXISTS (
    SELECT 1
    FROM inserted i
    JOIN dbo.Reservation r
      ON r.noSalle = i.noSalle
     AND r.idReservation_PK <> i.idReservation_PK
     AND r.heureDebut < i.heureFin
     AND r.heureFin   > i.heureDebut
  )
  BEGIN
    RAISERROR(N'Chevauchement de réservations pour la même salle.',17,1);
    ROLLBACK TRANSACTION;
    RETURN;
  END
END;
GO


CREATE OR ALTER TRIGGER verifierNombreAvertissement
ON Avertissement
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    ;WITH u AS (
        -- utilisateurs impactés par cette insertion
        SELECT DISTINCT idUtilisateur
        FROM inserted
    ),
    c AS (
        -- nombre total d'avertissements PAR utilisateur (après l'insert)
        SELECT a.idUtilisateur, COUNT(*) AS nbAvert
        FROM Avertissement a
        JOIN u ON u.idUtilisateur = a.idUtilisateur
        GROUP BY a.idUtilisateur
    ),
    d AS (
        -- calcul de la duree selon le nombre d'avertissements
        SELECT
            c.idUtilisateur,
            CAST(CASE
                    WHEN c.nbAvert = 1 THEN '01:00:00'
                    WHEN c.nbAvert = 2 THEN '23:59:59.999'  -- ~24h (TIME ne supporte pas 24:00:00)
                    ELSE NULL                                -- >= 3 => ban permanent (NULL)
                END AS TIME) AS duree
        FROM c
    )
    -- 1) UPDATE des lignes Blacklist déjà existantes
    UPDATE b 
    SET b.duree = d.duree
    FROM Blacklist b
    JOIN d ON d.idUtilisateur = b.idUtilisateur;

    -- 2) INSERT pour ceux qui n'ont pas encore de ligne dans Blacklist
    INSERT INTO Blacklist (idUtilisateur, duree)
    SELECT d.idUtilisateur, d.duree
    FROM d
    WHERE NOT EXISTS (
        SELECT 1
        FROM Blacklist b
        WHERE b.idUtilisateur = d.idUtilisateur
    );
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

-- Recréer le trigger pour valider selon le type de capteur
IF OBJECT_ID('trg_check_donnees_capteur', 'TR') IS NOT NULL
    DROP TRIGGER trg_check_donnees_capteur;
GO

CREATE TRIGGER trg_check_donnees_capteur
ON Donnees
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    -- Vérifier capteur MOUVEMENT : pas de mesure, pas de photo
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Capteur c ON c.idCapteur_PK = i.idCapteur
        WHERE c.type = 'MOUVEMENT'
          AND (i.mesure IS NOT NULL OR i.photoBlob IS NOT NULL)
    )
    BEGIN
        RAISERROR('Un capteur MOUVEMENT ne peut pas avoir de mesure ou de photo', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Vérifier capteur BRUIT : mesure obligatoire, pas de photo
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Capteur c ON c.idCapteur_PK = i.idCapteur
        WHERE c.type = 'BRUIT'
          AND (i.mesure IS NULL OR i.photoBlob IS NOT NULL)
    )
    BEGIN
        RAISERROR('Un capteur BRUIT doit avoir une mesure et pas de photo', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Vérifier capteur CAMERA : photoBlob obligatoire, pas de mesure
    IF EXISTS (
        SELECT 1
        FROM inserted i
        JOIN Capteur c ON c.idCapteur_PK = i.idCapteur
        WHERE c.type = 'CAMERA'
          AND (i.photoBlob IS NULL OR i.mesure IS NOT NULL)
    )
    BEGIN
        RAISERROR('Un capteur CAMERA doit avoir une photo (BLOB) et pas de mesure', 16, 1);
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