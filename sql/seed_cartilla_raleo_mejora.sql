/*
  Duplica la configuración, campos y asignaciones activas de RALEO.
  Es seguro ejecutarlo más de una vez: no duplica registros existentes.
*/
SET XACT_ABORT ON;
BEGIN TRANSACTION;

DECLARE @now datetime2 = SYSDATETIME();
DECLARE @plantillaRaleoId int;
DECLARE @plantillaRaleoMejoraId int;

SELECT @plantillaRaleoId = PlantillaId
FROM dbo.Plantilla
WHERE Codigo = N'cartilla-raleo'
  AND DeletedAt IS NULL;

IF @plantillaRaleoId IS NULL
    THROW 50001, 'No se encontró la plantilla origen cartilla-raleo.', 1;

SELECT @plantillaRaleoMejoraId = PlantillaId
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_raleo_mejora';

IF @plantillaRaleoMejoraId IS NULL
BEGIN
    INSERT INTO dbo.Plantilla (
        Codigo, Nombre, Descripcion, PayloadJson, Version,
        IsActive, UpdatedAt, DeletedAt
    )
    SELECT
        N'cartilla_raleo_mejora',
        N'RALEO MEJORA',
        N'Cartilla de raleo mejora',
        PayloadJson,
        Version,
        1,
        @now,
        NULL
    FROM dbo.Plantilla
    WHERE PlantillaId = @plantillaRaleoId;

    SET @plantillaRaleoMejoraId = SCOPE_IDENTITY();
END
ELSE
BEGIN
    UPDATE destino
    SET Nombre = N'RALEO MEJORA',
        Descripcion = N'Cartilla de raleo mejora',
        PayloadJson = origen.PayloadJson,
        Version = origen.Version,
        IsActive = 1,
        UpdatedAt = @now,
        DeletedAt = NULL
    FROM dbo.Plantilla destino
    INNER JOIN dbo.Plantilla origen
        ON origen.PlantillaId = @plantillaRaleoId
    WHERE destino.PlantillaId = @plantillaRaleoMejoraId;
END;

INSERT INTO dbo.PlantillaCampo (
    PlantillaId, JsonKey, Label, DataType, Seccion, Orden,
    EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo,
    Formato, AgregacionKpi, Placeholder, Observacion
)
SELECT
    @plantillaRaleoMejoraId,
    JsonKey, Label, DataType, Seccion, Orden,
    EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo,
    Formato, AgregacionKpi, Placeholder, Observacion
FROM dbo.PlantillaCampo origen
WHERE origen.PlantillaId = @plantillaRaleoId
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.PlantillaCampo destino
      WHERE destino.PlantillaId = @plantillaRaleoMejoraId
        AND destino.JsonKey = origen.JsonKey
  );

UPDATE destino
SET Estado = origen.Estado,
    UpdatedAt = @now,
    DeletedAt = NULL
FROM dbo.UserPlantilla destino
INNER JOIN dbo.UserPlantilla origen
    ON origen.UserId = destino.UserId
   AND origen.PlantillaId = @plantillaRaleoId
   AND origen.DeletedAt IS NULL
WHERE destino.PlantillaId = @plantillaRaleoMejoraId;

INSERT INTO dbo.UserPlantilla (
    UserId, PlantillaId, Estado, AssignedAt, UpdatedAt, DeletedAt
)
SELECT
    origen.UserId,
    @plantillaRaleoMejoraId,
    origen.Estado,
    @now,
    @now,
    NULL
FROM dbo.UserPlantilla origen
WHERE origen.PlantillaId = @plantillaRaleoId
  AND origen.DeletedAt IS NULL
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.UserPlantilla destino
      WHERE destino.UserId = origen.UserId
        AND destino.PlantillaId = @plantillaRaleoMejoraId
  );

COMMIT TRANSACTION;

SELECT PlantillaId, Codigo, Nombre, Version, IsActive
FROM dbo.Plantilla
WHERE PlantillaId = @plantillaRaleoMejoraId;
