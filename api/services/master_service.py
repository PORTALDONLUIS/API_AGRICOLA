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

    return Response({
        "campanias": campanias,
        "lotes": lotes,
        "loteOrillas": lote_orillas,
        "variedades": variedades,
    })