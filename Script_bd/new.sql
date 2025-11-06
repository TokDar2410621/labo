USE Prog3A25_bdSalleSense;
GO

-- Ajouter une colonne BLOB pour les photos
ALTER TABLE Donnees
ADD photoBlob VARBINARY(MAX) NULL;
GO
ALTER TABLE Donnees
DROP COLUMN photo NVARCHAR(255) NULL;
GO
-- Optionnel : garder 'photo' pour le nom/métadonnées ou la supprimer
-- Si vous voulez garder le nom du fichier :
-- ALTER TABLE Donnees ALTER COLUMN photo NVARCHAR(255) NULL;

-- Ou supprimer complètement la colonne 'photo' :
-- ALTER TABLE Donnees DROP CONSTRAINT ck_donnees_photo_format;
-- ALTER TABLE Donnees DROP COLUMN photo;