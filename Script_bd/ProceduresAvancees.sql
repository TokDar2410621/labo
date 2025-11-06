/* ============================================================
   PROCÉDURES STOCKÉES AVANCÉES - SalleSense
   ============================================================
   Procédures complexes pour gérer les opérations métier
   ============================================================ */

USE Prog3A25_bdSalleSense;
GO

/* ============================================================
   1) usp_Reservation_Creer
   ----------------------------------------------------------
   Crée une réservation avec validations complètes:
   - Vérifie que l'utilisateur n'est pas banni
   - Vérifie la disponibilité de la salle
   - Vérifie la capacité
   - Retourne l'ID de la réservation ou code d'erreur
   ============================================================ */
CREATE OR ALTER PROCEDURE dbo.usp_Reservation_Creer
    @IdUtilisateur INT,
    @IdSalle INT,
    @HeureDebut DATETIME2,
    @HeureFin DATETIME2,
    @NombrePersonnes INT,
    @IdReservation INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Vérifier si l'utilisateur existe
        IF NOT EXISTS (SELECT 1 FROM Utilisateur WHERE idUtilisateur_PK = @IdUtilisateur)
        BEGIN
            ROLLBACK;
            RETURN -1;  -- Utilisateur introuvable
        END

        -- Vérifier si l'utilisateur est banni
        IF EXISTS (SELECT 1 FROM Blacklist WHERE idUtilisateur = @IdUtilisateur)
        BEGIN
            ROLLBACK;
            RETURN -2;  -- Utilisateur banni
        END

        -- Vérifier si la salle existe
        DECLARE @CapaciteMax INT;
        SELECT @CapaciteMax = capaciteMaximale
        FROM Salle
        WHERE idSalle_PK = @IdSalle;

        IF @CapaciteMax IS NULL
        BEGIN
            ROLLBACK;
            RETURN -3;  -- Salle introuvable
        END

        -- Vérifier la capacité
        IF @NombrePersonnes > @CapaciteMax
        BEGIN
            ROLLBACK;
            RETURN -4;  -- Capacité dépassée
        END

        -- Vérifier les chevauchements
        IF EXISTS (
            SELECT 1 FROM Reservation
            WHERE noSalle = @IdSalle
            AND (
                (@HeureDebut >= heureDebut AND @HeureDebut < heureFin)
                OR (@HeureFin > heureDebut AND @HeureFin <= heureFin)
                OR (@HeureDebut <= heureDebut AND @HeureFin >= heureFin)
            )
        )
        BEGIN
            ROLLBACK;
            RETURN -5;  -- Salle déjà réservée
        END

        -- Créer la réservation
        INSERT INTO Reservation (heureDebut, heureFin, noSalle, noPersonne, nombrePersonne)
        VALUES (@HeureDebut, @HeureFin, @IdSalle, @IdUtilisateur, @NombrePersonnes);

        SET @IdReservation = SCOPE_IDENTITY();

        COMMIT TRANSACTION;
        RETURN 0;  -- Succès

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        RETURN -99;  -- Erreur système
    END CATCH
END;
GO

/* ======= EXEMPLE D'UTILISATION =======
DECLARE @IdRes INT;
DECLARE @Result INT;

EXEC @Result = dbo.usp_Reservation_Creer
    @IdUtilisateur = 1,
    @IdSalle = 1,
    @HeureDebut = '2025-09-25 10:00:00',
    @HeureFin = '2025-09-25 12:00:00',
    @NombrePersonnes = 5,
    @IdReservation = @IdRes OUTPUT;

IF @Result = 0
    PRINT 'Réservation créée avec ID: ' + CAST(@IdRes AS VARCHAR);
ELSE
    PRINT 'Erreur code: ' + CAST(@Result AS VARCHAR);
=========================================*/


/* ============================================================
   2) usp_Reservation_Annuler
   ----------------------------------------------------------
   Annule une réservation si elle n'a pas encore commencé
   ============================================================ */
CREATE OR ALTER PROCEDURE dbo.usp_Reservation_Annuler
    @IdReservation INT,
    @IdUtilisateur INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Vérifier si la réservation existe
        DECLARE @HeureDebut DATETIME2, @Proprietaire INT;

        SELECT @HeureDebut = heureDebut, @Proprietaire = noPersonne
        FROM Reservation
        WHERE idReservation_PK = @IdReservation;

        IF @HeureDebut IS NULL
        BEGIN
            ROLLBACK;
            RETURN -1;  -- Réservation introuvable
        END

        -- Vérifier que c'est le propriétaire
        IF @Proprietaire != @IdUtilisateur
        BEGIN
            ROLLBACK;
            RETURN -2;  -- Pas le propriétaire
        END

        -- Vérifier que la réservation n'a pas commencé
        IF @HeureDebut <= GETDATE()
        BEGIN
            ROLLBACK;
            RETURN -3;  -- Réservation déjà commencée
        END

        -- Supprimer la réservation
        DELETE FROM Reservation WHERE idReservation_PK = @IdReservation;

        COMMIT TRANSACTION;
        RETURN 0;  -- Succès

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        RETURN -99;  -- Erreur système
    END CATCH
END;
GO


/* ============================================================
   3) usp_Salle_Disponibilite
   ----------------------------------------------------------
   Retourne toutes les salles disponibles pour une période donnée
   avec leur capacité
   ============================================================ */
CREATE OR ALTER PROCEDURE dbo.usp_Salle_Disponibilite
    @HeureDebut DATETIME2,
    @HeureFin DATETIME2,
    @CapaciteMin INT = 1
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        s.idSalle_PK,
        s.numero,
        s.capaciteMaximale,
        -- Nombre de capteurs dans la salle
        (SELECT COUNT(DISTINCT idCapteur)
         FROM Donnees
         WHERE noSalle = s.idSalle_PK) AS nb_capteurs
    FROM Salle s
    WHERE s.capaciteMaximale >= @CapaciteMin
    AND NOT EXISTS (
        SELECT 1 FROM Reservation r
        WHERE r.noSalle = s.idSalle_PK
        AND (
            (@HeureDebut >= r.heureDebut AND @HeureDebut < r.heureFin)
            OR (@HeureFin > r.heureDebut AND @HeureFin <= r.heureFin)
            OR (@HeureDebut <= r.heureDebut AND @HeureFin >= r.heureFin)
        )
    )
    ORDER BY s.capaciteMaximale, s.numero;
END;
GO

/* ======= EXEMPLE D'UTILISATION =======
-- Trouver les salles disponibles demain de 10h à 12h avec min 10 places
EXEC dbo.usp_Salle_Disponibilite
    @HeureDebut = '2025-09-25 10:00:00',
    @HeureFin = '2025-09-25 12:00:00',
    @CapaciteMin = 10;
=========================================*/


/* ============================================================
   4) usp_Evenement_Creer_Auto
   ----------------------------------------------------------
   Crée automatiquement un événement basé sur une donnée capteur
   avec logique de détection intelligente
   ============================================================ */
CREATE OR ALTER PROCEDURE dbo.usp_Evenement_Creer_Auto
    @IdDonnee INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @TypeCapteur NVARCHAR(40);
        DECLARE @Mesure FLOAT;
        DECLARE @TypeEvenement NVARCHAR(60);
        DECLARE @Description NVARCHAR(MAX);

        -- Récupérer les infos de la donnée
        SELECT
            @TypeCapteur = c.type,
            @Mesure = d.mesure
        FROM Donnees d
        JOIN Capteur c ON c.idCapteur_PK = d.idCapteur
        WHERE d.idDonnee_PK = @IdDonnee;

        -- Déterminer le type d'événement selon le capteur et la mesure
        IF @TypeCapteur = 'MOUVEMENT'
        BEGIN
            -- Vérifier s'il y a une réservation active
            DECLARE @ReservationActive BIT = 0;
            SELECT @ReservationActive = 1
            FROM Donnees d
            JOIN Reservation r ON r.noSalle = d.noSalle
            WHERE d.idDonnee_PK = @IdDonnee
            AND d.dateHeure BETWEEN r.heureDebut AND r.heureFin;

            IF @ReservationActive = 1
                SET @TypeEvenement = 'MOUVEMENT_DETECTE';
            ELSE
                SET @TypeEvenement = 'ENTREE';

            SET @Description = 'Mouvement détecté par capteur';
        END
        ELSE IF @TypeCapteur = 'BRUIT'
        BEGIN
            IF @Mesure >= 80
            BEGIN
                SET @TypeEvenement = 'BRUIT_FORT';
                SET @Description = 'Niveau sonore élevé: ' + CAST(ROUND(@Mesure, 1) AS NVARCHAR) + ' dB';
            END
            ELSE
            BEGIN
                SET @TypeEvenement = 'BRUIT_FAIBLE';
                SET @Description = 'Niveau sonore normal: ' + CAST(ROUND(@Mesure, 1) AS NVARCHAR) + ' dB';
            END
        END
        ELSE IF @TypeCapteur = 'CAMERA'
        BEGIN
            SET @TypeEvenement = 'CAPTURE';
            SET @Description = 'Photo capturée par caméra de surveillance';
        END
        ELSE IF @TypeCapteur = 'TEMPERATURE'
        BEGIN
            IF @Mesure > 25
            BEGIN
                SET @TypeEvenement = 'TEMPERATURE_HAUTE';
                SET @Description = 'Température élevée: ' + CAST(ROUND(@Mesure, 1) AS NVARCHAR) + '°C';
            END
            ELSE IF @Mesure < 18
            BEGIN
                SET @TypeEvenement = 'TEMPERATURE_BASSE';
                SET @Description = 'Température basse: ' + CAST(ROUND(@Mesure, 1) AS NVARCHAR) + '°C';
            END
        END
        ELSE IF @TypeCapteur = 'CO2'
        BEGIN
            IF @Mesure > 1000
            BEGIN
                SET @TypeEvenement = 'ALERTE_CO2';
                SET @Description = 'Taux de CO2 élevé: ' + CAST(ROUND(@Mesure, 0) AS NVARCHAR) + ' ppm';
            END
        END

        -- Créer l'événement si un type a été déterminé
        IF @TypeEvenement IS NOT NULL
        BEGIN
            INSERT INTO Evenement (type, idDonnee, description)
            VALUES (@TypeEvenement, @IdDonnee, @Description);

            COMMIT TRANSACTION;
            RETURN SCOPE_IDENTITY();  -- ID de l'événement créé
        END
        ELSE
        BEGIN
            ROLLBACK;
            RETURN -1;  -- Pas d'événement à créer
        END

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        RETURN -99;  -- Erreur système
    END CATCH
END;
GO


/* ============================================================
   5) usp_Utilisateur_Bannir
   ----------------------------------------------------------
   Ajoute un utilisateur à la blacklist et annule ses réservations futures
   ============================================================ */
CREATE OR ALTER PROCEDURE dbo.usp_Utilisateur_Bannir
    @IdUtilisateur INT,
    @NbReservationsAnnulees INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Vérifier si l'utilisateur existe
        IF NOT EXISTS (SELECT 1 FROM Utilisateur WHERE idUtilisateur_PK = @IdUtilisateur)
        BEGIN
            ROLLBACK;
            RETURN -1;  -- Utilisateur introuvable
        END

        -- Vérifier s'il n'est pas déjà banni
        IF EXISTS (SELECT 1 FROM Blacklist WHERE idUtilisateur = @IdUtilisateur)
        BEGIN
            ROLLBACK;
            RETURN -2;  -- Déjà banni
        END

        -- Compter les réservations futures
        SELECT @NbReservationsAnnulees = COUNT(*)
        FROM Reservation
        WHERE noPersonne = @IdUtilisateur
        AND heureFin >= GETDATE();

        -- Annuler toutes les réservations futures
        DELETE FROM Reservation
        WHERE noPersonne = @IdUtilisateur
        AND heureFin >= GETDATE();

        -- Ajouter à la blacklist
        INSERT INTO Blacklist (idUtilisateur)
        VALUES (@IdUtilisateur);

        COMMIT TRANSACTION;
        RETURN 0;  -- Succès

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        RETURN -99;  -- Erreur système
    END CATCH
END;
GO


/* ============================================================
   6) usp_Statistiques_Salle
   ----------------------------------------------------------
   Retourne des statistiques complètes pour une salle
   ============================================================ */
CREATE OR ALTER PROCEDURE dbo.usp_Statistiques_Salle
    @IdSalle INT,
    @DateDebut DATETIME2 = NULL,
    @DateFin DATETIME2 = NULL
AS
BEGIN
    SET NOCOUNT ON;

    -- Par défaut: stats des 30 derniers jours
    IF @DateDebut IS NULL
        SET @DateDebut = DATEADD(DAY, -30, GETDATE());
    IF @DateFin IS NULL
        SET @DateFin = GETDATE();

    SELECT
        s.numero AS NumeroSalle,
        s.capaciteMaximale AS Capacite,
        -- Statistiques réservations
        COUNT(DISTINCT r.idReservation_PK) AS NbReservations,
        SUM(r.nombrePersonne) AS TotalPersonnes,
        AVG(CAST(r.nombrePersonne AS FLOAT)) AS MoyennePersonnes,
        SUM(DATEDIFF(MINUTE, r.heureDebut, r.heureFin)) AS MinutesReservees,
        -- Statistiques événements
        (SELECT COUNT(*) FROM Evenement e
         JOIN Donnees d ON d.idDonnee_PK = e.idDonnee
         WHERE d.noSalle = @IdSalle
         AND d.dateHeure BETWEEN @DateDebut AND @DateFin
         AND e.type = 'BRUIT_FORT') AS NbIncidentsBruit,
        -- Niveau de bruit moyen
        (SELECT AVG(d.mesure) FROM Donnees d
         JOIN Capteur c ON c.idCapteur_PK = d.idCapteur
         WHERE d.noSalle = @IdSalle
         AND c.type = 'BRUIT'
         AND d.dateHeure BETWEEN @DateDebut AND @DateFin) AS NiveauBruitMoyen,
        -- Taux d'occupation (%)
        ROUND(
            (SUM(DATEDIFF(MINUTE, r.heureDebut, r.heureFin)) * 100.0)
            / DATEDIFF(MINUTE, @DateDebut, @DateFin)
        , 2) AS TauxOccupationPourcent
    FROM Salle s
    LEFT JOIN Reservation r
        ON r.noSalle = s.idSalle_PK
        AND r.heureDebut >= @DateDebut
        AND r.heureFin <= @DateFin
    WHERE s.idSalle_PK = @IdSalle
    GROUP BY s.idSalle_PK, s.numero, s.capaciteMaximale;
END;
GO

/* ======= EXEMPLE D'UTILISATION =======
-- Stats de la salle 1 pour le dernier mois
EXEC dbo.usp_Statistiques_Salle @IdSalle = 1;

-- Stats pour une période spécifique
EXEC dbo.usp_Statistiques_Salle
    @IdSalle = 1,
    @DateDebut = '2025-09-01',
    @DateFin = '2025-09-30';
=========================================*/


/* ============================================================
   7) usp_Rapport_Utilisateur
   ----------------------------------------------------------
   Génère un rapport complet pour un utilisateur
   ============================================================ */
CREATE OR ALTER PROCEDURE dbo.usp_Rapport_Utilisateur
    @IdUtilisateur INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Informations de base
    SELECT
        u.pseudo,
        u.courriel,
        CASE WHEN b.idBlacklist_PK IS NOT NULL THEN 'BANNI' ELSE 'ACTIF' END AS Statut,
        COUNT(DISTINCT r.idReservation_PK) AS NbReservationsTotal,
        COUNT(DISTINCT CASE WHEN r.heureFin >= GETDATE() THEN r.idReservation_PK END) AS NbReservationsFutures,
        COUNT(DISTINCT CASE WHEN r.heureFin < GETDATE() THEN r.idReservation_PK END) AS NbReservationsPassees,
        -- Score de fiabilité depuis la vue
        (SELECT score_fiabilite FROM v_score_fiabilite_utilisateur WHERE idUtilisateur_PK = @IdUtilisateur) AS ScoreFiabilite,
        -- Salle préférée
        (SELECT TOP 1 s.numero
         FROM Reservation r2
         JOIN Salle s ON s.idSalle_PK = r2.noSalle
         WHERE r2.noPersonne = @IdUtilisateur
         GROUP BY s.numero
         ORDER BY COUNT(*) DESC) AS SallePrefere
    FROM Utilisateur u
    LEFT JOIN Blacklist b ON b.idUtilisateur = u.idUtilisateur_PK
    LEFT JOIN Reservation r ON r.noPersonne = u.idUtilisateur_PK
    WHERE u.idUtilisateur_PK = @IdUtilisateur
    GROUP BY u.idUtilisateur_PK, u.pseudo, u.courriel, b.idBlacklist_PK;

    -- Détail des réservations futures
    SELECT
        r.idReservation_PK,
        s.numero AS Salle,
        r.heureDebut,
        r.heureFin,
        r.nombrePersonne,
        DATEDIFF(MINUTE, r.heureDebut, r.heureFin) AS DureeMinutes
    FROM Reservation r
    JOIN Salle s ON s.idSalle_PK = r.noSalle
    WHERE r.noPersonne = @IdUtilisateur
    AND r.heureFin >= GETDATE()
    ORDER BY r.heureDebut;
END;
GO

/* ======= EXEMPLE D'UTILISATION =======
EXEC dbo.usp_Rapport_Utilisateur @IdUtilisateur = 1;
=========================================*/


/* ======= RÉSUMÉ DES PROCÉDURES =======

1. usp_Reservation_Creer: Créer réservation avec validations complètes
   Retourne: 0=succès, -1=user introuvable, -2=banni, -3=salle introuvable,
            -4=capacité dépassée, -5=chevauchement, -99=erreur

2. usp_Reservation_Annuler: Annuler une réservation future
   Retourne: 0=succès, -1=introuvable, -2=pas propriétaire, -3=déjà commencée

3. usp_Salle_Disponibilite: Liste des salles disponibles pour une période
   Paramètres: dates + capacité minimale

4. usp_Evenement_Creer_Auto: Crée événement automatiquement selon capteur
   Logique intelligente selon type et mesure

5. usp_Utilisateur_Bannir: Bannir user + annuler ses réservations futures
   Retourne nb de réservations annulées

6. usp_Statistiques_Salle: Stats complètes d'une salle (occupation, bruit, etc.)
   Paramètres: période (défaut 30j)

7. usp_Rapport_Utilisateur: Rapport complet d'un utilisateur
   Retourne 2 résultats: infos générales + réservations futures

=========================================*/
