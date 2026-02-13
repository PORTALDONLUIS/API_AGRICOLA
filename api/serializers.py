from rest_framework import serializers

class SyncRegistroInSerializer(serializers.Serializer):
    templateKey = serializers.CharField()
    payloadVersion = serializers.IntegerField()
    dataJson = serializers.JSONField()

    fechaEjecucion = serializers.DateTimeField(required=False, allow_null=True)
    campaniaId = serializers.IntegerField(required=False, allow_null=True)
    loteId = serializers.IntegerField(required=False, allow_null=True)
    lat = serializers.DecimalField(required=False, allow_null=True, max_digits=9, decimal_places=6)
    lon = serializers.DecimalField(required=False, allow_null=True, max_digits=9, decimal_places=6)

class SyncRegistroOutSerializer(serializers.Serializer):
    serverRegistroId = serializers.IntegerField()
    syncStatus = serializers.CharField()
