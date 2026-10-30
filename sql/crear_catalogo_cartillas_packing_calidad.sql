/* Catálogos compartidos por las cinco cartillas Packing de Calidad. Idempotente. */
IF OBJECT_ID(N'dbo.CartillaPackingCalidadCatalogo', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CartillaPackingCalidadCatalogo (
        CatalogoId BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_CartillaPackingCalidadCatalogo PRIMARY KEY,
        Tipo NVARCHAR(32) NOT NULL,
        Valor NVARCHAR(160) NULL,
        Fundo NVARCHAR(160) NULL,
        CodigoLugarProduccion NVARCHAR(80) NULL,
        CreadoPorUserId INT NOT NULL,
        Activo BIT NOT NULL CONSTRAINT DF_CPCC_Activo DEFAULT (1),
        CreadoEn DATETIME2(0) NOT NULL CONSTRAINT DF_CPCC_CreadoEn DEFAULT (SYSDATETIME()),
        CONSTRAINT CK_CPCC_Tipo CHECK (Tipo IN (N'PLANTA', N'CONTROL_CALIDAD', N'LUGAR_PRODUCCION')),
        CONSTRAINT CK_CPCC_Contenido CHECK (
            (Tipo IN (N'PLANTA', N'CONTROL_CALIDAD') AND NULLIF(LTRIM(RTRIM(Valor)), N'') IS NOT NULL)
            OR (Tipo=N'LUGAR_PRODUCCION' AND NULLIF(LTRIM(RTRIM(Fundo)), N'') IS NOT NULL
                AND NULLIF(LTRIM(RTRIM(CodigoLugarProduccion)), N'') IS NOT NULL)
        )
    );
    CREATE INDEX IX_CPCC_Tipo_Activo ON dbo.CartillaPackingCalidadCatalogo(Tipo, Activo);
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.CartillaPackingCalidadCatalogo
               WHERE Tipo=N'PLANTA' AND UPPER(LTRIM(RTRIM(Valor)))=N'ZOOMFLIX' AND Activo=1)
    INSERT INTO dbo.CartillaPackingCalidadCatalogo
      (Tipo, Valor, CreadoPorUserId, Activo, CreadoEn)
    VALUES (N'PLANTA', N'Zoomflix', 0, 1, SYSDATETIME());
GO
