/* Crea una cartilla independiente. No modifica ni copia datos de otras cartillas. */
SET XACT_ABORT ON;
BEGIN TRANSACTION;

DECLARE @now datetime2 = SYSDATETIME();
DECLARE @plantillaId int;

SELECT @plantillaId = PlantillaId
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_conteo_bayas';

IF @plantillaId IS NULL
BEGIN
    INSERT INTO dbo.Plantilla (
        Codigo, Nombre, Descripcion, PayloadJson, Version,
        IsActive, UpdatedAt, DeletedAt
    ) VALUES (
        N'cartilla_conteo_bayas', N'CONTEO DE BAYAS',
        N'Registro de conteo de bayas por racimo', N'{}', 2,
        1, @now, NULL
    );
    SET @plantillaId = SCOPE_IDENTITY();
END
ELSE
BEGIN
    UPDATE dbo.Plantilla
    SET Nombre = N'CONTEO DE BAYAS',
        Descripcion = N'Registro de conteo de bayas por racimo',
        Version = 2, IsActive = 1, UpdatedAt = @now, DeletedAt = NULL
    WHERE PlantillaId = @plantillaId;
END;

;WITH campos (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido) AS (
    SELECT * FROM (VALUES
        (N'fecha', N'Fecha', N'string', N'DATOS GENERALES', 1, 1, 1, 0, 1, 1),
        (N'loteId', N'Lote', N'int', N'DATOS GENERALES', 2, 1, 1, 0, 1, 1),
        (N'fundo', N'Fundo', N'string', N'DATOS GENERALES', 3, 1, 1, 0, 1, 1),
        (N'hilera', N'Hilera', N'int', N'DATOS GENERALES', 4, 1, 1, 0, 1, 1),
        (N'planta', N'Planta', N'int', N'DATOS GENERALES', 5, 1, 1, 0, 1, 1),
        (N'promNumeroBayas', N'Prom. N.º Bayas', N'decimal', N'PROMEDIOS', 246, 1, 0, 1, 0, 0)
    ) AS v (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido)
)
INSERT INTO dbo.PlantillaCampo (
    PlantillaId, JsonKey, Label, DataType, Seccion, Orden,
    EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo,
    Formato, AgregacionKpi, Placeholder, Observacion
)
SELECT @plantillaId, c.JsonKey, c.Label, c.DataType, c.Seccion, c.Orden,
       c.EsVisibleTabla, c.EsFiltro, c.EsKpi, c.EsAgrupable, c.EsRequerido, 1,
       NULL, NULL, NULL, NULL
FROM campos c
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.PlantillaCampo pc
    WHERE pc.PlantillaId = @plantillaId AND pc.JsonKey = c.JsonKey
);

-- Solo actualiza metadatos de esta cartilla; no modifica muestras guardadas.
DELETE pc
FROM dbo.PlantillaCampo pc
WHERE pc.PlantillaId = @plantillaId
  AND (pc.JsonKey = N'promLongitud' OR pc.JsonKey LIKE N'longitudCm%');

UPDATE pc
SET Label = N'Prom. N.º Bayas', DataType = N'decimal', Seccion = N'PROMEDIOS',
    Orden = 246, EsVisibleTabla = 1, EsFiltro = 0, EsKpi = 1,
    EsAgrupable = 0, EsRequerido = 0, EsActivo = 1
FROM dbo.PlantillaCampo pc
WHERE pc.PlantillaId = @plantillaId
  AND pc.JsonKey = N'promNumeroBayas';

DECLARE @racimo int = 1;
WHILE @racimo <= 120
BEGIN
    DECLARE @ordenBase int = 6 + ((@racimo - 1) * 2);
    DECLARE @seccion nvarchar(50) = CONCAT(N'RACIMO ', @racimo);

    UPDATE pc
    SET Label = CASE
            WHEN pc.JsonKey = CONCAT(N'tipoRacimo', @racimo) THEN N'Tipo Rac.'
            ELSE N'N.º Bayas'
        END,
        DataType = CASE
            WHEN pc.JsonKey = CONCAT(N'tipoRacimo', @racimo) THEN N'string'
            ELSE N'int'
        END,
        Seccion = @seccion,
        Orden = CASE
            WHEN pc.JsonKey = CONCAT(N'tipoRacimo', @racimo) THEN @ordenBase
            ELSE @ordenBase + 1
        END,
        EsVisibleTabla = 1, EsFiltro = 0, EsKpi = 0, EsAgrupable = 0,
        EsRequerido = 0, EsActivo = 1
    FROM dbo.PlantillaCampo pc
    WHERE pc.PlantillaId = @plantillaId
      AND pc.JsonKey IN (CONCAT(N'tipoRacimo', @racimo), CONCAT(N'numeroBayas', @racimo));

    INSERT INTO dbo.PlantillaCampo (
        PlantillaId, JsonKey, Label, DataType, Seccion, Orden,
        EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo,
        Formato, AgregacionKpi, Placeholder, Observacion
    )
    SELECT @plantillaId, v.JsonKey, v.Label, v.DataType, @seccion, v.Orden,
           1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL
    FROM (VALUES
        (CONCAT(N'tipoRacimo', @racimo), N'Tipo Rac.', N'string', @ordenBase),
        (CONCAT(N'numeroBayas', @racimo), N'N.º Bayas', N'int', @ordenBase + 1)
    ) AS v (JsonKey, Label, DataType, Orden)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.PlantillaCampo pc
        WHERE pc.PlantillaId = @plantillaId AND pc.JsonKey = v.JsonKey
    );

    SET @racimo += 1;
END;

COMMIT TRANSACTION;

SELECT PlantillaId, Codigo, Nombre, Version, IsActive
FROM dbo.Plantilla
WHERE PlantillaId = @plantillaId;
