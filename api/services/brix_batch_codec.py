"""Contrato v1: JSON individual y revisión estable entre Python y Dart.

La revisión excluye columnas SQL redondeadas (Lat/Lon) y metadatos de transporte.
Una delta sustituye una clave completa; nunca se mezclan objetos recursivamente.
"""

import hashlib
import json
import math
import struct


BRIX_KEY = "cartilla_brix_moscatel"
MAX_BATCH_BYTES = 512 * 1024
MAX_BATCH_RECORDS = 50
MAX_SAFE_INTEGER = 2 ** 53


def normalize_template_key(value):
    return value.strip().lower().replace("-", "_")


def _typed_node(value, depth=0):
    if depth > 24:
        raise ValueError("JSON demasiado anidado")
    if value is None:
        return ["null"]
    if isinstance(value, bool):
        return ["bool", value]
    if isinstance(value, str):
        # También rechaza sustitutos UTF-16 sin pareja: no son UTF-8 válido.
        value.encode("utf-8")
        return ["string", value]
    if isinstance(value, (int, float)):
        if isinstance(value, int) and abs(value) > MAX_SAFE_INTEGER:
            raise ValueError("Entero fuera del contrato JSON v1")
        number = float(value)
        if not math.isfinite(number) or abs(number) > MAX_SAFE_INTEGER:
            raise ValueError("Número fuera del contrato JSON v1")
        if number == 0:
            number = 0.0
        return ["number", struct.pack(">d", number).hex()]
    if isinstance(value, list):
        return ["list", [_typed_node(item, depth + 1) for item in value]]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("Las claves JSON deben ser texto")
        # Dart compara unidades UTF-16; también coincide para claves con emoji.
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return ["map", [[key, _typed_node(value[key], depth + 1)] for key in keys]]
    raise ValueError("Tipo no admitido en JSON v1")


def canonical_revision(template_key, payload_version, data_json):
    snapshot = {
        "templateKey": normalize_template_key(template_key),
        "payloadVersion": payload_version,
        "dataJson": {
            "payloadVersion": data_json.get("payloadVersion", payload_version),
            "header": data_json.get("header") or {},
            "body": data_json.get("body") or {},
        },
    }
    encoded = json.dumps(
        _typed_node(snapshot), ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def expand_record(contexts, record):
    index = record["context"]
    if index >= len(contexts):
        raise ValueError("Contexto fuera del bloque")
    context = contexts[index]
    header = dict(context["header"])
    header.update(record.get("header", {}))
    body = dict(context["body"])
    body.update(record.get("body", {}))
    return {"payloadVersion": record["payloadVersion"], "header": header, "body": body}
