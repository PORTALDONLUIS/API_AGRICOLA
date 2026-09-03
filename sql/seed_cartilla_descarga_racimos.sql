/*
  Crea o actualiza únicamente la cartilla DESCARGA RACIMOS.
  No altera muestras, campos ni asignaciones de otras cartillas.
*/
SET XACT_ABORT ON;
BEGIN TRANSACTION;

DECLARE @now datetime2 = SYSDATETIME();
DECLARE @plantillaId int;
DECLARE @plantillaDesbroteId int;

SELECT @plantillaId = PlantillaId
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_descarga_racimos';

IF @plantillaId IS NULL
BEGIN
    INSERT INTO dbo.Plantilla (
        Codigo, Nombre, Descripcion, PayloadJson, Version,
        IsActive, UpdatedAt, DeletedAt
    ) VALUES (
        N'cartilla_descarga_racimos', N'DESCARGA RACIMOS',
        N'Registro de descarga total de racimos por planta', N'{}', 1,
        1, @now, NULL
    );
    SET @plantillaId = SCOPE_IDENTITY();
END
ELSE
BEGIN
    UPDATE dbo.Plantilla
    SET Nombre = N'DESCARGA RACIMOS',
        Descripcion = N'Registro de descarga total de racimos por planta',
        Version = 1,
        IsActive = 1,
        UpdatedAt = @now,
        DeletedAt = NULL
    WHERE PlantillaId = @plantillaId;
END;

;WITH campos (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido) AS (
    SELECT * FROM (VALUES
        (N'loteId', N'Lote', N'int', N'DATOS GENERALES', 1, 1, 1, 0, 1, 1),
        (N'operario1Id', N'Operario 1', N'int', N'DATOS GENERALES', 2, 1, 1, 0, 1, 1),
        (N'operario2Id', N'Operario 2', N'int', N'DATOS GENERALES', 3, 1, 1, 0, 1, 1),
        (N'supervisorId', N'Supervisor', N'int', N'DATOS GENERALES', 4, 1, 1, 0, 1, 1),
        (N'variedad', N'Variedad', N'int', N'DATOS GENERALES', 5, 1, 1, 0, 1, 1),
        (N'hilera', N'Hilera', N'int', N'DATOS GENERALES', 6, 1, 1, 0, 1, 1),
        (N'planta', N'Planta', N'int', N'DATOS GENERALES', 7, 1, 1, 0, 1, 1),
        (N'totalRacimo', N'Total T. Racimo', N'int', N'TOTAL DE RACIMO', 8, 1, 0, 1, 0, 1),
        (N'observaciones', N'Observaciones', N'string', N'OBSERVACIONES / FOTOS', 9, 1, 0, 0, 0, 0),
        (N'foto1', N'FOTO 1', N'string', N'OBSERVACIONES / FOTOS', 10, 0, 0, 0, 0, 0),
        (N'foto2', N'FOTO 2', N'string', N'OBSERVACIONES / FOTOS', 11, 0, 0, 0, 0, 0)
    ) AS v (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido)
)
MERGE dbo.PlantillaCampo AS destino
USING campos AS origen
ON destino.PlantillaId = @plantillaId AND destino.JsonKey = origen.JsonKey
WHEN MATCHED THEN UPDATE SET
    Label = origen.Label, DataType = origen.DataType, Seccion = origen.Seccion,
    Orden = origen.Orden, EsVisibleTabla = origen.EsVisibleTabla,
    EsFiltro = origen.EsFiltro, EsKpi = origen.EsKpi,
    EsAgrupable = origen.EsAgrupable, EsRequerido = origen.EsRequerido,
    EsActivo = 1
WHEN NOT MATCHED THEN INSERT (
    PlantillaId, JsonKey, Label, DataType, Seccion, Orden,
    EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo,
    Formato, AgregacionKpi, Placeholder, Observacion
) VALUES (
    @plantillaId, origen.JsonKey, origen.Label, origen.DataType, origen.Seccion,
    origen.Orden, origen.EsVisibleTabla, origen.EsFiltro, origen.EsKpi,
    origen.EsAgrupable, origen.EsRequerido, 1, NULL, NULL, NULL, NULL
);

/* Da acceso a los mismos usuarios activos de LABOR DESBROTE, sin modificar esa cartilla. */
SELECT @plantillaDesbroteId = PlantillaId
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_labor_desbrote' AND DeletedAt IS NULL;

IF @plantillaDesbroteId IS NOT NULL
BEGIN
    UPDATE destino
    SET Estado = origen.Estado,
        UpdatedAt = @now,
        DeletedAt = NULL
    FROM dbo.UserPlantilla destino
    INNER JOIN dbo.UserPlantilla origen
        ON origen.UserId = destino.UserId
       AND origen.PlantillaId = @plantillaDesbroteId
       AND origen.DeletedAt IS NULL
    WHERE destino.PlantillaId = @plantillaId;

    INSERT INTO dbo.UserPlantilla (
        UserId, PlantillaId, Estado, AssignedAt, UpdatedAt, DeletedAt
    )
    SELECT origen.UserId, @plantillaId, origen.Estado, @now, @now, NULL
    FROM dbo.UserPlantilla origen
    WHERE origen.PlantillaId = @plantillaDesbroteId
      AND origen.DeletedAt IS NULL
      AND NOT EXISTS (
          SELECT 1 FROM dbo.UserPlantilla destino
          WHERE destino.UserId = origen.UserId
            AND destino.PlantillaId = @plantillaId
      );
END;

COMMIT TRANSACTION;

SELECT PlantillaId, Codigo, Nombre, Version, IsActive
FROM dbo.Plantilla
WHERE PlantillaId = @plantillaId;
