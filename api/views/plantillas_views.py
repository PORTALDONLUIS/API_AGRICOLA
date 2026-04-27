import json
import logging
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db import connection
from django.utils import timezone
from rest_framework import status

from api.models import UserPlantilla, Plantilla, PlantillaRegistro
from api.operational_timezone_pe import (
    fecha_ejecucion_naive_lima_desde_epoch_ms,
    instante_naive_lima_desde_utc_aware,
)
from api.serializers.registros_sync_serializers import SyncRegistroInSerializer
from api.services.plantillas_service import obtener_plantillas_asignadas
from api.serializers.plantillas_serializers import PlantillaAssignedSerializer
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser, FormParser

logger = logging.getLogger("api.sync")


def _delete_previous_fotos_for_slot(storage, folder: str, slot: int) -> None:
    """
    Elimina en almacenamiento los archivos previos del mismo slot dentro de [folder]:
    - legado: foto_{slot}.jpg
    - actual: s{slot}_*.jpg (nombre único por subida)
    """
    try:
        _, files = storage.listdir(folder)
    except (NotImplementedError, OSError, FileNotFoundError):
        return
    legacy = f"foto_{slot}.jpg"
    prefix = f"s{slot}_"
    exts = (".jpg", ".jpeg", ".png", ".webp")
    for name in files:
        if not isinstance(name, str):
            continue
        lower = name.lower()
        if name == legacy or (
            name.startswith(prefix) and any(lower.endswith(e) for e in exts)
        ):
            try:
                storage.delete(f"{folder}/{name}")
            except OSError:
                pass


# class PlantillasAsignadasView(APIView):
#     authentication_classes = [DebugJWTAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         return Response({"ok": True, "user": request.user.username})


class PlantillasAsignadasView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        auth = JWTAuthentication()
        res = auth.authenticate(request)
        print("JWT authenticate =>", res)

        since = request.query_params.get("since")
        data = obtener_plantillas_asignadas(request.user, since)

        serializer = PlantillaAssignedSerializer(
            data["plantillas"],
            many=True,
            context={"assignment_by_plantilla": data["assignment_by_plantilla"]},
        )

        return Response({
            "serverTime": data["serverTime"],
            "items": serializer.data,
            "deleted": data["deleted"],
        })

class SyncRegistroView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.debug(
            "SYNC START user_id=%s remote_addr=%s content_type=%s",
            getattr(request.user, "id", None),
            request.META.get("REMOTE_ADDR"),
            request.META.get("CONTENT_TYPE"),
        )
        # s = SyncRegistroInSerializer(data=request.data)
        # s.is_valid(raise_exception=True)
        s = SyncRegistroInSerializer(data=request.data)
        if not s.is_valid():
            logger.warning("SYNC INVALID payload=%s errors=%s", request.data, s.errors)
            return Response({"errors": s.errors, "received": request.data}, status=400)
        data = s.validated_data

        template_key = data["templateKey"]
        payload_version = data.get("payloadVersion", 1)
        payload = data["dataJson"]
        header = payload.get("header") or {}

        logger.debug(
            "SYNC VALID template=%s payload_version=%s campania=%s lote=%s header_keys=%s body_keys=%s",
            template_key,
            payload_version,
            data.get("campaniaId"),
            data.get("loteId"),
            list(header.keys()) if isinstance(header, dict) else [],
            list((payload.get("body") or {}).keys()) if isinstance(payload.get("body"), dict) else [],
        )

        # 1) Plantilla por código (OJO: usar nombres del MODELO: codigo/is_active/deleted_at)
        try:
            plantilla = Plantilla.objects.get(
                codigo=template_key,
                is_active=True,
                deleted_at__isnull=True
            )
        except Plantilla.DoesNotExist:
            logger.warning("SYNC TEMPLATE_NOT_FOUND template=%s", template_key)
            return Response({"detail": "Plantilla no existe"}, status=status.HTTP_404_NOT_FOUND)

        # 2) Verifica asignación (OJO: UserPlantilla usa FK user/plantilla y deleted_at)
        ok = UserPlantilla.objects.filter(
            user=request.user,
            plantilla=plantilla,
            deleted_at__isnull=True
        ).exists()
        if not ok:
            logger.warning(
                "SYNC NOT_ASSIGNED user_id=%s template=%s plantilla_id=%s",
                request.user.id,
                template_key,
                plantilla.id,
            )
            return Response({"detail": "Plantilla no asignada al usuario"}, status=status.HTTP_403_FORBIDDEN)

        # 3) Valida versión
        if plantilla.version != payload_version:
            logger.warning(
                "SYNC VERSION_MISMATCH template=%s expected=%s got=%s",
                template_key,
                plantilla.version,
                payload_version,
            )
            return Response(
                {"detail": "Versión de payload no coincide", "expected": plantilla.version},
                status=status.HTTP_409_CONFLICT
            )

        # Instantáneo servidor (UTC aware). Django+USE_TZ guardaría en SQL como UTC;
        # reescribimos después con UPDATE en hora civil Perú para que SSMS muestre 29/03 22:42, no 30/03 03:42.
        try:
            now = timezone.now()
            lima_now_naive = instante_naive_lima_desde_utc_aware(now)

            fecha_ejecucion_ms = None
            if isinstance(header, dict):
                fecha_ejecucion_ms = header.get("fechaEjecucion")
            if fecha_ejecucion_ms is None:
                fecha_ejecucion_ms = data.get("fechaEjecucion")

            lima_ejec_naive = None
            if isinstance(fecha_ejecucion_ms, (int, float)) and fecha_ejecucion_ms > 0:
                lima_ejec_naive = fecha_ejecucion_naive_lima_desde_epoch_ms(fecha_ejecucion_ms)

            # 5) Insertar en PlantillaRegistro (OJO: aquí SÍ se usan los campos PascalCase del modelo)
            registro = PlantillaRegistro.objects.create(
                PlantillaId=plantilla.id,                 # PlantillaId int
                UserId=request.user.id,                   # UserId int
                FechaRegistro=now,
                FechaEjecucion=lima_ejec_naive,
                CampaniaId=data.get("campaniaId"),
                LoteId=data.get("loteId"),
                Lat=data.get("lat"),
                Lon=data.get("lon"),
                Estado="synced",
                # Tu BD exige isjson(DataJson)=1 → guardamos JSON string
                DataJson=json.dumps(payload, ensure_ascii=False),
                SyncStatus="synced",
                SyncError=None,
                SyncAttempts=0,
                ServerRegistroId=None,
                CreatedAt=now,
                UpdatedAt=now,
                DeletedAt=None
            )

            # Si quieres que ServerRegistroId = RegistroId (como venías haciendo):
            registro.ServerRegistroId = registro.RegistroId
            registro.save(update_fields=["ServerRegistroId"])

            # Escribir fechas como hora local Perú literal (evita conversión ORM a UTC en datetime2).
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE dbo.PlantillaRegistro
                    SET FechaRegistro = %s,
                        FechaEjecucion = %s,
                        CreatedAt = %s,
                        UpdatedAt = %s
                    WHERE RegistroId = %s
                    """,
                    [
                        lima_now_naive,
                        lima_ejec_naive,
                        lima_now_naive,
                        lima_now_naive,
                        registro.RegistroId,
                    ],
                )
        except Exception:
            logger.exception(
                "SYNC DB_ERROR template=%s user_id=%s campania=%s lote=%s",
                template_key,
                request.user.id,
                data.get("campaniaId"),
                data.get("loteId"),
            )
            raise

        logger.info(
            "SYNC OK registro_id=%s server_registro_id=%s template=%s user_id=%s",
            registro.RegistroId,
            registro.ServerRegistroId,
            template_key,
            request.user.id,
        )

        return Response(
            {"serverRegistroId": int(registro.RegistroId), "syncStatus": "synced"},
            status=status.HTTP_200_OK
        )

class UploadRegistroFotoView(APIView):
    """Sube una foto para un registro. Multipart: file, slot.

    Guarda en ``registros/{registro_id}/s{slot}_{uuid}.jpg`` (único por subida).
    Antes de guardar, elimina archivos previos del mismo slot (legado ``foto_{slot}.jpg``
    o ``s{slot}_*.jpg``) para no acumular ni pisar URLs en DataJson.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, registro_id: int):
        logger.debug(
            "FOTO START registro_id=%s user_id=%s remote_addr=%s content_type=%s",
            registro_id,
            getattr(request.user, "id", None),
            request.META.get("REMOTE_ADDR"),
            request.META.get("CONTENT_TYPE"),
        )
        try:
            raw_slot = request.data.get("slot")
            if raw_slot is None:
                logger.warning("FOTO MISSING_SLOT registro_id=%s", registro_id)
                return Response({"detail": "slot requerido"}, status=status.HTTP_400_BAD_REQUEST)
            slot = int(raw_slot) if not isinstance(raw_slot, int) else raw_slot
        except (ValueError, TypeError):
            logger.warning("FOTO INVALID_SLOT registro_id=%s raw_slot=%s", registro_id, request.data.get("slot"))
            return Response({"detail": "slot debe ser número 1-10"}, status=status.HTTP_400_BAD_REQUEST)

        if slot < 1 or slot > 10:
            logger.warning("FOTO OUT_OF_RANGE registro_id=%s slot=%s", registro_id, slot)
            return Response({"detail": "slot inválido (1-10)"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES.get("file")
        if not file:
            logger.warning("FOTO MISSING_FILE registro_id=%s slot=%s", registro_id, slot)
            return Response({"detail": "archivo requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reg = PlantillaRegistro.objects.get(
                RegistroId=registro_id,
                UserId=request.user.id,
                DeletedAt__isnull=True,
            )
        except PlantillaRegistro.DoesNotExist:
            logger.warning("FOTO REGISTRO_NOT_FOUND registro_id=%s user_id=%s", registro_id, request.user.id)
            return Response({"detail": "registro no existe"}, status=status.HTTP_404_NOT_FOUND)

        folder = f"registros/{registro_id}"
        # Nombre único por subida (evita pisar entre reemplazos / usuarios con el mismo slot).
        try:
            _delete_previous_fotos_for_slot(default_storage, folder, slot)
            filename = f"s{slot}_{uuid.uuid4().hex}.jpg"
            path = f"{folder}/{filename}"

            saved = default_storage.save(path, file)
            url = default_storage.url(saved)

            payload = json.loads(reg.DataJson)
            body = payload.get("body")
            if body is None:
                body = payload
            fotos = body.get("fotos", []) if isinstance(body, dict) else []

            found = False
            for f in fotos:
                if isinstance(f, dict) and int(f.get("slot", 0)) == slot:
                    f["serverUrl"] = url
                    found = True
                    break
            if not found:
                fotos.append({"slot": slot, "serverUrl": url})
            body["fotos"] = fotos
            if "body" in payload:
                payload["body"] = body
            else:
                payload["fotos"] = fotos

            reg.DataJson = json.dumps(payload, ensure_ascii=False)
            reg.UpdatedAt = timezone.now()
            reg.save(update_fields=["DataJson", "UpdatedAt"])
        except Exception:
            logger.exception(
                "FOTO SAVE_ERROR registro_id=%s slot=%s filename=%s",
                registro_id,
                slot,
                getattr(file, "name", None),
            )
            raise

        logger.info(
            "FOTO OK registro_id=%s slot=%s saved=%s url=%s size=%s",
            registro_id,
            slot,
            saved,
            url,
            getattr(file, "size", None),
        )

        return Response({"slot": slot, "serverUrl": url}, status=status.HTTP_200_OK)
