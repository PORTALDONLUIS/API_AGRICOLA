from rest_framework import serializers
from api.models import Plantilla, UserPlantilla

class PlantillaAssignedSerializer(serializers.ModelSerializer):
    plantillaId = serializers.IntegerField(source="id")
    payloadJson = serializers.CharField(source="payload_json")
    updatedAt = serializers.DateTimeField(source="updated_at")
    deletedAt = serializers.DateTimeField(source="deleted_at", allow_null=True)
    assignment = serializers.SerializerMethodField()

    class Meta:
        model = Plantilla
        fields = ["plantillaId","codigo","nombre","descripcion","payloadJson","version","updatedAt","deletedAt","assignment"]

    def get_assignment(self, obj):
        mapping = self.context.get("assignment_by_plantilla", {})
        up = mapping.get(obj.id)
        if not up:
            return None
        return {
            "userPlantillaId": up.id,
            "estado": up.estado,
            "assignedAt": up.assigned_at,
            "updatedAt": up.updated_at,
            "deletedAt": up.deleted_at,
        }
