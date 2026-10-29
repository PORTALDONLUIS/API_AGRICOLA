-- Cartillas TIC transaccionales: catálogo/asignación existentes. Solo DCULQUI.
-- No inserta muestras ni duplica equipos. El inventario permanece en PORTAL_AEI.
SET NOCOUNT ON;
SET XACT_ABORT ON;
IF DB_NAME() <> N'APP_AGRICOLA' THROW 51240, 'Base incorrecta.', 1;
BEGIN TRY
 BEGIN TRANSACTION;
 DECLARE @usuario int,@area int,@ahora datetime2=SYSUTCDATETIME();
 SELECT @usuario=id FROM dbo.user_user WHERE username=N'DCULQUI' AND active=1;
 IF @usuario IS NULL THROW 51241,'DCULQUI no existe o no está activo.',1;
 SELECT @area=id_area FROM dbo.AREA WHERE UPPER(LTRIM(RTRIM(nombre_area))) IN (N'TI',N'TIC');
 IF @area IS NULL THROW 51242,'No existe el área TI/TIC. Revisar sin crear duplicados.',1;
 DECLARE @cartillas TABLE(Codigo nvarchar(50),Nombre nvarchar(150),Descripcion nvarchar(400),Flujo nvarchar(40));
 INSERT @cartillas VALUES
 (N'cartilla_tic_equipos',N'Plantilla TIC Equipos',N'REGISTRO Y CONTROL DE EQUIPOS TIC',N'equipos'),
 (N'cartilla_tic_entregas',N'Plantilla TIC Entregas',N'ASIGNACIÓN Y ENTREGA DE EQUIPOS TIC',N'entregas'),
 (N'cartilla_tic_devoluciones',N'Plantilla TIC Devoluciones',N'DEVOLUCIÓN Y RECEPCIÓN DE EQUIPOS TIC',N'devoluciones'),
 (N'cartilla_tic_informes_tecnicos',N'Plantilla TIC Informes técnicos',N'FALLAS, MANTENIMIENTO Y REPARACIÓN DE EQUIPOS TIC',N'informes'),
 (N'cartilla_tic_ampliaciones',N'Plantilla TIC Ampliaciones',N'AMPLIACIÓN Y REEMPLAZO DE COMPONENTES TIC',N'ampliaciones'),
 (N'cartilla_tic_trabajadores',N'Plantilla TIC Trabajadores',N'PADRÓN DE TRABAJADORES Y RESPONSABLES TIC',N'trabajadores'),
 (N'cartilla_tic_recursos',N'Plantilla TIC Consumibles y servicios',N'CONTROL DE CONSUMIBLES, LÍNEAS Y SERVICIOS TIC',N'recursos'),
 (N'cartilla_tic_reportes',N'Plantilla TIC Reportes',N'REPORTES E INFORMES CORPORATIVOS DE ASIGNACIONES TIC',N'reportes');
 IF EXISTS(SELECT 1 FROM dbo.Plantilla p JOIN @cartillas c ON p.Codigo=c.Codigo WHERE p.Version<>1)
  THROW 51243,'Existe una versión distinta de una cartilla TIC. Revisar antes de actualizar.',1;
 INSERT dbo.Plantilla(Codigo,Nombre,Descripcion,PayloadJson,Version,IsActive,UpdatedAt,DeletedAt)
 SELECT c.Codigo,c.Nombre,c.Descripcion,N'{"domain":"tic_asignaciones","flow":"'+c.Flujo+N'","transactional":true,"requiresGeo":false}',1,1,@ahora,NULL
 FROM @cartillas c WHERE NOT EXISTS(SELECT 1 FROM dbo.Plantilla p WITH(UPDLOCK,HOLDLOCK) WHERE p.Codigo=c.Codigo);
 UPDATE p SET Nombre=c.Nombre,Descripcion=c.Descripcion,PayloadJson=N'{"domain":"tic_asignaciones","flow":"'+c.Flujo+N'","transactional":true,"requiresGeo":false}',IsActive=1,DeletedAt=NULL,UpdatedAt=@ahora
 FROM dbo.Plantilla p JOIN @cartillas c ON p.Codigo=c.Codigo;
 INSERT dbo.area_plantilla(id_area,id_plantilla,orden,is_active,created_at,updated_at)
 SELECT @area,p.PlantillaId,100,1,@ahora,@ahora FROM dbo.Plantilla p JOIN @cartillas c ON p.Codigo=c.Codigo
 WHERE NOT EXISTS(SELECT 1 FROM dbo.area_plantilla a WHERE a.id_area=@area AND a.id_plantilla=p.PlantillaId);
 UPDATE a SET is_active=1,updated_at=@ahora FROM dbo.area_plantilla a JOIN dbo.Plantilla p ON p.PlantillaId=a.id_plantilla JOIN @cartillas c ON c.Codigo=p.Codigo WHERE a.id_area=@area;
 INSERT dbo.UserPlantilla(UserId,PlantillaId,Estado,AssignedAt,UpdatedAt,DeletedAt)
 SELECT @usuario,p.PlantillaId,N'Activo',@ahora,@ahora,NULL FROM dbo.Plantilla p JOIN @cartillas c ON p.Codigo=c.Codigo
 WHERE NOT EXISTS(SELECT 1 FROM dbo.UserPlantilla u WITH(UPDLOCK,HOLDLOCK) WHERE u.UserId=@usuario AND u.PlantillaId=p.PlantillaId);
 UPDATE u SET Estado=N'Activo',DeletedAt=NULL,UpdatedAt=@ahora FROM dbo.UserPlantilla u JOIN dbo.Plantilla p ON u.PlantillaId=p.PlantillaId JOIN @cartillas c ON p.Codigo=c.Codigo WHERE u.UserId=@usuario;
 COMMIT TRANSACTION;
 SELECT p.PlantillaId,p.Codigo FROM dbo.Plantilla p JOIN @cartillas c ON p.Codigo=c.Codigo ORDER BY p.PlantillaId;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
