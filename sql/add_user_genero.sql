-- Avatar por género para usuarios de la aplicación.
-- H = hombre, M = mujer. NULL conserva un avatar neutro.
IF COL_LENGTH('dbo.user_user', 'genero') IS NULL
BEGIN
    ALTER TABLE dbo.user_user
    ADD genero CHAR(1) NULL;
END;
GO

-- Evita valores distintos de H y M, manteniendo permitido NULL mientras
-- se completa la información de usuarios existentes.
IF NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE name = 'CK_user_user_genero'
      AND parent_object_id = OBJECT_ID('dbo.user_user')
)
BEGIN
    ALTER TABLE dbo.user_user
    ADD CONSTRAINT CK_user_user_genero
    CHECK (genero IS NULL OR genero IN ('H', 'M'));
END;
GO
