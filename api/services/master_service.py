import logging

from django.db import connections
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger("api")


def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def bootstrap(request):
    # Ajusta el alias si tu DB no se llama "default"
    # Ej: connections["sqlserver"]
    conn = connections["default"]
    donluis_conn = connections["DONLUIS"]
    topico_portal_conn = connections["TOPICO_PORTAL_AEI"]

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT
                ID_CAMPANIA,
                DESCRIPCION
            FROM dbo.CAMPANIA
            ORDER BY ID_CAMPANIA DESC
        """)
        campanias = dictfetchall(cursor)

        cursor.execute("""
            SELECT
                l.ID_LOTE,
                l.DESCRIPCION,
                l.CODIGO_LOTE,
                l.LOTE,
                l.SUB_LOTE,
                l.CULTIVO,
                l.ESTADO,
                l.AREA_TOTAL,
                l.ID_FUNDO,
                f.DESCRIPCION AS FUNDO_DESCRIPCION,
                l.ID_VARIEDAD,
                l.CECO,
                l.Geom.STAsText() AS GEOM_WKT
            FROM dbo.LOTE l
            LEFT JOIN dbo.FUNDO f ON f.ID_FUNDO = l.ID_FUNDO
            ORDER BY l.ID_LOTE DESC
        """)
        lotes = dictfetchall(cursor)

        # Orillas por lote (BRIX)
        lote_orillas = []
        for table_name in ("dbo.LOTE_ORILLA_CATALOGO", "dbo.LOTE_ORILLAS", "dbo.LOTE_ORILLAS_CATALOGO"):
            try:
                cursor.execute(f"""
                    SELECT
                        ID_LOTE_ORILLA,
                        ID_LOTE,
                        ORILLA_CODIGO,
                        ORILLA_LABEL,
                        PERIMETRAL_DESCRIPCION,
                        ACTIVO
                    FROM {table_name}
                    WHERE ACTIVO = 1
                    ORDER BY ID_LOTE, ORILLA_CODIGO
                """)
                lote_orillas = dictfetchall(cursor)
                break
            except Exception:
                continue

        # Variedades (catálogo maestro)
        variedades = []
        variedad_queries = (
            """
                SELECT
                    ID,
                    DESCRIPCION,
                    FECHA_CREACION
                FROM dbo.VARIEDAD
                ORDER BY ID DESC
            """,
            """
                SELECT
                    ID_VARIEDAD AS ID,
                    DESCRIPCION,
                    FECHA_CREACION
                FROM dbo.VARIEDAD
                ORDER BY ID_VARIEDAD DESC
            """,
            """
                SELECT
                    ID,
                    DESCRIPCION,
                    FECHA_CREACION
                FROM dbo.VARIEDADES
                ORDER BY ID DESC
            """,
        )
        for q in variedad_queries:
            try:
                cursor.execute(q)
                variedades = dictfetchall(cursor)
                break
            except Exception:
                continue

    actividad_labores = []
    actividad_labor_queries = (
        """
            WITH ranked AS (
                SELECT
                    LTRIM(RTRIM(idempresa)) AS idempresa,
                    LTRIM(RTRIM(idactividad)) AS actividadId,
                    LTRIM(RTRIM(dsc_actividad)) AS actividadNombre,
                    LTRIM(RTRIM(idlabor)) AS laborId,
                    LTRIM(RTRIM(dsc_labor)) AS laborNombre,
                    TRY_CONVERT(float, cantidad_periodo) AS rendimiento,
                    LTRIM(RTRIM(medida_periodo)) AS medida,
                    TRY_CONVERT(float, precio_periodo) AS costo,
                    periodo,
                    ROW_NUMBER() OVER (
                        PARTITION BY idempresa, idactividad, idlabor
                        ORDER BY periodo DESC, fecha_inicio DESC
                    ) AS rn
                FROM dbo.vst_costo_rendimiento_actividad_labor
                WHERE idactividad IS NOT NULL
                  AND idlabor IS NOT NULL
                  AND dsc_actividad IS NOT NULL
                  AND dsc_labor IS NOT NULL
            )
            SELECT
                idempresa,
                actividadId,
                actividadNombre,
                laborId,
                laborNombre,
                rendimiento,
                medida,
                costo,
                periodo
            FROM ranked
            WHERE rn = 1
            ORDER BY actividadNombre, laborNombre
        """,
        """
            WITH ranked AS (
                SELECT
                    LTRIM(RTRIM(idempresa)) AS idempresa,
                    LTRIM(RTRIM(idactividad)) AS actividadId,
                    LTRIM(RTRIM(dsc_actividad)) AS actividadNombre,
                    LTRIM(RTRIM(idlabor)) AS laborId,
                    LTRIM(RTRIM(dsc_labor)) AS laborNombre,
                    TRY_CONVERT(float, cantidad_periodo) AS rendimiento,
                    LTRIM(RTRIM(medida_periodo)) AS medida,
                    TRY_CONVERT(float, precio_periodo) AS costo,
                    periodo,
                    ROW_NUMBER() OVER (
                        PARTITION BY idempresa, idactividad, idlabor
                        ORDER BY periodo DESC, fecha_inicio DESC
                    ) AS rn
                FROM vst_costo_rendimiento_actividad_labor
                WHERE idactividad IS NOT NULL
                  AND idlabor IS NOT NULL
                  AND dsc_actividad IS NOT NULL
                  AND dsc_labor IS NOT NULL
            )
            SELECT
                idempresa,
                actividadId,
                actividadNombre,
                laborId,
                laborNombre,
                rendimiento,
                medida,
                costo,
                periodo
            FROM ranked
            WHERE rn = 1
            ORDER BY actividadNombre, laborNombre
        """,
    )
    with donluis_conn.cursor() as cursor:
        for q in actividad_labor_queries:
            try:
                cursor.execute(q)
                actividad_labores = dictfetchall(cursor)
                break
            except Exception:
                continue

    topico_empresas = []
    topico_pacientes = []
    with donluis_conn.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT
                    LTRIM(RTRIM(CAST(IDEMPRESA AS varchar(30)))) AS idEmpresa,
                    LTRIM(RTRIM(CAST(RAZON_SOCIAL AS varchar(250)))) AS razonSocial,
                    LTRIM(RTRIM(CAST(RUC AS varchar(30)))) AS ruc,
                    LTRIM(RTRIM(CAST(nombre_corto AS varchar(120)))) AS nombreCorto,
                    CASE
                        WHEN ESTADO IS NULL THEN 1
                        WHEN CAST(ESTADO AS varchar(20)) IN ('1', 'A', 'ACTIVO', 'True', 'true') THEN 1
                        ELSE 0
                    END AS activo
                FROM dbo.EMPRESAS
                ORDER BY IDEMPRESA
            """)
            topico_empresas = dictfetchall(cursor)
        except Exception:
            logger.exception("Error sincronizando tópico: empresas")
            topico_empresas = []

        try:
            cursor.execute("""
                WITH ranked_personal AS (
                    SELECT
                        p.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY p.IDCODIGOGENERAL
                            ORDER BY p.FECHA_INICIOPLANILLA DESC, p.FECHACREACION DESC
                        ) AS rn
                    FROM dbo.PERSONAL p
                    WHERE p.IDCODIGOGENERAL IS NOT NULL
                      AND (
                        p.ESTADO IS NULL
                        OR UPPER(LTRIM(RTRIM(CAST(p.ESTADO AS varchar(30))))) NOT IN (
                            '0', 'I', 'INACTIVO', 'FALSE', 'BAJA', 'CESADO'
                        )
                      )
                )
                SELECT
                    LTRIM(RTRIM(CAST(pg.IDCODIGOGENERAL AS varchar(30)))) AS idCodigoGeneral,
                    LTRIM(RTRIM(CAST(pg.NRODOCUMENTO AS varchar(30)))) AS dni,
                    LTRIM(RTRIM(CONCAT(
                        COALESCE(CAST(pg.A_PATERNO AS varchar(120)), ''),
                        ' ',
                        COALESCE(CAST(pg.A_MATERNO AS varchar(120)), ''),
                        ', ',
                        COALESCE(CAST(pg.NOMBRES AS varchar(160)), '')
                    ))) AS nombreCompleto,
                    LTRIM(RTRIM(CAST(pg.SEXO AS varchar(30)))) AS genero,
                    LTRIM(RTRIM(CAST(p.IDEMPRESA AS varchar(30)))) AS idEmpresa,
                    LTRIM(RTRIM(CAST(e.RAZON_SOCIAL AS varchar(250)))) AS empresa,
                    LTRIM(RTRIM(CAST(p.IDPLANILLA AS varchar(30)))) AS idPlanilla,
                    LTRIM(RTRIM(CAST(pl.DESCRIPCION AS varchar(160)))) AS planilla,
                    LTRIM(RTRIM(CAST(p.IDCARGO AS varchar(30)))) AS idCargo,
                    LTRIM(RTRIM(CAST(cp.DESCRIPCION AS varchar(160)))) AS cargo,
                    LTRIM(RTRIM(CAST(p.IDGRUPOTRABAJO AS varchar(30)))) AS idGrupoTrabajo,
                    LTRIM(RTRIM(CAST(gt.DESCRIPCION AS varchar(160)))) AS area,
                    1 AS activo
                FROM dbo.PERSONAL_GENERAL pg
                LEFT JOIN ranked_personal p
                    ON p.IDCODIGOGENERAL = pg.IDCODIGOGENERAL
                   AND p.rn = 1
                LEFT JOIN dbo.EMPRESAS e
                    ON e.IDEMPRESA = p.IDEMPRESA
                LEFT JOIN dbo.PLANILLA pl
                    ON pl.IDEMPRESA = p.IDEMPRESA
                   AND pl.IDPLANILLA = p.IDPLANILLA
                LEFT JOIN dbo.CARGOS_PERSONAL cp
                    ON cp.IDEMPRESA = p.IDEMPRESA
                   AND cp.IDCARGO = p.IDCARGO
                LEFT JOIN dbo.GRUPO_TRABAJO gt
                    ON gt.IDGRUPOTRABAJO = p.IDGRUPOTRABAJO
                WHERE pg.IDCODIGOGENERAL IS NOT NULL
                  AND LTRIM(RTRIM(COALESCE(CAST(pg.NOMBRES AS varchar(160)), ''))) <> ''
                  AND (
                    pg.ESTADO IS NULL
                    OR UPPER(LTRIM(RTRIM(CAST(pg.ESTADO AS varchar(30))))) NOT IN (
                        '0', 'I', 'INACTIVO', 'FALSE', 'BAJA', 'CESADO'
                    )
                  )
                ORDER BY pg.A_PATERNO, pg.A_MATERNO, pg.NOMBRES
            """)
            topico_pacientes = dictfetchall(cursor)
            if not topico_pacientes:
                cursor.execute("""
                    SELECT
                        LTRIM(RTRIM(CAST(pg.IDCODIGOGENERAL AS varchar(30)))) AS idCodigoGeneral,
                        LTRIM(RTRIM(CAST(pg.NRODOCUMENTO AS varchar(30)))) AS dni,
                        LTRIM(RTRIM(CONCAT(
                            COALESCE(CAST(pg.A_PATERNO AS varchar(120)), ''),
                            ' ',
                            COALESCE(CAST(pg.A_MATERNO AS varchar(120)), ''),
                            ', ',
                            COALESCE(CAST(pg.NOMBRES AS varchar(160)), '')
                        ))) AS nombreCompleto,
                        LTRIM(RTRIM(CAST(pg.SEXO AS varchar(30)))) AS genero,
                        NULL AS idEmpresa,
                        NULL AS empresa,
                        NULL AS idPlanilla,
                        NULL AS planilla,
                        NULL AS idCargo,
                        NULL AS cargo,
                        NULL AS idGrupoTrabajo,
                        NULL AS area,
                        1 AS activo
                    FROM dbo.PERSONAL_GENERAL pg
                    WHERE pg.IDCODIGOGENERAL IS NOT NULL
                      AND LTRIM(RTRIM(COALESCE(CAST(pg.NOMBRES AS varchar(160)), ''))) <> ''
                      AND (
                        pg.ESTADO IS NULL
                        OR UPPER(LTRIM(RTRIM(CAST(pg.ESTADO AS varchar(30))))) NOT IN (
                            '0', 'I', 'INACTIVO', 'FALSE', 'BAJA', 'CESADO'
                        )
                      )
                    ORDER BY pg.A_PATERNO, pg.A_MATERNO, pg.NOMBRES
                """)
                topico_pacientes = dictfetchall(cursor)
        except Exception:
            logger.exception("Error sincronizando tópico: pacientes")
            topico_pacientes = []

    topico_consultas = []
    topico_medicamentos = []
    try:
        with topico_portal_conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    Codigo AS codigo,
                    Descripcion AS descripcion,
                    TipoAtencion AS tipoAtencion,
                    1 AS activo
                FROM dbo.TopicoConsultas
                ORDER BY Descripcion
            """)
            topico_consultas = dictfetchall(cursor)

            cursor.execute("""
                SELECT
                    Codigo AS codigo,
                    Medicamento AS medicamento,
                    TipoPresentacion AS tipoPresentacion,
                    Lugar AS lugar,
                    1 AS activo
                FROM dbo.TopicoMedicamentos
                ORDER BY Medicamento
            """)
            topico_medicamentos = dictfetchall(cursor)
    except Exception:
        logger.exception("Error sincronizando tópico desde TOPICO_PORTAL_AEI. Se intentará con default.")
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        Codigo AS codigo,
                        Descripcion AS descripcion,
                        TipoAtencion AS tipoAtencion,
                        1 AS activo
                    FROM dbo.TopicoConsultas
                    ORDER BY Descripcion
                """)
                topico_consultas = dictfetchall(cursor)

                cursor.execute("""
                    SELECT
                        Codigo AS codigo,
                        Medicamento AS medicamento,
                        TipoPresentacion AS tipoPresentacion,
                        Lugar AS lugar,
                        1 AS activo
                    FROM dbo.TopicoMedicamentos
                    ORDER BY Medicamento
                """)
                topico_medicamentos = dictfetchall(cursor)
        except Exception:
            logger.exception("Error sincronizando tópico desde default.")
            topico_consultas = []
            topico_medicamentos = []

    return Response({
        "campanias": campanias,
        "lotes": lotes,
        "loteOrillas": lote_orillas,
        "variedades": variedades,
        "actividadLabores": actividad_labores,
        "topicoEmpresas": topico_empresas,
        "topicoPacientes": topico_pacientes,
        "topicoConsultas": topico_consultas,
        "topicoMedicamentos": topico_medicamentos,
    })
