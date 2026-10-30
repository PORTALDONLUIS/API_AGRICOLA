"""Catálogos compartidos y ampliables para cartillas Packing de Calidad."""
from django.db import connections, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import UserPlantilla


PACKING_KEYS = (
    "cartilla_packing_recepcion_uva_calidad",
    "cartilla_packing_abastecimiento_uva_calidad",
    "cartilla_packing_linea_uva_calidad",
    "cartilla_packing_paletizado_uva_calidad",
    "cartilla_packing_ingreso_planta_uva_calidad",
)
ALLOWED_TYPES = {"PLANTA", "CONTROL_CALIDAD", "LUGAR_PRODUCCION"}


def _authorized(user):
    return UserPlantilla.objects.filter(
        user_id=user.pk,
        estado="Activo",
        deleted_at__isnull=True,
        plantilla__codigo__in=PACKING_KEYS,
        plantilla__is_active=True,
        plantilla__deleted_at__isnull=True,
    ).exists()


class PackingCalidadCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def _read(self, cursor):
        cursor.execute("""
            SELECT CatalogoId, Tipo, Valor, Fundo, CodigoLugarProduccion
            FROM dbo.CartillaPackingCalidadCatalogo
            WHERE Activo=1
            ORDER BY Tipo, Fundo, Valor, CodigoLugarProduccion
        """)
        return [dict(id=row[0], tipo=row[1], valor=row[2], fundo=row[3],
                     codigoLugarProduccion=row[4]) for row in cursor.fetchall()]

    def get(self, request):
        if not _authorized(request.user):
            return Response({"detail": "Se requiere tener asignada una cartilla Packing de Calidad."}, status=403)
        try:
            with connections["default"].cursor() as cursor:
                items = self._read(cursor)
        except Exception:
            # Permite desplegar primero la app/API; el catálogo queda vacío hasta instalar el SQL.
            return Response({"items": [], "catalogReady": False})
        return Response({"items": items, "catalogReady": True})

    def post(self, request):
        if not _authorized(request.user):
            return Response({"detail": "Se requiere tener asignada una cartilla Packing de Calidad."}, status=403)
        raw = request.data.get("items", []) if isinstance(request.data, dict) else request.data
        if not isinstance(raw, list) or len(raw) > 200:
            return Response({"detail": "La solicitud debe contener hasta 200 opciones."}, status=400)
        cleaned = []
        for item in raw:
            if not isinstance(item, dict):
                return Response({"detail": "Opción no válida."}, status=400)
            kind = str(item.get("tipo", "")).strip().upper()
            value = str(item.get("valor", "")).strip()
            fund = str(item.get("fundo", "")).strip()
            code = str(item.get("codigoLugarProduccion", "")).strip()
            if kind not in ALLOWED_TYPES:
                return Response({"detail": "Tipo de catálogo no permitido."}, status=400)
            if kind in ("PLANTA", "CONTROL_CALIDAD"):
                if not value or len(value) > 160:
                    return Response({"detail": "El nombre es obligatorio y admite hasta 160 caracteres."}, status=400)
                fund = code = ""
            else:
                if not fund or not code or len(fund) > 160 or len(code) > 80:
                    return Response({"detail": "Fundo y código son obligatorios; revise sus longitudes."}, status=400)
                value = ""
            cleaned.append((kind, value, fund, code))
        try:
            with transaction.atomic(using="default"):
                with connections["default"].cursor() as cursor:
                    for kind, value, fund, code in cleaned:
                        cursor.execute("""
                            IF NOT EXISTS (
                              SELECT 1 FROM dbo.CartillaPackingCalidadCatalogo WITH (UPDLOCK,HOLDLOCK)
                              WHERE Activo=1 AND Tipo=%s
                                AND ISNULL(Valor,'')=%s AND ISNULL(Fundo,'')=%s
                                AND ISNULL(CodigoLugarProduccion,'')=%s
                            )
                            INSERT INTO dbo.CartillaPackingCalidadCatalogo
                              (Tipo,Valor,Fundo,CodigoLugarProduccion,CreadoPorUserId,Activo,CreadoEn)
                            VALUES (%s,%s,%s,%s,%s,1,SYSDATETIME())
                        """, [kind, value, fund, code, kind, value or None, fund or None,
                              code or None, request.user.pk])
                    items = self._read(cursor)
        except Exception:
            return Response({"detail": "No se pudo guardar el catálogo. Reintente cuando vuelva la conexión."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"items": items, "catalogReady": True}, status=status.HTTP_200_OK)
