-- Cosecha Uva v1. Ejecutar en APP_AGRICOLA después de desplegar App/API/Web.
-- Solo registra esta cartilla y su área Calidad; no asigna usuarios ni cambia muestras.
SET NOCOUNT ON;
SET XACT_ABORT ON;
IF DB_NAME()<>N'APP_AGRICOLA' THROW 51130,'Base incorrecta.',1;
BEGIN TRY
 BEGIN TRANSACTION;
 DECLARE @area int,@id int,@now datetime2=SYSDATETIME();
 IF (SELECT COUNT(*) FROM dbo.AREA WHERE UPPER(LTRIM(RTRIM(nombre_area)))=N'CALIDAD')<>1
  THROW 51131,'No se encontró un área Calidad única.',1;
 SELECT @area=id_area FROM dbo.AREA WHERE UPPER(LTRIM(RTRIM(nombre_area)))=N'CALIDAD';
 IF (SELECT COUNT(*) FROM dbo.Plantilla WHERE REPLACE(Codigo,'-','_')=N'cartilla_cosecha_uva')>1
  THROW 51132,'Hay códigos duplicados de Cosecha Uva.',1;
 SELECT @id=PlantillaId FROM dbo.Plantilla WITH (UPDLOCK,HOLDLOCK) WHERE REPLACE(Codigo,'-','_')=N'cartilla_cosecha_uva';
 IF @id IS NULL
 BEGIN
  INSERT dbo.Plantilla(Codigo,Nombre,Descripcion,PayloadJson,Version,IsActive,UpdatedAt,DeletedAt)
  VALUES(N'cartilla_cosecha_uva',N'Plantilla Cosecha Uva',N'EVALUACION DE COSECHA DE UVA-CALIDAD',N'{}',1,1,@now,NULL);
  SET @id=SCOPE_IDENTITY();
 END;
 IF EXISTS(SELECT 1 FROM dbo.Plantilla WHERE PlantillaId=@id AND Version<>1)
  THROW 51133,'La versión existente requiere revisión.',1;
 UPDATE dbo.Plantilla SET Nombre=N'Plantilla Cosecha Uva',Descripcion=N'EVALUACION DE COSECHA DE UVA-CALIDAD',IsActive=1,DeletedAt=NULL,UpdatedAt=@now WHERE PlantillaId=@id;
 IF EXISTS(SELECT 1 FROM dbo.area_plantilla WHERE id_plantilla=@id AND id_area<>@area AND is_active=1)
  THROW 51134,'La cartilla ya pertenece a otra área. Revisar.',1;
 IF NOT EXISTS(SELECT 1 FROM dbo.area_plantilla WHERE id_plantilla=@id AND id_area=@area)
  INSERT dbo.area_plantilla(id_area,id_plantilla,orden,is_active,created_at,updated_at) VALUES(@area,@id,99,1,@now,@now);
 ELSE UPDATE dbo.area_plantilla SET is_active=1,updated_at=@now WHERE id_area=@area AND id_plantilla=@id;
 DECLARE @fields TABLE(JsonKey nvarchar(100),Label nvarchar(200),DataType nvarchar(30),Seccion nvarchar(100),Orden int,Visible bit,Requerido bit);
 INSERT @fields VALUES
(N'loteId',N'Lote',N'int',N'DATOS GENERALES',1,1,1),
(N'campaniaId',N'Campaña',N'string',N'DATOS GENERALES',2,0,1),
(N'fecha',N'Fecha',N'string',N'DATOS GENERALES',3,1,1),
(N'operario',N'Operario',N'int',N'DATOS GENERALES',4,1,1),
(N'codigoLimpiador',N'Código del limpiador',N'string',N'DATOS GENERALES',5,1,0),
(N'supervisor',N'Supervisor',N'int',N'DATOS GENERALES',6,1,1),
(N'variedad',N'Variedad',N'int',N'DATOS GENERALES',7,1,0),
(N'hora',N'Hora',N'string',N'DATOS GENERALES',8,1,1),
(N'temperatura',N'Temperatura',N'string',N'DATOS GENERALES',9,1,0),
(N'conformados',N'Racimos conformados',N'int',N'CLASIFICACIÓN DE RACIMOS',10,1,0),
(N'pampanos',N'Pámpanos',N'int',N'CLASIFICACIÓN DE RACIMOS',11,1,0),
(N'semipaludos',N'Semipaludos',N'int',N'CLASIFICACIÓN DE RACIMOS',12,1,0),
(N'paludos',N'Paludos',N'int',N'CLASIFICACIÓN DE RACIMOS',13,1,0),
(N'totalRacimos',N'Total de racimos',N'int',N'CLASIFICACIÓN DE RACIMOS',14,1,0),
(N'verde',N'Verde',N'int',N'CLASIFICACIÓN DE COLOR',15,1,0),
(N'cremoso',N'Cremoso',N'int',N'CLASIFICACIÓN DE COLOR',16,1,0),
(N'ambar',N'Ámbar',N'int',N'CLASIFICACIÓN DE COLOR',17,1,0),
(N'totalRacimosColor',N'Total de racimos',N'int',N'CLASIFICACIÓN DE COLOR',18,1,0),
(N'pudricion',N'Pudrición',N'int',N'N.º DE BAYAS DEFECTUOSAS',19,1,0),
(N'partiduras',N'Partiduras',N'int',N'N.º DE BAYAS DEFECTUOSAS',20,1,0),
(N'mediaLuna',N'Media luna',N'int',N'N.º DE BAYAS DEFECTUOSAS',21,1,0),
(N'oidium',N'Oidium',N'int',N'N.º DE BAYAS DEFECTUOSAS',22,1,0),
(N'danoMecanico',N'Daño mecánico',N'int',N'N.º DE BAYAS DEFECTUOSAS',23,1,0),
(N'chanchitoBlanco',N'Chanchito blanco',N'int',N'N.º DE RACIMOS DEFECTUOSOS',24,1,0),
(N'paloNegro',N'Palo negro',N'int',N'N.º DE RACIMOS DEFECTUOSOS',25,1,0),
(N'presenciaPolvo',N'Presencia de polvo',N'int',N'N.º DE RACIMOS DEFECTUOSOS',26,1,0),
(N'presenciaAranaTela',N'Presencia de araña y tela',N'int',N'N.º DE RACIMOS DEFECTUOSOS',27,1,0),
(N'bayasAcuosas',N'Bayas acuosas',N'int',N'N.º DE RACIMOS DEFECTUOSOS',28,1,0),
(N'golpeSol',N'Golpe de sol',N'int',N'N.º DE RACIMOS DEFECTUOSOS',29,1,0),
(N'raquisLignificado',N'Raquis lignificado',N'int',N'N.º DE RACIMOS DEFECTUOSOS',30,1,0),
(N'pediceloNecrosado',N'Pedicelo necrosado',N'int',N'N.º DE RACIMOS DEFECTUOSOS',31,1,0),
(N'russet',N'Russet',N'int',N'N.º DE RACIMOS DEFECTUOSOS',32,1,0),
(N'descalibre',N'Descalibre',N'int',N'N.º DE RACIMOS DEFECTUOSOS',33,1,0),
(N'colapso',N'Colapso',N'int',N'N.º DE RACIMOS DEFECTUOSOS',34,1,0),
(N'restosVegetales',N'Presencia de restos vegetales',N'string',N'DATOS COMPLEMENTARIOS Y EVIDENCIAS',35,1,0),
(N'observaciones',N'Observaciones',N'string',N'DATOS COMPLEMENTARIOS Y EVIDENCIAS',36,1,0),
(N'foto1',N'FOTO 1',N'string',N'DATOS COMPLEMENTARIOS Y EVIDENCIAS',37,0,0),
(N'foto2',N'FOTO 2',N'string',N'DATOS COMPLEMENTARIOS Y EVIDENCIAS',38,0,0),
(N'foto3',N'FOTO 3',N'string',N'DATOS COMPLEMENTARIOS Y EVIDENCIAS',39,0,0),
(N'racimosConDefectos',N'Racimos con defectos (suma de incidencias)',N'int',N'RESUMEN DE LA MUESTRA',40,1,0),
(N'racimosSinDefectos',N'Racimos sin defectos',N'int',N'RESUMEN DE LA MUESTRA',41,1,0),
(N'porcentajeConDefectos',N'Racimos con defectos (%)',N'decimal',N'RESUMEN DE LA MUESTRA',42,1,0),
(N'porcentajeSinDefectos',N'Racimos sin defectos (%)',N'decimal',N'RESUMEN DE LA MUESTRA',43,1,0),
(N'totalBayasDefectuosas',N'Total de bayas defectuosas',N'int',N'RESUMEN DE LA MUESTRA',44,1,0),
(N'restosVegetalesSiNo',N'Restos vegetales: SI / NO',N'string',N'RESUMEN DE LA MUESTRA',45,1,0);
 INSERT dbo.PlantillaCampo(PlantillaId,JsonKey,Label,DataType,Seccion,Orden,EsVisibleTabla,EsFiltro,EsKpi,EsAgrupable,EsRequerido,EsActivo,CreatedAt,UpdatedAt)
 SELECT @id,f.JsonKey,f.Label,f.DataType,f.Seccion,f.Orden,f.Visible,0,0,0,f.Requerido,1,@now,@now FROM @fields f
 WHERE NOT EXISTS(SELECT 1 FROM dbo.PlantillaCampo c WHERE c.PlantillaId=@id AND c.JsonKey=f.JsonKey);
 UPDATE c SET Label=f.Label,DataType=f.DataType,Seccion=f.Seccion,Orden=f.Orden,EsVisibleTabla=f.Visible,EsRequerido=f.Requerido,EsActivo=1,UpdatedAt=@now
 FROM dbo.PlantillaCampo c JOIN @fields f ON c.JsonKey=f.JsonKey WHERE c.PlantillaId=@id;
 COMMIT TRANSACTION;
 SELECT @id AS PlantillaId,@area AS AreaCalidad;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
