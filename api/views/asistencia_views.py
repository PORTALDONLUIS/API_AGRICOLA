"""Marcaciones de asistencia desde DonTec App.

Este módulo usa el mismo origen PORTAL_AEI que el marcador web.  Las marcas se
confirman en línea para que la hora, la alternancia ingreso/salida y el listado
web sean una única fuente de verdad.
"""
from datetime import datetime, timedelta
import logging

from django.db import connections, transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import UserPlantilla


logger = logging.getLogger(__name__)
PORTAL_AEI_ALIAS = "TOPICO_PORTAL_AEI"
TEMPLATE_KEY = "cartilla_asistencia"


def _has_attendance_assignment(user) -> bool:
    return UserPlantilla.objects.filter(
        user=user,
        plantilla__codigo__iexact=TEMPLATE_KEY,
        plantilla__is_active=True,
        plantilla__deleted_at__isnull=True,
        estado__iexact="Activo",
        deleted_at__isnull=True,
    ).exists()


def _assignment_error(user):
    if _has_attendance_assignment(user):
        return None
    return Response(
        {"detail": "No tienes asignada la cartilla de asistencia."}, status=403
    )


def _parse_location(data):
    # La ubicación es obligatoria: la cartilla existe precisamente para dejar
    # evidencia de dónde se realizó cada ingreso o salida.
    try:
        lat = float(data["latitud"])
        lon = float(data["longitud"])
        accuracy = float(data["precision"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 <= accuracy <= 500):
        return None
    return lat, lon, accuracy


def _clean_code(value) -> str:
    return "".join(str(value or "").strip().split())[:32]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def asistencia_sedes(request):
    denied = _assignment_error(request.user)
    if denied:
        return denied

    try:
        with connections[PORTAL_AEI_ALIAS].cursor() as cursor:
            cursor.execute(
                """
                SELECT ID_SEDE, NOMBRE_SEDE, IDEMPRESA
                FROM SEDES_MARCACIONES
                ORDER BY NOMBRE_SEDE, ID_SEDE
                """
            )
            sedes = [
                {"id": row[0], "nombre": row[1], "empresaId": row[2]}
                for row in cursor.fetchall()
            ]
    except Exception:
        logger.exception("No se pudieron obtener las sedes de asistencia")
        return Response(
            {"detail": "No se pudieron cargar las sedes. Intenta nuevamente."},
            status=503,
        )
    return Response({"items": sedes})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def asistencia_marcar(request):
    denied = _assignment_error(request.user)
    if denied:
        return denied

    code = _clean_code(request.data.get("codigoPersonal"))
    if not code:
        return Response({"detail": "Ingresa o escanea el DNI."}, status=400)

    try:
        sede_id = int(request.data.get("sedeId"))
        if sede_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return Response({"detail": "La sede seleccionada no es válida."}, status=400)

    location = _parse_location(request.data)
    if location is None:
        return Response(
            {"detail": "Captura una ubicación GPS válida antes de marcar."}, status=400
        )

    try:
        with transaction.atomic(using=PORTAL_AEI_ALIAS):
            with connections[PORTAL_AEI_ALIAS].cursor() as cursor:
                cursor.execute(
                    "SELECT ID_SEDE FROM SEDES_MARCACIONES WHERE ID_SEDE = %s",
                    [sede_id],
                )
                if cursor.fetchone() is None:
                    return Response({"detail": "La sede ya no está disponible."}, status=404)

                cursor.execute(
                    """
                    SELECT ID_PERSONAL, CODIGO_PERSONAL, NOMBRES, APELLIDOS
                    FROM PERSONAL
                    WHERE CODIGO_PERSONAL = %s AND ESTADO = 1
                    """,
                    [code],
                )
                personal = cursor.fetchone()
                if personal is None:
                    return Response(
                        {"detail": "No se encontró un trabajador activo con ese DNI."},
                        status=404,
                    )

                # La hora se obtiene de SQL Server, no del celular, para que el
                # reporte web y la app muestren exactamente la misma marcación.
                cursor.execute("SELECT GETDATE()")
                server_now = cursor.fetchone()[0]
                if not isinstance(server_now, datetime):
                    raise RuntimeError("PORTAL_AEI no devolvió una hora válida")

                cursor.execute(
                    """
                    SELECT TOP 1 ID_ASISTENCIA, HORA_INGRESO, HORA_SALIDA, LOG_FECHA
                    FROM ASISTENCIA WITH (UPDLOCK, HOLDLOCK)
                    WHERE ID_PERSONAL = %s
                      AND ID_SEDE = %s
                      AND CAST(LOG_FECHA AS DATE) = CAST(%s AS DATE)
                    ORDER BY ID_ASISTENCIA DESC
                    """,
                    [personal[0], sede_id, server_now],
                )
                previous = cursor.fetchone()
                lat, lon, accuracy = location

                action = "ingreso"
                if previous is not None and previous[2] is None:
                    previous_date = previous[3].date() if hasattr(previous[3], "date") else previous[3]
                    previous_time = previous[1]
                    previous_at = datetime.combine(previous_date, previous_time)
                    if server_now - previous_at <= timedelta(minutes=5):
                        return Response(
                            {"detail": "Ya existe un ingreso registrado en los últimos 5 minutos."},
                            status=409,
                        )
                    cursor.execute(
                        """
                        UPDATE ASISTENCIA
                        SET HORA_SALIDA = %s,
                            LATITUD_SALIDA = %s,
                            LONGITUD_SALIDA = %s,
                            PRECISION_SALIDA = %s
                        WHERE ID_ASISTENCIA = %s
                        """,
                        [server_now.time(), lat, lon, accuracy, previous[0]],
                    )
                    action = "salida"
                else:
                    if previous is not None and previous[2] is not None:
                        previous_date = previous[3].date() if hasattr(previous[3], "date") else previous[3]
                        previous_at = datetime.combine(previous_date, previous[2])
                        if server_now - previous_at <= timedelta(minutes=5):
                            return Response(
                                {"detail": "Ya existe una marcación en los últimos 5 minutos."},
                                status=409,
                            )
                    cursor.execute(
                        """
                        INSERT INTO ASISTENCIA (
                            ID_PERSONAL, ID_SEDE, HORA_INGRESO, LOG_FECHA, ESTADO,
                            LATITUD_INGRESO, LONGITUD_INGRESO, PRECISION_INGRESO
                        )
                        VALUES (%s, %s, %s, CAST(%s AS DATE), 1, %s, %s, %s)
                        """,
                        [personal[0], sede_id, server_now.time(), server_now, lat, lon, accuracy],
                    )
    except Exception:
        logger.exception("No se pudo registrar asistencia para usuario=%s", request.user.pk)
        return Response(
            {"detail": "No se pudo confirmar la marcación. Reintenta sin cambiar el DNI."},
            status=503,
        )

    full_name = " ".join(part for part in (personal[2], personal[3]) if part).strip()
    return Response(
        {
            "action": action,
            "codigoPersonal": personal[1],
            "nombreCompleto": full_name,
            "hora": server_now.strftime("%H:%M:%S"),
            "fecha": server_now.strftime("%Y-%m-%d"),
        }
    )
