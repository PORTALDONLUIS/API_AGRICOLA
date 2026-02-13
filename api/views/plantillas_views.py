import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.utils import timezone
from rest_framework import status

from api.models import UserPlantilla, Plantilla, PlantillaRegistro
from api.serializers.registros_sync_serializers import SyncRegistroInSerializer
from api.services.plantillas_service import obtener_plantillas_asignadas
from api.serializers.plantillas_serializers import PlantillaAssignedSerializer
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser, FormParser

# class PlantillasAsignadasView(APIView):
#     authentication_classes = [DebugJWTAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         return Response({"ok": True, "user": request.user.username})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registros_sync(request):
    """
    Espera:
    {
      "templateKey": "cartilla-fito",
      "payloadVersion": 1,
      "dataJson": {...},
      "campaniaId": 2026, "loteId": 12,
      "lat": -14.1, "lon": -72.3
    }

    Responde:
    { "serverRegistroId": 123 }
    """

    template_key = request.data.get("templateKey")
    payload_version = request.data.get("payloadVersion")
    data_json = request.data.get("dataJson")

    if not template_key or data_json is None:
        return Response(
            {"detail": "templateKey y dataJson son obligatorios"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Crea o actualiza (si luego quieres idempotencia, aquí lo mejoras)
    obj = Registro.objects.create(
        user=request.user,
        template_key=template_key,
        payload_version=payload_version or 1,
        data_json=data_json,
        campania_id=request.data.get("campaniaId"),
        lote_id=request.data.get("loteId"),
        lat=request.data.get("lat"),
        lon=request.data.get("lon"),
    )

    return Response({"serverRegistroId": obj.id}, status=status.HTTP_201_CREATED)

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
        # s = SyncRegistroInSerializer(data=request.data)
        # s.is_valid(raise_exception=True)
        s = SyncRegistroInSerializer(data=request.data)
        if not s.is_valid():
            return Response({"errors": s.errors, "received": request.data}, status=400)
        data = s.validated_data

        template_key = data["templateKey"]
        payload_version = data.get("payloadVersion", 1)
        payload = data["dataJson"]

        # 1) Plantilla por código (OJO: usar nombres del MODELO: codigo/is_active/deleted_at)
        try:
            plantilla = Plantilla.objects.get(
                codigo=template_key,
                is_active=True,
                deleted_at__isnull=True
            )
        except Plantilla.DoesNotExist:
            return Response({"detail": "Plantilla no existe"}, status=status.HTTP_404_NOT_FOUND)

        # 2) Verifica asignación (OJO: UserPlantilla usa FK user/plantilla y deleted_at)
        ok = UserPlantilla.objects.filter(
            user=request.user,
            plantilla=plantilla,
            deleted_at__isnull=True
        ).exists()
        if not ok:
            return Response({"detail": "Plantilla no asignada al usuario"}, status=status.HTTP_403_FORBIDDEN)

        # 3) Valida versión
        if plantilla.version != payload_version:
            return Response(
                {"detail": "Versión de payload no coincide", "expected": plantilla.version},
                status=status.HTTP_409_CONFLICT
            )

        now = timezone.now()

        # 4) Insertar en PlantillaRegistro (OJO: aquí SÍ se usan los campos PascalCase del modelo)
        registro = PlantillaRegistro.objects.create(
            PlantillaId=plantilla.id,                 # PlantillaId int
            UserId=request.user.id,                   # UserId int
            FechaRegistro=now,
            FechaEjecucion=data.get("fechaEjecucion"),
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

        return Response(
            {"serverRegistroId": int(registro.RegistroId), "syncStatus": "synced"},
            status=status.HTTP_200_OK
        )

class UploadRegistroFotoView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, registro_id: int):
        slot = int(request.data.get("slot", "0"))
        file = request.FILES.get("file")

        if slot < 1 or slot > 10:
            return Response({"detail": "slot inválido"}, status=400)
        if not file:
            return Response({"detail": "archivo requerido"}, status=400)

        try:
            reg = PlantillaRegistro.objects.get(RegistroId=registro_id, UserId=request.user.id, DeletedAt__isnull=True)
        except PlantillaRegistro.DoesNotExist:
            return Response({"detail": "registro no existe"}, status=404)

        # guarda archivo
        folder = f"registros/{registro_id}"
        filename = f"foto_{slot}.jpg"
        path = os.path.join(folder, filename)

        saved = default_storage.save(path, file)
        url = default_storage.url(saved)  # serverUrl

        # actualiza DataJson.fotos
        payload = json.loads(reg.DataJson)
        fotos = payload.get("fotos", [])
        # busca slot
        found = False
        for f in fotos:
            if int(f.get("slot", 0)) == slot:
                f["serverUrl"] = url
                found = True
                break
        if not found:
            fotos.append({"slot": slot, "serverUrl": url})
        payload["fotos"] = fotos

        reg.DataJson = json.dumps(payload, ensure_ascii=False)
        reg.UpdatedAt = timezone.now()
        reg.save(update_fields=["DataJson", "UpdatedAt"])

        return Response({"slot": slot, "serverUrl": url}, status=200)


