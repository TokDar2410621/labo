USE Prog3A25_bdSalleSense;
GO

-- Supprimer les tables si elles existent (dans le bon ordre à cause des dépendances)

IF OBJECT_ID('Evenement', 'U') IS NOT NULL DROP TABLE Evenement;
IF OBJECT_ID('Donnees', 'U') IS NOT NULL DROP TABLE Donnees;
IF OBJECT_ID('Capteur', 'U') IS NOT NULL DROP TABLE Capteur;
IF OBJECT_ID('Reservation', 'U') IS NOT NULL DROP TABLE Reservation;
IF OBJECT_ID('Salle', 'U') IS NOT NULL DROP TABLE Salle;
IF OBJECT_ID('Blacklist', 'U') IS NOT NULL DROP TABLE Blacklist;
IF OBJECT_ID('Utilisateur', 'U') IS NOT NULL DROP TABLE Utilisateur;
GO

-- Utilisateur
CREATE TABLE Utilisateur (
    idUtilisateur_PK        INT IDENTITY(1,1)          PRIMARY KEY,
    pseudo                  NVARCHAR(80)               NOT NULL,
    courriel                NVARCHAR(120)              NOT NULL,
    motDePasse              NVARCHAR(255)              NOT NULL
);
GO

-- Blacklist
CREATE TABLE Blacklist (
    idBlacklist_PK      INT             IDENTITY(1,1) PRIMARY KEY,
    idUtilisateur       INT             NOT NULL
);
GO

-- Salle
CREATE TABLE Salle (
    idSalle_PK              INT IDENTITY(1,1)   PRIMARY KEY,
    numero                  NVARCHAR(40)        NOT NULL,
    capaciteMaximale        INT                 NOT NULL
);
GO

-- Reservation
CREATE TABLE Reservation (
    idReservation_PK            INT IDENTITY(1,1)              PRIMARY KEY,
    heureDebut                  DATETIME2                      NOT NULL,
    heureFin                    DATETIME2                      NOT NULL,
    noSalle                     INT                            NOT NULL,
    noPersonne                  INT                            NOT NULL,
    nombrePersonne              INT                            NOT NULL
);
GO

-- Capteur
CREATE TABLE Capteur (
    idCapteur_PK                INT IDENTITY(1,1)              PRIMARY KEY,
    nom                         NVARCHAR(80)                   NOT NULL,
    type                        NVARCHAR(40)                   NOT NULL
);
GO

-- Donnees
CREATE TABLE Donnees (
    idDonnee_PK                 INT IDENTITY(1,1)           PRIMARY KEY,
    dateHeure                   DATETIME2                   NOT NULL,
    idCapteur                   INT                         NOT NULL,
    mesure                      FLOAT                       NULL,
    photoBlob                   VARBINARY(MAX)              NULL,
    noSalle                     INT                         NOT NULL

);
GO

-- Evenement
CREATE TABLE Evenement (
    idEvenement_PK              INT IDENTITY(1,1)           PRIMARY KEY,
    type                        NVARCHAR(60)                NOT NULL,
    idDonnee                    INT NOT                     NULL,
    description                 NVARCHAR(MAX)               NULL

);
GO
