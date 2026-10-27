"""Protocolo compacto limitado explícitamente a Brix Moscatel y Cosecha Uva."""

import io
import logging
import uuid

from django.db import DatabaseError, transaction
from django.utils.decorators import method_decorator
from rest_framework.exceptions import APIException, ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.models import Plantilla, UserPlantilla
from api.serializers.brix_batch_serializers import BrixBatchInSerializer, BrixBatchRecordSerializer
from api.services.brix_batch_codec import BRIX_KEY, COMPACT_KEYS, MAX_BATCH_BYTES, normalize_template_key
from api.services.brix_batch_sync import BatchRecordError, prepare_record, store_record


logger = logging.getLogger("api.sync")


class BatchTooLarge(APIException):
    status_code = 413
    default_detail = "El bloque supera 512 KiB. Reduzca el bloque y reintente."
    default_code = "batch_too_large"


class BoundedBatchJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        raw = stream.read(MAX_BATCH_BYTES + 1)
        if len(raw) > MAX_BATCH_BYTES:
            raise BatchTooLarge()
        try:
            return super().parse(io.BytesIO(raw), media_type, parser_context)
        except RecursionError as exc:
            raise ParseError("JSON demasiado anidado.") from exc


def _error_result(raw, error):
    return {
        "clientRecordId": str(raw.get("clientRecordId", ""))[:64],
        "revision": str(raw.get("revision", ""))[:64],
        "status": "error", "serverRegistroId": None, "error": error,
    }


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class SyncBrixBatchView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [BoundedBatchJSONParser]

    def post(self, request):
        serializer = BrixBatchInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Bloque inválido", "errors": serializer.errors}, status=400)
        data = serializer.validated_data
        if normalize_template_key(data["key"]) not in COMPACT_KEYS:
            return Response({"detail": "Este protocolo está habilitado para Brix Moscatel y Cosecha Uva."}, status=400)
        try:
            plantilla = Plantilla.objects.get(
                id=data["plantillaId"], is_active=True, deleted_at__isnull=True,
            )
        except Plantilla.DoesNotExist:
            return Response({"detail": "Plantilla no existe"}, status=404)
        if normalize_template_key(plantilla.codigo) != normalize_template_key(data["key"]):
            return Response({"detail": "El ID no corresponde a la cartilla solicitada."}, status=400)
        if not UserPlantilla.objects.filter(
            user=request.user, plantilla=plantilla, deleted_at__isnull=True,
        ).exists():
            return Response({"detail": "Plantilla no asignada al usuario"}, status=403)
        if data["plantillaVersion"] != plantilla.version:
            return Response({"detail": "Versión de plantilla no coincide", "expected": plantilla.version}, status=409)

        seen = set()
        for raw in data["records"]:
            try:
                identity = uuid.UUID(str(raw.get("clientRecordId", "")))
            except (ValueError, TypeError, AttributeError):
                continue  # Error individual; no se escribe esta fila.
            if identity in seen:
                return Response({"detail": "UUID repetido dentro del mismo bloque."}, status=400)
            seen.add(identity)

        results = []
        unavailable = False
        for raw in data["records"]:
            record_serializer = BrixBatchRecordSerializer(data=raw)
            if not record_serializer.is_valid():
                results.append(_error_result(raw, "invalid_record"))
                continue
            record = record_serializer.validated_data
            if unavailable:
                results.append(_error_result(raw, "database_unavailable"))
                continue
            try:
                payload, capture_date, columns = prepare_record(
                    data["contexts"], record, plantilla, request.user.id,
                )
                results.append(store_record(
                    record, payload, capture_date, columns, plantilla, request.user.id,
                ))
            except BatchRecordError as exc:
                results.append(_error_result(raw, str(exc)))
            except DatabaseError as exc:
                from api.services.web_edit_conflicts import web_edit_conflict
                conflict=web_edit_conflict(exc)
                if conflict:
                    item=_error_result(raw,conflict)
                    item['status']='conflict'
                    results.append(item)
                    continue
                # Ante una caída no repetir 50 conexiones fallidas en el mismo POST.
                logger.exception("BATCH DB_ERROR user_id=%s uuid=%s", request.user.id, record["clientRecordId"])
                results.append(_error_result(raw, "database_unavailable"))
                unavailable = True
        return Response({"protocolVersion": 1, "results": results})
