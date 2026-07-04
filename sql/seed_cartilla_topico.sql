DECLARE @now datetime2 = SYSDATETIME();

IF NOT EXISTS (
    SELECT 1
    FROM dbo.Plantilla
    WHERE Codigo = N'catilla-topico'
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
        N'catilla-topico',
        N'Cartilla tópico',
        N'Registro de atención en tópico',
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
    SET Nombre = N'Cartilla tópico',
        Descripcion = N'Registro de atención en tópico',
        Version = 1,
        IsActive = 1,
        UpdatedAt = @now,
        DeletedAt = NULL
    WHERE Codigo = N'catilla-topico';
END

SELECT PlantillaId, Codigo, Nombre, Version, IsActive
FROM dbo.Plantilla
WHERE Codigo = N'catilla-topico';
