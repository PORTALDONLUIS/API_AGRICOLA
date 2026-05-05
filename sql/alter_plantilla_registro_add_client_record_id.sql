ALTER TABLE dbo.PlantillaRegistro
ADD ClientRecordId VARCHAR(64) NULL;
GO

UPDATE dbo.PlantillaRegistro
SET ClientRecordId = CONCAT('legacy-', UserId, '-', RegistroId)
WHERE ClientRecordId IS NULL;
GO

CREATE UNIQUE NONCLUSTERED INDEX UX_PlantillaRegistro_User_ClientRecordId
ON dbo.PlantillaRegistro (UserId, ClientRecordId)
WHERE ClientRecordId IS NOT NULL;
GO
