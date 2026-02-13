from rest_framework import serializers


class SyncRegistroInSerializer(serializers.Serializer):
    templateKey = serializers.CharField(max_length=100)
    payloadVersion = serializers.IntegerField(required=False, default=1)
    dataJson = serializers.JSONField()

    campaniaId = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    loteId = serializers.IntegerField(required=False, allow_null=True)

    # campaniaId = serializers.IntegerField(required=False, allow_null=True)
    # loteId = serializers.IntegerField(required=False, allow_null=True)
    lat = serializers.FloatField(required=False, allow_null=True)
    lon = serializers.FloatField(required=False, allow_null=True)
