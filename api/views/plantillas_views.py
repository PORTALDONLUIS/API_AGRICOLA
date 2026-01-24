from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.services.plantillas_service import obtener_plantillas_asignadas
from api.serializers.plantillas_serializers import PlantillaAssignedSerializer
from api.views.auth_debug import DebugJWTAuthentication


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
