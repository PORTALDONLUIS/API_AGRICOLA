-- Registra las cinco cartillas Packing Uva de Calidad y las asigna inicialmente a DCULQUI.
-- Idempotente, transaccional y limitado a catálogo, vínculo Calidad y asignación de plantillas.
-- No crea tablas ni modifica muestras existentes. Ejecutar en APP_AGRICOLA tras desplegar API/App/Web.
SET NOCOUNT ON;
SET XACT_ABORT ON;
IF DB_NAME()<>N'APP_AGRICOLA' THROW 51310,'Base incorrecta; se requiere APP_AGRICOLA.',1;
BEGIN TRY
 BEGIN TRANSACTION;
 DECLARE @area int,@usuario int,@now datetime2=SYSDATETIME();
 IF (SELECT COUNT(*) FROM dbo.AREA WHERE UPPER(LTRIM(RTRIM(nombre_area)))=N'CALIDAD')<>1
  THROW 51311,'No se encontró un área Calidad única.',1;
 SELECT @area=id_area FROM dbo.AREA WHERE UPPER(LTRIM(RTRIM(nombre_area)))=N'CALIDAD';
 IF NOT EXISTS(SELECT 1 FROM dbo.AREA WHERE id_area=@area AND mostrar_en_cartillas_agricolas=1)
  THROW 51312,'Calidad no está habilitada en Cartillas Agrícolas.',1;
 SELECT @usuario=id FROM dbo.user_user WHERE username=N'DCULQUI' AND active=1;
 IF @usuario IS NULL THROW 51313,'DCULQUI no existe o no está activo.',1;
 DECLARE @templates TABLE(Codigo nvarchar(100) PRIMARY KEY,Nombre nvarchar(200),Descripcion nvarchar(400));
 INSERT @templates VALUES
 (N'cartilla_packing_recepcion_uva_calidad',N'Plantilla Packing Recepcion uva-CALIDAD',N'Recepción de uva para Calidad'),
 (N'cartilla_packing_abastecimiento_uva_calidad',N'Plantilla Packing Abastecimiento uva- CALIDAD',N'Abastecimiento de uva para Calidad'),
 (N'cartilla_packing_linea_uva_calidad',N'Plantilla Packing Linea uva- CALIDAD',N'Control de línea de uva para Calidad'),
 (N'cartilla_packing_paletizado_uva_calidad',N'Plantilla Packing Paletizado uva- CALIDAD',N'Paletizado de uva para Calidad'),
 (N'cartilla_packing_ingreso_planta_uva_calidad',N'Plantilla Packing Ingreso producto planta uva- CALIDAD',N'Ingreso de producto a planta de uva para Calidad');
 IF EXISTS(SELECT 1 FROM dbo.Plantilla p JOIN @templates t ON p.Codigo=t.Codigo WHERE p.Version<>1)
  THROW 51314,'Una plantilla existente tiene versión distinta; no se sobrescribió.',1;
 IF EXISTS(SELECT Codigo FROM dbo.Plantilla WHERE Codigo IN (SELECT Codigo FROM @templates) GROUP BY Codigo HAVING COUNT(*)>1)
  THROW 51315,'Hay códigos duplicados de plantilla; revisar antes de continuar.',1;
 INSERT dbo.Plantilla(Codigo,Nombre,Descripcion,PayloadJson,Version,IsActive,UpdatedAt,DeletedAt)
 SELECT t.Codigo,t.Nombre,t.Descripcion,N'{"headerKeys":["loteId","campaniaId"],"payloadVersion":1}',1,1,@now,NULL
 FROM @templates t WHERE NOT EXISTS(SELECT 1 FROM dbo.Plantilla p WITH(UPDLOCK,HOLDLOCK) WHERE p.Codigo=t.Codigo);
 UPDATE p SET Nombre=t.Nombre,Descripcion=t.Descripcion,IsActive=1,DeletedAt=NULL,UpdatedAt=@now
 FROM dbo.Plantilla p JOIN @templates t ON p.Codigo=t.Codigo;
 DECLARE @ids TABLE(PlantillaId int PRIMARY KEY,Codigo nvarchar(100));
 INSERT @ids SELECT p.PlantillaId,p.Codigo FROM dbo.Plantilla p JOIN @templates t ON t.Codigo=p.Codigo;
 IF (SELECT COUNT(*) FROM @ids)<>5 THROW 51316,'No se encontraron exactamente las cinco plantillas.',1;
 IF EXISTS(SELECT 1 FROM dbo.area_plantilla ap JOIN @ids i ON i.PlantillaId=ap.id_plantilla WHERE ap.id_area<>@area AND ap.is_active=1)
  THROW 51317,'Alguna cartilla ya está vinculada a otra área activa.',1;
 IF EXISTS(SELECT ap.id_plantilla FROM dbo.area_plantilla ap JOIN @ids i ON i.PlantillaId=ap.id_plantilla WHERE ap.id_area=@area GROUP BY ap.id_plantilla HAVING COUNT(*)>1)
  THROW 51318,'Hay vínculos duplicados con Calidad.',1;
 UPDATE ap SET is_active=1,updated_at=@now FROM dbo.area_plantilla ap JOIN @ids i ON i.PlantillaId=ap.id_plantilla WHERE ap.id_area=@area AND ap.is_active=0;
 INSERT dbo.area_plantilla(id_area,id_plantilla,orden,is_active,created_at,updated_at)
 SELECT @area,i.PlantillaId,99,1,@now,@now FROM @ids i WHERE NOT EXISTS(SELECT 1 FROM dbo.area_plantilla ap WHERE ap.id_area=@area AND ap.id_plantilla=i.PlantillaId);
 DECLARE @fields TABLE(Codigo nvarchar(100),JsonKey nvarchar(100),Label nvarchar(200),DataType nvarchar(30),Seccion nvarchar(100),Orden int,Visible bit,Filtro bit,Agrupable bit,Requerido bit);
 INSERT @fields(Codigo,JsonKey,Label,DataType,Seccion,Orden,Visible,Filtro,Agrupable,Requerido) VALUES
(N'cartilla_packing_recepcion_uva_calidad',N'loteId',N'Lote',N'int',N'DATOS GENERALES',1,1,1,1,1),
(N'cartilla_packing_recepcion_uva_calidad',N'campaniaId',N'Campaña',N'string',N'DATOS GENERALES',2,0,0,0,1),
(N'cartilla_packing_recepcion_uva_calidad',N'fecha',N'Fecha',N'string',N'DATOS GENERALES',3,1,1,0,1),
(N'cartilla_packing_recepcion_uva_calidad',N'variedad',N'Variedad',N'int',N'DATOS GENERALES',4,1,1,1,1),
(N'cartilla_packing_recepcion_uva_calidad',N'nroGuia',N'N.° de guía',N'string',N'DATOS GENERALES',5,1,0,0,1),
(N'cartilla_packing_recepcion_uva_calidad',N'totalPaletPorGuia',N'Total de palets por guía',N'int',N'DATOS GENERALES',6,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'sector',N'Sector',N'string',N'DATOS GENERALES',7,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'numeroJabas',N'N.° de jabas',N'int',N'DATOS GENERALES',8,1,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'pesoTotalJabas',N'Peso total de jabas (kg)',N'decimal',N'DATOS GENERALES',9,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'pesoNeto',N'Peso neto (kg)',N'decimal',N'DATOS GENERALES',10,1,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'pesoBaya',N'Peso de baya (kg)',N'decimal',N'DATOS GENERALES',11,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'pesoPorJaba',N'Peso por jaba (kg)',N'decimal',N'DATOS GENERALES',12,1,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'brix',N'Brix',N'string',N'DATOS GENERALES',13,1,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'temperatura',N'Temperatura (°C)',N'decimal',N'DATOS GENERALES',14,1,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'pudricion',N'Pudrición',N'decimal',N'PRINCIPALES DEFECTOS',15,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'deshidratacion',N'Deshidratación',N'int',N'PRINCIPALES DEFECTOS',16,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'danoMecanico',N'Daño mecánico',N'decimal',N'PRINCIPALES DEFECTOS',17,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'chanchitoBlanco',N'Chanchito blanco',N'int',N'PRINCIPALES DEFECTOS',18,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'oidium',N'Oidium',N'decimal',N'PRINCIPALES DEFECTOS',19,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'paloNegro',N'Palo negro',N'decimal',N'PRINCIPALES DEFECTOS',20,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'presenciaPolvo',N'Presencia de polvo',N'int',N'PRINCIPALES DEFECTOS',21,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'presenciaArana',N'Presencia de araña',N'int',N'PRINCIPALES DEFECTOS',22,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'bayasAcuosas',N'Bayas acuosas',N'int',N'PRINCIPALES DEFECTOS',23,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'golpeSol',N'Golpe de sol',N'int',N'PRINCIPALES DEFECTOS',24,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'russet',N'Russet',N'decimal',N'PRINCIPALES DEFECTOS',25,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'descalibre',N'Descalibre',N'int',N'PRINCIPALES DEFECTOS',26,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'observaciones',N'Observaciones',N'string',N'OBSERVACIÓN',27,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'pesoMinimoRacimo',N'Peso mínimo de racimo (kg)',N'decimal',N'DATOS COMPLEMENTARIOS',28,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'pesoMaximoRacimo',N'Peso máximo de racimo (kg)',N'decimal',N'DATOS COMPLEMENTARIOS',29,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'foto1',N'Foto 1',N'string',N'EVIDENCIAS FOTOGRÁFICAS',30,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'foto2',N'Foto 2',N'string',N'EVIDENCIAS FOTOGRÁFICAS',31,0,0,0,0),
(N'cartilla_packing_recepcion_uva_calidad',N'foto3',N'Foto 3',N'string',N'EVIDENCIAS FOTOGRÁFICAS',32,0,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'loteId',N'Lote',N'int',N'DATOS GENERALES',33,1,1,1,1),
(N'cartilla_packing_abastecimiento_uva_calidad',N'campaniaId',N'Campaña',N'string',N'DATOS GENERALES',34,0,0,0,1),
(N'cartilla_packing_abastecimiento_uva_calidad',N'fecha',N'Fecha',N'string',N'DATOS GENERALES',35,1,1,0,1),
(N'cartilla_packing_abastecimiento_uva_calidad',N'nroGuia',N'N.° de guía',N'string',N'DATOS GENERALES',36,1,0,0,1),
(N'cartilla_packing_abastecimiento_uva_calidad',N'cantidadPaletIngresado',N'Cantidad de palets ingresados',N'int',N'DATOS GENERALES',37,1,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'pesoPaletIngresado',N'Peso de palets ingresados (kg)',N'decimal',N'DATOS GENERALES',38,1,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'variedad',N'Variedad',N'int',N'DATOS GENERALES',39,1,1,1,1),
(N'cartilla_packing_abastecimiento_uva_calidad',N'horaInicioGasificado',N'Hora de inicio de gasificado',N'string',N'CONTROL DE GASIFICADO Y PRE FRÍO',40,0,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'horaFinGasificado',N'Hora de fin de gasificado',N'string',N'CONTROL DE GASIFICADO Y PRE FRÍO',41,0,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'horaPreFrio',N'Hora de pre frío',N'string',N'CONTROL DE GASIFICADO Y PRE FRÍO',42,0,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'horaSalidaPreFrio',N'Hora de salida de pre frío',N'string',N'CONTROL DE GASIFICADO Y PRE FRÍO',43,0,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'observaciones',N'Observaciones',N'string',N'OBSERVACIÓN',44,0,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'foto1',N'Foto 1',N'string',N'EVIDENCIAS FOTOGRÁFICAS',45,0,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'foto2',N'Foto 2',N'string',N'EVIDENCIAS FOTOGRÁFICAS',46,0,0,0,0),
(N'cartilla_packing_abastecimiento_uva_calidad',N'foto3',N'Foto 3',N'string',N'EVIDENCIAS FOTOGRÁFICAS',47,0,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'loteId',N'Lote',N'int',N'DATOS GENERALES',48,1,1,1,1),
(N'cartilla_packing_linea_uva_calidad',N'campaniaId',N'Campaña',N'string',N'DATOS GENERALES',49,0,0,0,1),
(N'cartilla_packing_linea_uva_calidad',N'nroGuia',N'N.° de guía',N'string',N'DATOS GENERALES',50,1,0,0,1),
(N'cartilla_packing_linea_uva_calidad',N'fecha',N'Fecha',N'string',N'DATOS GENERALES',51,1,1,0,1),
(N'cartilla_packing_linea_uva_calidad',N'variedad',N'Variedad',N'int',N'DATOS GENERALES',52,1,1,1,1),
(N'cartilla_packing_linea_uva_calidad',N'sector',N'Sector',N'string',N'DATOS GENERALES',53,1,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'horaInicio',N'Hora de inicio',N'string',N'DATOS GENERALES',54,1,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'horaFinal',N'Hora final',N'string',N'DATOS GENERALES',55,1,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'presentacion',N'Presentación',N'string',N'DATOS GENERALES',56,0,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'pautas',N'Pautas',N'string',N'DATOS GENERALES',57,0,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'observaciones',N'Observaciones',N'string',N'OBSERVACIÓN',58,0,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'foto1',N'Foto 1',N'string',N'EVIDENCIAS FOTOGRÁFICAS',59,0,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'foto2',N'Foto 2',N'string',N'EVIDENCIAS FOTOGRÁFICAS',60,0,0,0,0),
(N'cartilla_packing_linea_uva_calidad',N'foto3',N'Foto 3',N'string',N'EVIDENCIAS FOTOGRÁFICAS',61,0,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'loteId',N'Lote',N'int',N'DATOS GENERALES',62,1,1,1,1),
(N'cartilla_packing_paletizado_uva_calidad',N'campaniaId',N'Campaña',N'string',N'DATOS GENERALES',63,0,0,0,1),
(N'cartilla_packing_paletizado_uva_calidad',N'nroGuia',N'N.° de guía',N'string',N'DATOS GENERALES',64,1,0,0,1),
(N'cartilla_packing_paletizado_uva_calidad',N'variedad',N'Variedad',N'int',N'DATOS GENERALES',65,1,1,1,1),
(N'cartilla_packing_paletizado_uva_calidad',N'horaInicio',N'Hora de inicio',N'string',N'DATOS GENERALES',66,0,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'numeroPalletsCompletos',N'N.° de pallets completos',N'int',N'DATOS GENERALES',67,1,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'numeroPuchos',N'N.° de puchos',N'int',N'DATOS GENERALES',68,1,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'numeroCalibre',N'N.° de calibre',N'int',N'PRESENTACIÓN',69,0,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'calibre',N'Calibre',N'string',N'DATOS GENERALES',70,0,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'numeroCajas',N'N.° de cajas',N'int',N'PRESENTACIÓN',71,1,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'horaIngresoCamaraFrio',N'Hora de ingreso a cámara de frío',N'string',N'PRESENTACIÓN',72,0,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'observaciones',N'Observaciones',N'string',N'OBSERVACIÓN',73,0,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'foto1',N'Foto 1',N'string',N'EVIDENCIAS FOTOGRÁFICAS',74,0,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'foto2',N'Foto 2',N'string',N'EVIDENCIAS FOTOGRÁFICAS',75,0,0,0,0),
(N'cartilla_packing_paletizado_uva_calidad',N'foto3',N'Foto 3',N'string',N'EVIDENCIAS FOTOGRÁFICAS',76,0,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'loteId',N'Lote',N'int',N'DATOS GENERALES',77,1,1,1,1),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'campaniaId',N'Campaña',N'string',N'DATOS GENERALES',78,0,0,0,1),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'planta',N'Planta',N'string',N'DATOS INICIALES',79,1,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'controlCalidad',N'Control de calidad',N'string',N'DATOS INICIALES',80,0,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'codigoLugarProduccion',N'Código de lugar de producción',N'string',N'DATOS INICIALES',81,0,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'cosecha',N'Fecha de cosecha',N'string',N'FECHAS',82,0,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'proceso',N'Fecha de proceso',N'string',N'FECHAS',83,1,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'serieGuia',N'Serie de guía',N'string',N'DATOS DE LA GUÍA',84,0,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'nroGuia',N'N.° de guía',N'string',N'DATOS DE LA GUÍA',85,1,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'variedad',N'Variedad',N'int',N'DETALLE',86,1,1,1,1),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'tipo',N'Tipo',N'string',N'DATOS DE ENVASES COSECHADOS',87,1,1,1,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'cantidad',N'Cantidad',N'int',N'DATOS DE ENVASES COSECHADOS',88,1,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'pesoKg',N'Peso (kg)',N'decimal',N'DATOS DE ENVASES COSECHADOS',89,1,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'kilosIngresados',N'Kilos ingresados',N'decimal',N'DATOS CAMPO (KG)',90,1,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'observaciones',N'Observaciones',N'string',N'OBSERVACIÓN',91,0,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'foto1',N'Foto 1',N'string',N'EVIDENCIAS FOTOGRÁFICAS',92,0,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'foto2',N'Foto 2',N'string',N'EVIDENCIAS FOTOGRÁFICAS',93,0,0,0,0),
(N'cartilla_packing_ingreso_planta_uva_calidad',N'foto3',N'Foto 3',N'string',N'EVIDENCIAS FOTOGRÁFICAS',94,0,0,0,0);
 INSERT dbo.PlantillaCampo(PlantillaId,JsonKey,Label,DataType,Seccion,Orden,EsVisibleTabla,EsFiltro,EsKpi,EsAgrupable,EsRequerido,EsActivo,CreatedAt,UpdatedAt)
 SELECT i.PlantillaId,f.JsonKey,f.Label,f.DataType,f.Seccion,f.Orden,f.Visible,f.Filtro,0,f.Agrupable,f.Requerido,1,@now,@now
 FROM @fields f JOIN @ids i ON i.Codigo=f.Codigo
 WHERE NOT EXISTS(SELECT 1 FROM dbo.PlantillaCampo c WHERE c.PlantillaId=i.PlantillaId AND c.JsonKey=f.JsonKey);
 UPDATE c SET Label=f.Label,DataType=f.DataType,Seccion=f.Seccion,Orden=f.Orden,EsVisibleTabla=f.Visible,EsFiltro=f.Filtro,EsKpi=0,EsAgrupable=f.Agrupable,EsRequerido=f.Requerido,EsActivo=1,UpdatedAt=@now
 FROM dbo.PlantillaCampo c JOIN @ids i ON i.PlantillaId=c.PlantillaId JOIN @fields f ON f.Codigo=i.Codigo AND f.JsonKey=c.JsonKey;
 INSERT dbo.UserPlantilla(UserId,PlantillaId,Estado,AssignedAt,UpdatedAt,DeletedAt)
 SELECT @usuario,i.PlantillaId,N'Activo',@now,@now,NULL FROM @ids i
 WHERE NOT EXISTS(SELECT 1 FROM dbo.UserPlantilla u WITH(UPDLOCK,HOLDLOCK) WHERE u.UserId=@usuario AND u.PlantillaId=i.PlantillaId);
 UPDATE u SET Estado=N'Activo',DeletedAt=NULL,UpdatedAt=@now FROM dbo.UserPlantilla u JOIN @ids i ON i.PlantillaId=u.PlantillaId WHERE u.UserId=@usuario;
 IF (SELECT COUNT(*) FROM dbo.area_plantilla ap JOIN @ids i ON i.PlantillaId=ap.id_plantilla WHERE ap.id_area=@area AND ap.is_active=1)<>5
  THROW 51319,'La verificación de vínculos con Calidad falló.',1;
 IF (SELECT COUNT(*) FROM dbo.UserPlantilla u JOIN @ids i ON i.PlantillaId=u.PlantillaId WHERE u.UserId=@usuario AND u.Estado=N'Activo' AND u.DeletedAt IS NULL)<>5
  THROW 51320,'La verificación de asignación a DCULQUI falló.',1;
 COMMIT TRANSACTION;
 SELECT i.Codigo,i.PlantillaId FROM @ids i ORDER BY i.Codigo;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
