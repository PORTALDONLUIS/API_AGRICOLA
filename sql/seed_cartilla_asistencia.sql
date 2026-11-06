-- Ejecutar una sola vez en APP_AGRICOLA para que la cartilla aparezca en DonTec.
-- Después asignarla a los usuarios autorizados mediante UserPlantilla.
-- No modifica PORTAL_AEI ni las tablas PERSONAL, ASISTENCIA o SEDES_MARCACIONES.
IF NOT EXISTS (SELECT 1 FROM dbo.Plantilla WHERE Codigo = 'cartilla_asistencia')
BEGIN
    INSERT INTO dbo.Plantilla (
        Codigo, Nombre, Descripcion, PayloadJson, Version, IsActive, UpdatedAt, DeletedAt
    )
    VALUES (
        'cartilla_asistencia',
        'Cartilla Asistencia',
        'Marcación de ingreso y salida con sede, GPS y DNI.',
        '{}',
        1,
        1,
        GETDATE(),
        NULL
    );
END;

-- Ejemplo de asignación. Reemplaza 123 por el UserId autorizado antes de ejecutar.
-- INSERT INTO dbo.UserPlantilla (UserId, PlantillaId, Estado, AssignedAt, UpdatedAt, DeletedAt)
-- SELECT 123, PlantillaId, 'Activo', GETDATE(), GETDATE(), NULL
-- FROM dbo.Plantilla
-- WHERE Codigo = 'cartilla_asistencia'
--   AND NOT EXISTS (
--       SELECT 1 FROM dbo.UserPlantilla up
--       WHERE up.UserId = 123 AND up.PlantillaId = dbo.Plantilla.PlantillaId
--   );
