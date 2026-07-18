DECLARE @now datetime2 = SYSDATETIME();

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Plantilla
    WHERE Codigo = N'cartilla_registro_motorizado_seguridad'
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
        N'cartilla_registro_motorizado_seguridad',
        N'Cartilla registro motorizado seguridad',
        N'Registro motorizado de seguridad',
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
    SET Nombre = N'Cartilla registro motorizado seguridad',
        Descripcion = N'Registro motorizado de seguridad',
        Version = 1,
        IsActive = 1,
        UpdatedAt = @now,
        DeletedAt = NULL
    WHERE Codigo = N'cartilla_registro_motorizado_seguridad';
END

SELECT PlantillaId, Codigo, Nombre, Version, IsActive
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_registro_motorizado_seguridad';
