USE Prog3A25_bdSalleSense;
IF COL_LENGTH('dbo.Utilisateur','mdp_salt') IS NULL
  ALTER TABLE dbo.Utilisateur ADD mdp_salt VARBINARY(16) NULL;
IF COL_LENGTH('dbo.Utilisateur','mdp_hash') IS NULL
  ALTER TABLE dbo.Utilisateur ADD mdp_hash VARBINARY(32) NULL;
GO
CREATE OR ALTER PROCEDURE dbo.usp_Utilisateur_Create
  @Pseudo       NVARCHAR(100),
  @Courriel     NVARCHAR(255),
  @MotDePasse   NVARCHAR(4000),
  @UserId INT OUTPUT
AS
BEGIN
  SET NOCOUNT ON;
  -- Un seul compte par courriel
  IF EXISTS (SELECT 1 FROM dbo.Utilisateur WHERE courriel = @Courriel)
    SET @UserId =  -1;
  DECLARE @salt VARBINARY(16) = CRYPT_GEN_RANDOM(16);
  DECLARE @hash VARBINARY(32) = HASHBYTES('SHA2_256',
      @salt + CONVERT(VARBINARY(4000), @MotDePasse)
  );
  INSERT INTO dbo.Utilisateur(pseudo, courriel, mdp_hash, mdp_salt)
  VALUES (@Pseudo, @Courriel, @hash, @salt);
  SET @UserId =  SCOPE_IDENTITY();  -- succès → id utilisateur
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_Utilisateur_Login
  @Courriel   NVARCHAR(255),
  @MotDePasse NVARCHAR(4000),
  @UserId INT OUTPUT
AS
BEGIN
  SET NOCOUNT ON;
  DECLARE
    @id   INT,
    @salt VARBINARY(16),
    @hash VARBINARY(32);
  SELECT
    @id   = idUtilisateur_PK,
    @salt = mdp_salt,
    @hash = mdp_hash
  FROM dbo.Utilisateur
  WHERE courriel = @Courriel;
  IF @id IS NULL
    SET @UserId = -1;  -- courriel inconnu
  DECLARE @hashTentative VARBINARY(32) =
    HASHBYTES('SHA2_256', @salt + CONVERT(VARBINARY(4000), @MotDePasse));
  IF @hashTentative = @hash
    SET @UserId =  @id;   -- succès
  ELSE
    SET @UserId =  -1;    -- mauvais mot de passe
END;
GO