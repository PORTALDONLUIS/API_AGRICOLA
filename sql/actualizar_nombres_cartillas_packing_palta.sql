-- Actualiza los nombres visibles de dos cartillas Packing de palta.
-- Cambia solo Plantilla.Nombre; conserva códigos, permisos, campos y registros.
SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'APP_AGRICOLA'
    THROW 51330, 'Base incorrecta; se requiere APP_AGRICOLA.', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @nombres TABLE (
        Codigo nvarchar(100) PRIMARY KEY,
        NombreNuevo nvarchar(150) NOT NULL
    );

    INSERT @nombres (Codigo, NombreNuevo)
    VALUES
        (N'cartilla-packing-recepcion', N'Plantilla Packing Recepción palta-CALIDAD'),
        (N'cartilla-packing-cajas', N'Plantilla Packing Cajas Clasificadas palta-CALIDAD');

    IF (SELECT COUNT(*)
        FROM dbo.Plantilla p
        JOIN @nombres n ON n.Codigo = p.Codigo) <> 2
        THROW 51331, 'No se encontraron exactamente las dos cartillas esperadas; no se hicieron cambios.', 1;

    UPDATE p
       SET p.Nombre = n.NombreNuevo,
           p.UpdatedAt = SYSDATETIME()
    FROM dbo.Plantilla p
    JOIN @nombres n ON n.Codigo = p.Codigo;

    IF (SELECT COUNT(*)
        FROM dbo.Plantilla p
        JOIN @nombres n ON n.Codigo = p.Codigo
        WHERE p.Nombre = n.NombreNuevo) <> 2
        THROW 51332, 'La verificación de nombres falló; se revierten los cambios.', 1;

    COMMIT TRANSACTION;

    SELECT Codigo, Nombre
    FROM dbo.Plantilla
    WHERE Codigo IN (N'cartilla-packing-recepcion', N'cartilla-packing-cajas')
    ORDER BY Codigo;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
