from django.db import connections
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


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
                ID_LOTE,
                DESCRIPCION,
                CODIGO_LOTE,
                LOTE,
                SUB_LOTE,
                CULTIVO,
                ESTADO,
                AREA_TOTAL,
                ID_FUNDO,
                ID_VARIEDAD,
                CECO,
                Geom.STAsText() AS GEOM_WKT
            FROM dbo.LOTE
            ORDER BY ID_LOTE DESC
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

    return Response({
        "campanias": campanias,
        "lotes": lotes,
        "loteOrillas": lote_orillas,
        "variedades": variedades,
        "actividadLabores": actividad_labores,
    })
