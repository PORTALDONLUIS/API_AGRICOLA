SET NOCOUNT ON;
GO

PRINT 'Procesando Plantilla Brix Moscatel';
DECLARE @PlantillaId int;
SELECT TOP (1) @PlantillaId = PlantillaId
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_brix_moscatel'
   OR Nombre = N'Plantilla Brix Moscatel';

IF @PlantillaId IS NULL
    THROW 50001, 'No se encontró la plantilla: Plantilla Brix Moscatel', 1;

;WITH src (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo, Formato, AgregacionKpi, Placeholder, Observacion) AS (
    SELECT * FROM (VALUES
        (N'loteId', N'1. Lote', N'int', N'DATOS GENERALES', 1, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'hilera', N'2. Hilera', N'int', N'DATOS GENERALES', 2, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'planta', N'3. Planta', N'int', N'DATOS GENERALES', 3, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'variedad', N'4. Variedad', N'int', N'DATOS GENERALES', 4, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'corresponde', N'5. Corresponde', N'string', N'DATOS GENERALES', 5, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'campaniaId', N'6. Campaña', N'string', N'DATOS GENERALES', 6, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'brixSsc', N'7. Brix - SSC', N'decimal', N'MEDICIÓN', 7, 1, 0, 0, 0, 1, 1, N'0.00', NULL, NULL, NULL)
    ) v (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo, Formato, AgregacionKpi, Placeholder, Observacion)
)
INSERT INTO dbo.PlantillaCampo (
    PlantillaId, JsonKey, Label, DataType, Seccion, Orden,
    EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo,
    Formato, AgregacionKpi, Placeholder, Observacion
)
SELECT
    @PlantillaId, s.JsonKey, s.Label, s.DataType, s.Seccion, s.Orden,
    s.EsVisibleTabla, s.EsFiltro, s.EsKpi, s.EsAgrupable, s.EsRequerido, s.EsActivo,
    s.Formato, s.AgregacionKpi, s.Placeholder, s.Observacion
FROM src s
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.PlantillaCampo pc
    WHERE pc.PlantillaId = @PlantillaId
      AND pc.JsonKey = s.JsonKey
);
GO

PRINT 'Procesando Plantilla Labor Desbrote';
DECLARE @PlantillaId int;
SELECT TOP (1) @PlantillaId = PlantillaId
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_labor_desbrote'
   OR Nombre = N'Plantilla Labor Desbrote';

IF @PlantillaId IS NULL
    THROW 50001, 'No se encontró la plantilla: Plantilla Labor Desbrote', 1;

;WITH src (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo, Formato, AgregacionKpi, Placeholder, Observacion) AS (
    SELECT * FROM (VALUES
        (N'loteId', N'1. Lote', N'int', N'DATOS GENERALES', 1, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'operario1Id', N'2. Operario 1', N'int', N'DATOS GENERALES', 2, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'operario2Id', N'3. Operario 2', N'int', N'DATOS GENERALES', 3, 1, 1, 0, 1, 0, 1, NULL, NULL, NULL, NULL),
        (N'supervisorId', N'4. Supervisor', N'int', N'DATOS GENERALES', 4, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'variedad', N'5. Variedad', N'int', N'DATOS GENERALES', 5, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'hilera', N'6. Hilera', N'int', N'DATOS GENERALES', 6, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'planta', N'7. Planta', N'int', N'DATOS GENERALES', 7, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'pitonBrote', N'8. Piton en brote', N'int', N'BROTES', 8, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'cargadores', N'9. Cargadores', N'int', N'BROTES', 9, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'materialViejo', N'10. Material Viejo', N'int', N'BROTES', 10, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'totalBrotes', N'11. Total Brotes', N'decimal', N'BROTES', 11, 1, 0, 0, 0, 0, 1, N'0.00', NULL, NULL, NULL),
        (N'piton', N'12. Piton', N'int', N'RACIMOS', 12, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'racimoSimple', N'13. Racimo Simple', N'int', N'RACIMOS', 13, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'racimoDoble', N'14. Racimo Doble', N'int', N'RACIMOS', 14, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'totalSimpleDoble', N'15. Total S+D', N'decimal', N'RACIMOS', 15, 1, 0, 0, 0, 0, 1, N'0.00', NULL, NULL, NULL),
        (N'racimoIndefinido', N'16. Racimo indefinido', N'int', N'RACIMOS', 16, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'observaciones', N'17. Observaciones', N'string', N'OBSERVACIONES / FOTOS', 17, 0, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'foto1', N'18. FOTO 1', N'string', N'OBSERVACIONES / FOTOS', 18, 0, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'foto2', N'19. FOTO 2', N'string', N'OBSERVACIONES / FOTOS', 19, 0, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL)
    ) v (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo, Formato, AgregacionKpi, Placeholder, Observacion)
)
INSERT INTO dbo.PlantillaCampo (
    PlantillaId, JsonKey, Label, DataType, Seccion, Orden,
    EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo,
    Formato, AgregacionKpi, Placeholder, Observacion
)
SELECT
    @PlantillaId, s.JsonKey, s.Label, s.DataType, s.Seccion, s.Orden,
    s.EsVisibleTabla, s.EsFiltro, s.EsKpi, s.EsAgrupable, s.EsRequerido, s.EsActivo,
    s.Formato, s.AgregacionKpi, s.Placeholder, s.Observacion
FROM src s
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.PlantillaCampo pc
    WHERE pc.PlantillaId = @PlantillaId
      AND pc.JsonKey = s.JsonKey
);
GO

PRINT 'Procesando Plantilla Poda';
DECLARE @PlantillaId int;
SELECT TOP (1) @PlantillaId = PlantillaId
FROM dbo.Plantilla
WHERE Codigo = N'cartilla_poda'
   OR Nombre = N'Plantilla Poda';

IF @PlantillaId IS NULL
    THROW 50001, 'No se encontró la plantilla: Plantilla Poda', 1;

;WITH src (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo, Formato, AgregacionKpi, Placeholder, Observacion) AS (
    SELECT * FROM (VALUES
        (N'loteId', N'Lote', N'int', N'DATOS GENERALES', 1, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'variedad', N'Variedad', N'int', N'DATOS GENERALES', 2, 1, 1, 0, 1, 0, 1, NULL, NULL, NULL, NULL),
        (N'podadorId', N'Podador', N'int', N'DATOS GENERALES', 3, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'supervisorId', N'Supervisor', N'int', N'DATOS GENERALES', 4, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'campaniaId', N'Campaña', N'string', N'DATOS GENERALES', 5, 1, 1, 0, 1, 0, 1, NULL, NULL, NULL, NULL),
        (N'pautaCargadores', N'Pauta cargadores', N'int', N'PAUTA', 6, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'pautaYemas', N'Pauta yemas', N'int', N'PAUTA', 7, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'hilera', N'Hilera', N'int', N'PAUTA', 8, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'planta', N'Planta', N'int', N'PAUTA', 9, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'pitones', N'N° Pitones', N'int', N'PITONES', 10, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'yemasPiton', N'Total de Yemas / Piton', N'int', N'PITONES', 11, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'cargDer', N'Cargadores Lado DER', N'int', N'N CARGADORES', 12, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'cargIzq', N'Cargadores Lado IZQ', N'int', N'N CARGADORES', 13, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'totalCargadores', N'Total cargadores', N'int', N'N CARGADORES', 14, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'debil', N'Conteo Debil', N'int', N'N CARGADORES', 15, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'normal', N'Conteo Normal', N'int', N'N CARGADORES', 16, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'vigoroso', N'Conteo Vigoroso', N'int', N'N CARGADORES', 17, 1, 0, 0, 0, 1, 1, NULL, NULL, NULL, NULL),
        (N'totalConteo', N'Total', N'int', N'N CARGADORES', 18, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'totalYemas', N'Total', N'int', N'N DE YEMAS', 19, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c1', N'C1', N'int', N'N DE YEMAS', 20, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c2', N'C2', N'int', N'N DE YEMAS', 21, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c3', N'C3', N'int', N'N DE YEMAS', 22, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c4', N'C4', N'int', N'N DE YEMAS', 23, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c5', N'C5', N'int', N'N DE YEMAS', 24, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c6', N'C6', N'int', N'N DE YEMAS', 25, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c7', N'C7', N'int', N'N DE YEMAS', 26, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c8', N'C8', N'int', N'N DE YEMAS', 27, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c9', N'C9', N'int', N'N DE YEMAS', 28, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c10', N'C10', N'int', N'N DE YEMAS', 29, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c11', N'C11', N'int', N'N DE YEMAS', 30, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c12', N'C12', N'int', N'N DE YEMAS', 31, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c13', N'C13', N'int', N'N DE YEMAS', 32, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c14', N'C14', N'int', N'N DE YEMAS', 33, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c15', N'C15', N'int', N'N DE YEMAS', 34, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c16', N'C16', N'int', N'N DE YEMAS', 35, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c17', N'C17', N'int', N'N DE YEMAS', 36, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c18', N'C18', N'int', N'N DE YEMAS', 37, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c19', N'C19', N'int', N'N DE YEMAS', 38, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c20', N'C20', N'int', N'N DE YEMAS', 39, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c21', N'C21', N'int', N'N DE YEMAS', 40, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c22', N'C22', N'int', N'N DE YEMAS', 41, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c23', N'C23', N'int', N'N DE YEMAS', 42, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c24', N'C24', N'int', N'N DE YEMAS', 43, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c25', N'C25', N'int', N'N DE YEMAS', 44, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c26', N'C26', N'int', N'N DE YEMAS', 45, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c27', N'C27', N'int', N'N DE YEMAS', 46, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c28', N'C28', N'int', N'N DE YEMAS', 47, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c29', N'C29', N'int', N'N DE YEMAS', 48, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c30', N'C30', N'int', N'N DE YEMAS', 49, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c31', N'C31', N'int', N'N DE YEMAS', 50, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c32', N'C32', N'int', N'N DE YEMAS', 51, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c33', N'C33', N'int', N'N DE YEMAS', 52, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c34', N'C34', N'int', N'N DE YEMAS', 53, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c35', N'C35', N'int', N'N DE YEMAS', 54, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c36', N'C36', N'int', N'N DE YEMAS', 55, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c37', N'C37', N'int', N'N DE YEMAS', 56, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c38', N'C38', N'int', N'N DE YEMAS', 57, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c39', N'C39', N'int', N'N DE YEMAS', 58, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c40', N'C40', N'int', N'N DE YEMAS', 59, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c41', N'C41', N'int', N'N DE YEMAS', 60, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c42', N'C42', N'int', N'N DE YEMAS', 61, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c43', N'C43', N'int', N'N DE YEMAS', 62, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c44', N'C44', N'int', N'N DE YEMAS', 63, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c45', N'C45', N'int', N'N DE YEMAS', 64, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c46', N'C46', N'int', N'N DE YEMAS', 65, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c47', N'C47', N'int', N'N DE YEMAS', 66, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c48', N'C48', N'int', N'N DE YEMAS', 67, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c49', N'C49', N'int', N'N DE YEMAS', 68, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'c50', N'C50', N'int', N'N DE YEMAS', 69, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'cargDebilMin', N'Carg. Debil < MIN', N'int', N'YEMA DEFECTUOSAS', 70, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'cargDebilMax', N'Carg. Debil > MAX', N'int', N'YEMA DEFECTUOSAS', 71, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'cargNormalMin', N'Carg. Normal < MIN', N'int', N'YEMA DEFECTUOSAS', 72, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'cargNormalMax', N'Carg. Normal > MAX', N'int', N'YEMA DEFECTUOSAS', 73, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'cargVigorosoMin', N'Carg. Vigoroso < MIN', N'int', N'YEMA DEFECTUOSAS', 74, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'cargVigorosoMax', N'Carg. Vigoroso > MAX', N'int', N'YEMA DEFECTUOSAS', 75, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'tableados', N'Tableados', N'int', N'YEMA DEFECTUOSAS', 76, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'limpieza', N'Limpieza', N'string', N'CALIFICACION', 77, 1, 1, 0, 1, 1, 1, NULL, NULL, NULL, NULL),
        (N'observacion', N'Observacion', N'string', N'CALIFICACION', 78, 0, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'foto1', N'Foto', N'string', N'CALIFICACION', 79, 0, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'finalFotos', N'Fotos Finales', N'string', N'CALIFICACION FINAL', 80, 0, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_pitones', N'N° Pitones (Final)', N'int', N'EVALUACIÓN FINAL', 81, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_yemasPiton', N'Total de Yemas / Piton (Final)', N'int', N'EVALUACIÓN FINAL', 82, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_cargDer', N'Cargadores Lado DER (Final)', N'int', N'EVALUACIÓN FINAL', 83, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_cargIzq', N'Cargadores Lado IZQ (Final)', N'int', N'EVALUACIÓN FINAL', 84, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_totalCargadores', N'Total cargadores (Final)', N'int', N'EVALUACIÓN FINAL', 85, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_debil', N'Conteo Debil (Final)', N'int', N'EVALUACIÓN FINAL', 86, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_normal', N'Conteo Normal (Final)', N'int', N'EVALUACIÓN FINAL', 87, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_vigoroso', N'Conteo Vigoroso (Final)', N'int', N'EVALUACIÓN FINAL', 88, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_totalConteo', N'Total (Final)', N'int', N'EVALUACIÓN FINAL', 89, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_totalYemas', N'Total (Final)', N'int', N'EVALUACIÓN FINAL', 90, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_cargDebilMin', N'Carg. Debil < MIN (Final)', N'int', N'EVALUACIÓN FINAL', 91, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_cargDebilMax', N'Carg. Debil > MAX (Final)', N'int', N'EVALUACIÓN FINAL', 92, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_cargNormalMin', N'Carg. Normal < MIN (Final)', N'int', N'EVALUACIÓN FINAL', 93, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_cargNormalMax', N'Carg. Normal > MAX (Final)', N'int', N'EVALUACIÓN FINAL', 94, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_cargVigorosoMin', N'Carg. Vigoroso < MIN (Final)', N'int', N'EVALUACIÓN FINAL', 95, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_cargVigorosoMax', N'Carg. Vigoroso > MAX (Final)', N'int', N'EVALUACIÓN FINAL', 96, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_tableados', N'Tableados (Final)', N'int', N'EVALUACIÓN FINAL', 97, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_limpieza', N'Limpieza (Final)', N'string', N'EVALUACIÓN FINAL', 98, 1, 1, 0, 1, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_observacion', N'Observacion (Final)', N'string', N'EVALUACIÓN FINAL', 99, 0, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c1', N'C1 (Final)', N'int', N'EVALUACIÓN FINAL', 100, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c2', N'C2 (Final)', N'int', N'EVALUACIÓN FINAL', 101, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c3', N'C3 (Final)', N'int', N'EVALUACIÓN FINAL', 102, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c4', N'C4 (Final)', N'int', N'EVALUACIÓN FINAL', 103, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c5', N'C5 (Final)', N'int', N'EVALUACIÓN FINAL', 104, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c6', N'C6 (Final)', N'int', N'EVALUACIÓN FINAL', 105, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c7', N'C7 (Final)', N'int', N'EVALUACIÓN FINAL', 106, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c8', N'C8 (Final)', N'int', N'EVALUACIÓN FINAL', 107, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c9', N'C9 (Final)', N'int', N'EVALUACIÓN FINAL', 108, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c10', N'C10 (Final)', N'int', N'EVALUACIÓN FINAL', 109, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c11', N'C11 (Final)', N'int', N'EVALUACIÓN FINAL', 110, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c12', N'C12 (Final)', N'int', N'EVALUACIÓN FINAL', 111, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c13', N'C13 (Final)', N'int', N'EVALUACIÓN FINAL', 112, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c14', N'C14 (Final)', N'int', N'EVALUACIÓN FINAL', 113, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c15', N'C15 (Final)', N'int', N'EVALUACIÓN FINAL', 114, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c16', N'C16 (Final)', N'int', N'EVALUACIÓN FINAL', 115, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c17', N'C17 (Final)', N'int', N'EVALUACIÓN FINAL', 116, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c18', N'C18 (Final)', N'int', N'EVALUACIÓN FINAL', 117, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c19', N'C19 (Final)', N'int', N'EVALUACIÓN FINAL', 118, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c20', N'C20 (Final)', N'int', N'EVALUACIÓN FINAL', 119, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c21', N'C21 (Final)', N'int', N'EVALUACIÓN FINAL', 120, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c22', N'C22 (Final)', N'int', N'EVALUACIÓN FINAL', 121, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c23', N'C23 (Final)', N'int', N'EVALUACIÓN FINAL', 122, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c24', N'C24 (Final)', N'int', N'EVALUACIÓN FINAL', 123, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c25', N'C25 (Final)', N'int', N'EVALUACIÓN FINAL', 124, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c26', N'C26 (Final)', N'int', N'EVALUACIÓN FINAL', 125, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c27', N'C27 (Final)', N'int', N'EVALUACIÓN FINAL', 126, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c28', N'C28 (Final)', N'int', N'EVALUACIÓN FINAL', 127, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c29', N'C29 (Final)', N'int', N'EVALUACIÓN FINAL', 128, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c30', N'C30 (Final)', N'int', N'EVALUACIÓN FINAL', 129, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c31', N'C31 (Final)', N'int', N'EVALUACIÓN FINAL', 130, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c32', N'C32 (Final)', N'int', N'EVALUACIÓN FINAL', 131, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c33', N'C33 (Final)', N'int', N'EVALUACIÓN FINAL', 132, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c34', N'C34 (Final)', N'int', N'EVALUACIÓN FINAL', 133, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c35', N'C35 (Final)', N'int', N'EVALUACIÓN FINAL', 134, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c36', N'C36 (Final)', N'int', N'EVALUACIÓN FINAL', 135, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c37', N'C37 (Final)', N'int', N'EVALUACIÓN FINAL', 136, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c38', N'C38 (Final)', N'int', N'EVALUACIÓN FINAL', 137, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c39', N'C39 (Final)', N'int', N'EVALUACIÓN FINAL', 138, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c40', N'C40 (Final)', N'int', N'EVALUACIÓN FINAL', 139, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c41', N'C41 (Final)', N'int', N'EVALUACIÓN FINAL', 140, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c42', N'C42 (Final)', N'int', N'EVALUACIÓN FINAL', 141, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c43', N'C43 (Final)', N'int', N'EVALUACIÓN FINAL', 142, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c44', N'C44 (Final)', N'int', N'EVALUACIÓN FINAL', 143, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c45', N'C45 (Final)', N'int', N'EVALUACIÓN FINAL', 144, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c46', N'C46 (Final)', N'int', N'EVALUACIÓN FINAL', 145, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c47', N'C47 (Final)', N'int', N'EVALUACIÓN FINAL', 146, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c48', N'C48 (Final)', N'int', N'EVALUACIÓN FINAL', 147, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c49', N'C49 (Final)', N'int', N'EVALUACIÓN FINAL', 148, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL),
        (N'final_c50', N'C50 (Final)', N'int', N'EVALUACIÓN FINAL', 149, 1, 0, 0, 0, 0, 1, NULL, NULL, NULL, NULL)
    ) v (JsonKey, Label, DataType, Seccion, Orden, EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo, Formato, AgregacionKpi, Placeholder, Observacion)
)
INSERT INTO dbo.PlantillaCampo (
    PlantillaId, JsonKey, Label, DataType, Seccion, Orden,
    EsVisibleTabla, EsFiltro, EsKpi, EsAgrupable, EsRequerido, EsActivo,
    Formato, AgregacionKpi, Placeholder, Observacion
)
SELECT
    @PlantillaId, s.JsonKey, s.Label, s.DataType, s.Seccion, s.Orden,
    s.EsVisibleTabla, s.EsFiltro, s.EsKpi, s.EsAgrupable, s.EsRequerido, s.EsActivo,
    s.Formato, s.AgregacionKpi, s.Placeholder, s.Observacion
FROM src s
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.PlantillaCampo pc
    WHERE pc.PlantillaId = @PlantillaId
      AND pc.JsonKey = s.JsonKey
);
GO
