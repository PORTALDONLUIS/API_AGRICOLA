"""Sincronización compacta Brix Moscatel, con confirmación por revisión.

Cada UUID tiene su transacción. El resultado se entrega después del commit;
reintentar una respuesta perdida no duplica filas ni cambia la fecha de captura.
No se almacenan contextos ni datos comprimidos en las tablas de las cartillas.
"""

import json
import math

from django.db import IntegrityError, connection, transaction
from django.utils import timezone
from rest_framework import serializers

from api.models import PlantillaRegistro
from api.operational_timezone_pe import (
    fecha_ejecucion_naive_lima_desde_epoch_ms,
    instante_naive_lima_desde_utc_aware,
)
from api.services.brix_batch_codec import canonical_revision, expand_record


class BatchRecordError(ValueError):
    pass


_LOTE_ID_COLUMN_FIELD = serializers.IntegerField(
    min_value=-2147483648, max_value=2147483647, allow_null=True,
)


def _lote_id_for_column(value):
    # El selector del APK guarda el ID como texto. Interpretar sólo el valor
    # destinado a SQL, igual que el endpoint legacy, sin cambiar JSON ni hash.
    if isinstance(value, bool):
        raise BatchRecordError("invalid_lote")
    try:
        return _LOTE_ID_COLUMN_FIELD.run_validation(value)
    except serializers.ValidationError as exc:
        raise BatchRecordError("invalid_lote") from exc


def prepare_record(contexts, record, plantilla, user_id):
    """Reconstruye y verifica el snapshot antes de abrir una transacción SQL."""
    if record["payloadVersion"] != plantilla.version:
        raise BatchRecordError("payload_version_mismatch")
    try:
        payload = expand_record(contexts, record)
        actual_revision = canonical_revision(plantilla.codigo, plantilla.version, payload)
    except (ValueError, TypeError, OverflowError, UnicodeError) as exc:
        raise BatchRecordError("invalid_snapshot") from exc
    if actual_revision != record["revision"]:
        raise BatchRecordError("revision_mismatch")
    header = payload["header"]
    if isinstance(header.get("userId"), bool) or header.get("userId") != user_id:
        raise BatchRecordError("header_user_mismatch")
    if isinstance(header.get("plantillaId"), bool) or header.get("plantillaId") != plantilla.id:
        raise BatchRecordError("header_template_mismatch")
    capture_ms = header.get("fechaEjecucion")
    if isinstance(capture_ms, bool) or not isinstance(capture_ms, (int, float)):
        raise BatchRecordError("invalid_capture_date")
    try:
        capture_date = fecha_ejecucion_naive_lima_desde_epoch_ms(capture_ms)
    except (OverflowError, OSError, ValueError) as exc:
        raise BatchRecordError("invalid_capture_date") from exc
    if capture_date is None:
        raise BatchRecordError("invalid_capture_date")

    columns = {}
    for key, column in (("campaniaId", "CampaniaId"), ("loteId", "LoteId"),
                        ("lat", "Lat"), ("lon", "Lon")):
        value = record.get(key, header.get(key))
        if key == "loteId":
            value = _lote_id_for_column(value)
            if key in header and key in record and _lote_id_for_column(header[key]) != value:
                raise BatchRecordError("header_metadata_mismatch")
        elif key in header and key in record and header[key] != record[key]:
            raise BatchRecordError("header_metadata_mismatch")
        if key == "campaniaId" and value is not None:
            if not isinstance(value, str) or len(value) > 8:
                raise BatchRecordError("invalid_campania")
        if key in ("lat", "lon") and value is not None:
            limit = 90 if key == "lat" else 180
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > limit:
                raise BatchRecordError("invalid_coordinates")
        columns[column] = value
    return payload, capture_date, columns


def _result(record, status, registro=None, error=None):
    result = {
        "clientRecordId": str(record["clientRecordId"]),
        "revision": record["revision"],
        "status": status,
        "serverRegistroId": int(registro.RegistroId) if registro is not None else None,
    }
    if error:
        result["error"] = error
    return result


def _store_once(record, payload, capture_date, columns, plantilla, user_id, allow_create):
    with transaction.atomic():
        registro = (PlantillaRegistro.objects.select_for_update().filter(
            UserId=user_id, ClientRecordId=str(record["clientRecordId"]),
        ).order_by("-RegistroId").first())
        if registro is not None:
            # La baja prevalece incluso ante un móvil que lleva tiempo sin red.
            if registro.DeletedAt is not None or registro.SyncStatus == "deleted":
                result = _result(record, "deleted", registro)
            elif registro.PlantillaId != plantilla.id:
                result = _result(record, "conflict", registro, "uuid_template_conflict")
            else:
                try:
                    stored = json.loads(registro.DataJson)
                    # Versiones antiguas de +1 podían omitir estos IDs del JSON.
                    # La identidad SQL es autoritativa: completar sólo la copia
                    # para comparar un ACK perdido, sin reescribir la muestra.
                    stored_header = dict(stored.get("header") or {})
                    for key, identity in (("userId", registro.UserId),
                                          ("plantillaId", registro.PlantillaId)):
                        previous = stored_header.get(key)
                        if previous is None:
                            stored_header[key] = identity
                        elif isinstance(previous, bool) or previous != identity:
                            raise ValueError("Identidad histórica contradictoria")
                    stored = dict(stored, header=stored_header)
                    old_revision = canonical_revision(
                        plantilla.codigo, stored.get("payloadVersion", plantilla.version), stored,
                    )
                except (ValueError, TypeError, AttributeError, OverflowError, UnicodeError):
                    old_revision = None
                if old_revision == record["revision"]:
                    result = _result(record, "synced", registro)
                elif not old_revision or record.get("baseRevision") != old_revision:
                    result = _result(record, "conflict", registro, "base_revision_required")
                else:
                    # Una revisión explícita permite editar sin pisar una edición
                    # concurrente. CreatedAt y FechaRegistro nunca se reescriben.
                    now = timezone.now()
                    values = dict(columns, DataJson=json.dumps(payload, ensure_ascii=False, allow_nan=False),
                                  FechaEjecucion=capture_date, UpdatedAt=now,
                                  Estado="synced", SyncStatus="synced", SyncError=None)
                    PlantillaRegistro.objects.filter(RegistroId=registro.RegistroId).update(**values)
                    _write_lima_dates(registro.RegistroId, capture_date, now, created=False)
                    result = _result(record, "synced", registro)
        elif not allow_create:
            raise IntegrityError("UUID no encontrado después de conflicto de inserción")
        else:
            now = timezone.now()
            registro = PlantillaRegistro.objects.create(
                ClientRecordId=str(record["clientRecordId"]), PlantillaId=plantilla.id,
                UserId=user_id, FechaRegistro=now, FechaEjecucion=capture_date,
                Estado="synced", DataJson=json.dumps(payload, ensure_ascii=False, allow_nan=False),
                SyncStatus="synced", SyncError=None, SyncAttempts=0,
                ServerRegistroId=None, CreatedAt=now, UpdatedAt=now,
                DeletedAt=None, **columns
            )
            PlantillaRegistro.objects.filter(RegistroId=registro.RegistroId).update(
                ServerRegistroId=registro.RegistroId,
            )
            _write_lima_dates(registro.RegistroId, capture_date, now, created=True)
            result = _result(record, "synced", registro)
    # No devolver ACK dentro del bloque: un fallo de commit debe llegar al caller.
    return result


def _write_lima_dates(registro_id, capture_date, now, created):
    """Mismo contrato datetime2 del endpoint legacy: reloj civil de Lima."""
    local_now = instante_naive_lima_desde_utc_aware(now)
    if created:
        query = ("UPDATE dbo.PlantillaRegistro SET FechaRegistro = %s, FechaEjecucion = %s, "
                 "CreatedAt = %s, UpdatedAt = %s WHERE RegistroId = %s")
        params = [local_now, capture_date, local_now, local_now, registro_id]
    else:
        query = ("UPDATE dbo.PlantillaRegistro SET FechaEjecucion = %s, UpdatedAt = %s "
                 "WHERE RegistroId = %s")
        params = [capture_date, local_now, registro_id]
    with connection.cursor() as cursor:
        cursor.execute(query, params)


def store_record(record, payload, capture_date, columns, plantilla, user_id):
    try:
        return _store_once(record, payload, capture_date, columns, plantilla, user_id, True)
    except IntegrityError:
        # El índice único (UserId, ClientRecordId) decide la carrera de dos POST.
        # El primer atomic ya salió y se revirtió antes de consultar el ganador.
        return _store_once(record, payload, capture_date, columns, plantilla, user_id, False)
