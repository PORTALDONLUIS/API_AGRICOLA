DECLARE @now datetime2 = SYSDATETIME();

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Plantilla
    WHERE Codigo = N'cartilla_inspeccion_herramientas_epp'
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
        N'cartilla_inspeccion_herramientas_epp',
        N'Cartilla inspección de herramientas y EPP',
        N'Inspección de almacén de herramientas y EPP',
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
    SET Nombre = N'Cartilla inspección de herramientas y EPP',
        Descripcion = N'Inspección de almacén de herramientas y EPP',
        Version = 1,
        IsActive = 1,
        UpdatedAt = @now,
        DeletedAt = NULL
    WHERE Codigo = N'cartilla_inspeccion_herramientas_epp';
END

SELECT PlantillaId, Codigo, Nombre, Version, IsActive
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_inspeccion_herramientas_epp';
