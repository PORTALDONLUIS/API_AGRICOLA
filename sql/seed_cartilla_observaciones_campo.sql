DECLARE @now datetime2 = SYSDATETIME();

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Plantilla
    WHERE Codigo = N'cartilla_observaciones_campo'
)
BEGIN
    INSERT INTO dbo.Plantilla (
        Codigo,
        Nombre,
        Descripcion,
        PayloadJson,
        Version,
        IsActive,
        UpdatedAt,
        DeletedAt
    )
    VALUES (
        N'cartilla_observaciones_campo',
        N'Cartilla observaciones campo',
        N'Registro de observaciones en campo',
        N'{}',
        1,
        1,
        @now,
        NULL
    );
END
ELSE
BEGIN
    UPDATE dbo.Plantilla
    SET Nombre = N'Cartilla observaciones campo',
        Descripcion = N'Registro de observaciones en campo',
        Version = 1,
        IsActive = 1,
        UpdatedAt = @now,
        DeletedAt = NULL
    WHERE Codigo = N'cartilla_observaciones_campo';
END

SELECT PlantillaId, Codigo, Nombre, Version, IsActive
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_observaciones_campo';
