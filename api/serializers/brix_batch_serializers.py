"""Validación acotada del protocolo compacto; no sustituye el endpoint legacy."""

from rest_framework import serializers

from api.services.brix_batch_codec import MAX_BATCH_RECORDS


class BatchContextSerializer(serializers.Serializer):
    header = serializers.DictField()
    body = serializers.DictField()


class BrixBatchInSerializer(serializers.Serializer):
    protocolVersion = serializers.IntegerField(min_value=1, max_value=1)
    plantillaId = serializers.IntegerField(min_value=1)
    key = serializers.CharField(max_length=100)
    plantillaVersion = serializers.IntegerField(min_value=1)
    contexts = BatchContextSerializer(many=True, allow_empty=False)
    records = serializers.ListField(
        child=serializers.DictField(), min_length=1, max_length=MAX_BATCH_RECORDS,
    )

    def validate_contexts(self, value):
        if len(value) > MAX_BATCH_RECORDS:
            raise serializers.ValidationError("Máximo 50 contextos por bloque.")
        return value


class BrixBatchRecordSerializer(serializers.Serializer):
    clientRecordId = serializers.UUIDField()
    revision = serializers.RegexField(r"^[0-9a-f]{64}$")
    baseRevision = serializers.RegexField(r"^[0-9a-f]{64}$", required=False)
    context = serializers.IntegerField(min_value=0, max_value=MAX_BATCH_RECORDS - 1)
    payloadVersion = serializers.IntegerField(min_value=1)
    header = serializers.DictField(required=False, default=dict)
    body = serializers.DictField(required=False, default=dict)
    campaniaId = serializers.CharField(
        max_length=8, required=False, allow_null=True, allow_blank=True,
    )
    loteId = serializers.IntegerField(required=False, allow_null=True)
    lat = serializers.FloatField(required=False, allow_null=True, min_value=-90, max_value=90)
    lon = serializers.FloatField(required=False, allow_null=True, min_value=-180, max_value=180)
