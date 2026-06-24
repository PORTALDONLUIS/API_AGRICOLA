import json
import logging
from urllib import error, request as urllib_request

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger("api.personas")


def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


class SuperadminRequiredMixin:
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _ensure_superadmin(self, request):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 is_superuser
                FROM dbo.user_user
                WHERE id = %s
                """,
                [request.user.id],
            )
            row = cursor.fetchone()

        if not row or not bool(row[0]):
            return Response(
                {"detail": "No tienes permisos para realizar esta acción."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


class PersonaPayloadMixin:
    def _validate_payload(self, payload):
        errors = {}

        dni = str(payload.get("dni", "")).strip()
        nombre_completo = str(payload.get("nombre_completo", "")).strip()
        tipo_id = payload.get("tipo_id")
        estado = payload.get("estado", True)

        if not dni:
            errors["dni"] = ["Este campo es requerido."]
        elif not dni.isdigit() or len(dni) != 8:
            errors["dni"] = ["El DNI debe tener exactamente 8 dígitos."]

        if not nombre_completo:
            errors["nombre_completo"] = ["Este campo es requerido."]

        if tipo_id in (None, ""):
            errors["tipo_id"] = ["Este campo es requerido."]
        else:
            try:
                tipo_id = int(tipo_id)
            except (TypeError, ValueError):
                errors["tipo_id"] = ["Debe ser un número entero."]

        estado_bool = self._parse_estado(estado)
        if estado_bool is None:
            errors["estado"] = ["Debe ser true o false."]

        if errors:
            return None, errors

        if not self._persona_tipo_exists(tipo_id):
            return None, {"tipo_id": ["El tipo de persona indicado no existe o está inactivo."]}

        return {
            "dni": dni,
            "nombre_completo": nombre_completo,
            "tipo_id": tipo_id,
            "estado": estado_bool,
        }, None

    def _persona_tipo_exists(self, tipo_id):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 1
                FROM dbo.PERSONA_TIPO
                WHERE ID_PERSONA_TIPO = %s
                  AND ESTADO = 1
                """,
                [tipo_id],
            )
            return cursor.fetchone() is not None

    def _parse_estado(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            if value in (0, 1):
                return bool(value)
            return None
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ("true", "1"):
                return True
            if normalized in ("false", "0"):
                return False
        return None

    def _get_persona_response(self, persona_id, response_status):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    p.ID_PERSONA AS id,
                    p.DNI AS dni,
                    p.NOMBRE_COMPLETO AS nombre_completo,
                    p.ID_PERSONA_TIPO AS tipo_id,
                    pt.CODIGO AS tipo_codigo,
                    pt.DESCRIPCION AS tipo_descripcion,
                    p.ESTADO AS estado
                FROM dbo.PERSONA p
                INNER JOIN dbo.PERSONA_TIPO pt
                    ON pt.ID_PERSONA_TIPO = p.ID_PERSONA_TIPO
                WHERE p.ID_PERSONA = %s
                """,
                [persona_id],
            )
            row = cursor.fetchone()

        if not row:
            return Response({"detail": "Persona no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "id": row[0],
                "dni": row[1],
                "nombre_completo": row[2],
                "tipo_id": row[3],
                "tipo_codigo": row[4],
                "tipo_descripcion": row[5],
                "estado": bool(row[6]),
            },
            status=response_status,
        )


class PersonaTipoListView(SuperadminRequiredMixin, APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ID_PERSONA_TIPO AS id,
                    CODIGO AS codigo,
                    DESCRIPCION AS descripcion
                FROM dbo.PERSONA_TIPO
                WHERE ESTADO = 1
                ORDER BY DESCRIPCION
                """
            )
            items = dictfetchall(cursor)

        return Response(items, status=status.HTTP_200_OK)


class PersonaListCreateView(SuperadminRequiredMixin, PersonaPayloadMixin, APIView):
    def get(self, request):
        filters = []
        params = []

        dni = (request.query_params.get("dni") or "").strip()
        tipo_id = (request.query_params.get("tipo_id") or "").strip()
        estado_param = request.query_params.get("estado")

        if dni:
            filters.append("p.DNI = %s")
            params.append(dni)

        if tipo_id:
            filters.append("p.ID_PERSONA_TIPO = %s")
            params.append(tipo_id)

        if estado_param is not None and estado_param != "":
            estado = self._parse_estado(estado_param)
            if estado is None:
                return Response(
                    {"detail": "El filtro estado debe ser true o false."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            filters.append("p.ESTADO = %s")
            params.append(1 if estado else 0)

        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    p.ID_PERSONA AS id,
                    p.DNI AS dni,
                    p.NOMBRE_COMPLETO AS nombre_completo,
                    p.ID_PERSONA_TIPO AS tipo_id,
                    pt.CODIGO AS tipo_codigo,
                    pt.DESCRIPCION AS tipo_descripcion,
                    p.ESTADO AS estado
                FROM dbo.PERSONA p
                INNER JOIN dbo.PERSONA_TIPO pt
                    ON pt.ID_PERSONA_TIPO = p.ID_PERSONA_TIPO
                {where_clause}
                ORDER BY p.ID_PERSONA DESC
                """,
                params,
            )
            rows = dictfetchall(cursor)

        items = [
            {
                "id": row["id"],
                "dni": row["dni"],
                "nombre_completo": row["nombre_completo"],
                "tipo_id": row["tipo_id"],
                "tipo_codigo": row["tipo_codigo"],
                "tipo_descripcion": row["tipo_descripcion"],
                "estado": bool(row["estado"]),
            }
            for row in rows
        ]
        return Response(items, status=status.HTTP_200_OK)

    def post(self, request):
        forbidden = self._ensure_superadmin(request)
        if forbidden:
            return forbidden

        data, errors = self._validate_payload(request.data)
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 1
                FROM dbo.PERSONA
                WHERE DNI = %s
                """,
                [data["dni"]],
            )
            if cursor.fetchone():
                return Response(
                    {"errors": {"dni": ["Ya existe una persona registrada con ese DNI."]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cursor.execute(
                """
                INSERT INTO dbo.PERSONA (
                    DNI,
                    NOMBRE_COMPLETO,
                    ID_PERSONA_TIPO,
                    ESTADO,
                    CREATED_AT,
                    UPDATED_AT
                )
                OUTPUT INSERTED.ID_PERSONA
                VALUES (%s, %s, %s, %s, SYSUTCDATETIME(), SYSUTCDATETIME())
                """,
                [
                    data["dni"],
                    data["nombre_completo"],
                    data["tipo_id"],
                    1 if data["estado"] else 0,
                ],
            )
            persona_id = cursor.fetchone()[0]

        return self._get_persona_response(persona_id, status.HTTP_201_CREATED)

class PersonaDetailView(SuperadminRequiredMixin, PersonaPayloadMixin, APIView):
    def put(self, request, persona_id):
        forbidden = self._ensure_superadmin(request)
        if forbidden:
            return forbidden

        data, errors = self._validate_payload(request.data)
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 ID_PERSONA
                FROM dbo.PERSONA
                WHERE ID_PERSONA = %s
                """,
                [persona_id],
            )
            if not cursor.fetchone():
                return Response({"detail": "Persona no encontrada."}, status=status.HTTP_404_NOT_FOUND)

            cursor.execute(
                """
                SELECT TOP 1 1
                FROM dbo.PERSONA
                WHERE DNI = %s
                  AND ID_PERSONA <> %s
                """,
                [data["dni"], persona_id],
            )
            if cursor.fetchone():
                return Response(
                    {"errors": {"dni": ["Ya existe una persona registrada con ese DNI."]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cursor.execute(
                """
                UPDATE dbo.PERSONA
                SET DNI = %s,
                    NOMBRE_COMPLETO = %s,
                    ID_PERSONA_TIPO = %s,
                    ESTADO = %s,
                    UPDATED_AT = SYSUTCDATETIME()
                WHERE ID_PERSONA = %s
                """,
                [
                    data["dni"],
                    data["nombre_completo"],
                    data["tipo_id"],
                    1 if data["estado"] else 0,
                    persona_id,
                ],
            )

        return PersonaListCreateView()._get_persona_response(persona_id, status.HTTP_200_OK)

    def delete(self, request, persona_id):
        forbidden = self._ensure_superadmin(request)
        if forbidden:
            return forbidden

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dbo.PERSONA
                SET ESTADO = 0,
                    UPDATED_AT = SYSUTCDATETIME()
                WHERE ID_PERSONA = %s
                """,
                [persona_id],
            )
            if cursor.rowcount == 0:
                return Response({"detail": "Persona no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)

class PersonaConsultarDniView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        dni = str(request.data.get("dni", "")).strip()
        if not dni:
            return Response(
                {"success": False, "message": "El DNI es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not dni.isdigit() or len(dni) != 8:
            return Response(
                {"success": False, "message": "El DNI debe tener exactamente 8 dígitos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = getattr(settings, "APIPERU_TOKEN", "") or ""
        if not token:
            logger.error("APIPERU_TOKEN no configurado")
            return Response(
                {"success": False, "message": "El servicio de consulta DNI no está configurado."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        payload = json.dumps({"dni": dni}).encode("utf-8")
        req = urllib_request.Request(
            "https://apiperu.dev/api/dni",
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=15) as resp:
                raw_body = resp.read().decode("utf-8")
                api_data = json.loads(raw_body) if raw_body else {}
        except error.HTTPError as exc:
            raw_error = exc.read().decode("utf-8", errors="ignore")
            logger.warning("APIPERU HTTPError status=%s body=%s", exc.code, raw_error)
            return Response(
                {"success": False, "message": "No se encontró información para el DNI indicado."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Error consultando API Perú para DNI %s", dni)
            return Response(
                {"success": False, "message": "No se pudo consultar el DNI en este momento."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        nombre_completo = self._extract_nombre_completo(api_data)
        if not nombre_completo:
            return Response(
                {"success": False, "message": "No se encontró información para el DNI indicado."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": True,
                "dni": dni,
                "nombre_completo": nombre_completo,
            },
            status=status.HTTP_200_OK,
        )

    def _extract_nombre_completo(self, api_data):
        if not isinstance(api_data, dict):
            return None

        direct_root_name = (api_data.get("nombre_completo") or api_data.get("nombre") or "").strip()
        if direct_root_name:
            return direct_root_name

        data = api_data.get("data")
        if not isinstance(data, dict):
            return None

        direct_name = (data.get("nombre_completo") or data.get("nombre") or "").strip()
        if direct_name:
            return direct_name

        parts = [
            (data.get("nombres") or "").strip(),
            (data.get("apellido_paterno") or data.get("apellidoPaterno") or "").strip(),
            (data.get("apellido_materno") or data.get("apellidoMaterno") or "").strip(),
        ]
        full_name = " ".join(part for part in parts if part).strip()
        return full_name or None


class PersonaJornalUpsertView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        dni = str(request.data.get("dni", "")).strip()
        nombre_completo = str(request.data.get("nombre_completo", "")).strip().upper()

        if not dni:
            return Response(
                {"errors": {"dni": ["Este campo es requerido."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not dni.isdigit() or len(dni) != 8:
            return Response(
                {"errors": {"dni": ["El DNI debe tener exactamente 8 dígitos."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not nombre_completo:
            return Response(
                {"errors": {"nombre_completo": ["Este campo es requerido."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 ID_PERSONA_TIPO
                FROM dbo.PERSONA_TIPO
                WHERE CODIGO = %s
                  AND ESTADO = 1
                """,
                ["JOR"],
            )
            tipo_row = cursor.fetchone()
            if not tipo_row:
                return Response(
                    {"detail": "No existe el tipo de persona JOR activo."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            tipo_id = tipo_row[0]

            cursor.execute(
                """
                SELECT TOP 1 ID_PERSONA
                FROM dbo.PERSONA
                WHERE DNI = %s
                """,
                [dni],
            )
            existing = cursor.fetchone()

            if existing:
                persona_id = existing[0]
                cursor.execute(
                    """
                    UPDATE dbo.PERSONA
                    SET NOMBRE_COMPLETO = %s,
                        ID_PERSONA_TIPO = %s,
                        ESTADO = 1,
                        UPDATED_AT = SYSUTCDATETIME()
                    WHERE ID_PERSONA = %s
                    """,
                    [nombre_completo, tipo_id, persona_id],
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO dbo.PERSONA (
                        DNI,
                        NOMBRE_COMPLETO,
                        ID_PERSONA_TIPO,
                        ESTADO,
                        CREATED_AT,
                        UPDATED_AT
                    )
                    OUTPUT INSERTED.ID_PERSONA
                    VALUES (%s, %s, %s, 1, SYSUTCDATETIME(), SYSUTCDATETIME())
                    """,
                    [dni, nombre_completo, tipo_id],
                )
                persona_id = cursor.fetchone()[0]

        return PersonaPayloadMixin()._get_persona_response(persona_id, status.HTTP_200_OK)
