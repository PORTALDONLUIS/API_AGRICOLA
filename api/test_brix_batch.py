"""Pruebas herméticas: python -m unittest api.test_brix_batch -v

Configura SQLite :memory: antes de cargar Django. Las pruebas de almacenamiento
se omiten si otro runner ya configuró una base distinta de SQLite en memoria.
Nunca se conectan a SQL Server, ni se leen credenciales del proyecto.
"""

import copy
import io
import json
import unittest
import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY="synthetic-batch-test-only",
        INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "api"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False, TIME_ZONE="America/Lima", ROOT_URLCONF=__name__,
        REST_FRAMEWORK={"UNAUTHENTICATED_USER": None},
    )
    import django
    django.setup()

from django.db import IntegrityError, connection
from django.urls import path
from rest_framework.exceptions import ParseError
from rest_framework.test import APIRequestFactory, force_authenticate

from api.models import PlantillaRegistro
from api.serializers.brix_batch_serializers import BrixBatchInSerializer, BrixBatchRecordSerializer
from api.services.brix_batch_codec import canonical_revision, expand_record
from api.services.brix_batch_sync import BatchRecordError, prepare_record, store_record
from api.views.brix_batch_views import BatchTooLarge, BoundedBatchJSONParser, SyncBrixBatchView


urlpatterns = [path("api/registros/sync-batch/", SyncBrixBatchView.as_view())]
TEMPLATE = SimpleNamespace(id=99, codigo="cartilla_brix_moscatel", version=1)
USER = SimpleNamespace(id=7, is_authenticated=True)
UUID = "a9bf289e-43c1-4fcf-aed8-d7a1a03bf165"


def fixture_payload():
    return {
        "payloadVersion": 1,
        "header": {"fechaEjecucion": 1793048400000, "lat": -0.0, "userId": 7},
        "body": {"brixSsc": 18.5, "observaciones": "Muestra ñ 🍇", "planta": 1},
    }


def fixture_block():
    payload = fixture_payload()
    payload["header"]["plantillaId"] = TEMPLATE.id
    return {
        "protocolVersion": 1, "plantillaId": 99, "key": TEMPLATE.codigo,
        "plantillaVersion": 1,
        "contexts": [{"header": payload["header"], "body": {"planta": 1}}],
        "records": [{
            "clientRecordId": UUID, "revision": canonical_revision(TEMPLATE.codigo, 1, payload),
            "context": 0, "payloadVersion": 1,
            "header": {}, "body": {"brixSsc": 18.5, "observaciones": "Muestra ñ 🍇"},
        }],
    }


def lote_fixture_block(lote_id="123", start=0, count=1):
    """Selector String y GPS reales; cada captura conserva UUID y su instante."""
    block = fixture_block()
    header = block["contexts"][0]["header"]
    base_ms = header.pop("fechaEjecucion")
    header.update(
        loteId=lote_id, campaniaId="2026", lat=-14.01959, lon=-75.75971,
        gpsAccuracy=8.0, gpsDate="2026-10-26T15:59:58-05:00", gpsSource="stream",
    )
    block["contexts"][0]["body"].update(hilera=1, planta=1, variedad=8, corresponde="PODA")
    block["records"] = []
    for index in range(start, start + count):
        record = {
            "clientRecordId": str(uuid.uuid5(uuid.NAMESPACE_URL, "synthetic-brix-lote-%s" % index)),
            "context": 0, "payloadVersion": 1,
            "header": {"fechaEjecucion": base_ms + index * 1000},
            "body": {"brixSsc": 18 + (index % 20) / 10, "observaciones": "Prueba sintética"},
        }
        record["revision"] = canonical_revision(
            TEMPLATE.codigo, 1, expand_record(block["contexts"], record),
        )
        block["records"].append(record)
    return block


def prepare_serialized_record(block, user_id=USER.id):
    envelope = BrixBatchInSerializer(data=block)
    envelope.is_valid(raise_exception=True)
    record = BrixBatchRecordSerializer(data=envelope.validated_data["records"][0])
    record.is_valid(raise_exception=True)
    return prepare_record(envelope.validated_data["contexts"], record.validated_data, TEMPLATE, user_id)


class LoteRegressionTests(unittest.TestCase):
    def test_selector_representations_become_int_column_without_changing_snapshot(self):
        for value, expected in ((123, 123), ("123", 123), (123.0, 123), ("123.0", 123),
                                (0, 0), ("0", 0), (0.0, 0), (None, None),
                                (-2147483648, -2147483648), ("2147483647", 2147483647)):
            block = lote_fixture_block(value)
            untouched = copy.deepcopy(block)
            revision = block["records"][0]["revision"]
            with self.subTest(lote=value):
                payload, _, columns = prepare_serialized_record(block)
                self.assertEqual(columns["LoteId"], expected)
                if expected is not None:
                    self.assertIs(type(columns["LoteId"]), int)
                self.assertEqual(payload["header"]["loteId"], value)
                self.assertIs(type(payload["header"]["loteId"]), type(value))
                self.assertEqual(columns["Lat"], -14.01959)
                self.assertEqual(columns["Lon"], -75.75971)
                self.assertEqual(canonical_revision(TEMPLATE.codigo, 1, payload), revision)
                self.assertEqual(block, untouched)

    def test_invalid_lote_values_remain_rejected(self):
        for value in (True, False, 123.5, "123.5", "CABILDOC1", "", "1e2", "123e0",
                      "1; DROP TABLE LOTE", [], {}, "1" * 1001,
                      2147483648, "2147483648", -2147483649, "-2147483649"):
            with self.subTest(lote=value), self.assertRaisesRegex(BatchRecordError, "invalid_lote"):
                prepare_serialized_record(lote_fixture_block(value))

    def test_duplicate_metadata_compares_integer_identity_but_rejects_different_lote(self):
        for header_value, top_value in (("123", 123), (123, "123"), (123.0, 123), ("123.0", 123)):
            block = lote_fixture_block(header_value)
            block["records"][0]["loteId"] = top_value
            with self.subTest(header=header_value, top=top_value):
                payload, _, columns = prepare_serialized_record(block)
                self.assertEqual(columns["LoteId"], 123)
                self.assertEqual(payload["header"]["loteId"], header_value)
        for header_value, top_value in (("123", 124), (123, "124"), (None, 123), (123, None)):
            block = lote_fixture_block(header_value)
            block["records"][0]["loteId"] = top_value
            with self.subTest(header=header_value, top=top_value):
                with self.assertRaisesRegex(BatchRecordError, "header_metadata_mismatch"):
                    prepare_serialized_record(block)

    def test_normalizing_lote_does_not_relax_coordinate_limits(self):
        for key, value in (("lat", 90.1), ("lon", -180.1), ("lat", True), ("lon", "-75.75971")):
            block = lote_fixture_block("123")
            block["contexts"][0]["header"][key] = value
            record = block["records"][0]
            record["revision"] = canonical_revision(TEMPLATE.codigo, 1, expand_record(block["contexts"], record))
            with self.subTest(key=key, value=value):
                with self.assertRaisesRegex(BatchRecordError, "invalid_coordinates"):
                    prepare_serialized_record(block)


class CodecTests(unittest.TestCase):
    def test_shared_dart_fixture(self):
        self.assertEqual(canonical_revision(TEMPLATE.codigo, 1, fixture_payload()),
                         "37feea892c65d361bd430932630dc4b6a998db2a1998136cf6c6510c4a90a654")

    def test_dictionary_order_and_integral_float_do_not_change_revision(self):
        payload = fixture_payload()
        other = copy.deepcopy(payload)
        other["header"] = {"userId": 7.0, "lat": 0, "fechaEjecucion": 1793048400000.0}
        self.assertEqual(canonical_revision(TEMPLATE.codigo, 1, payload),
                         canonical_revision(" CARTILLA-BRIX-MOSCATEL ", 1, other))
        other["body"]["brixSsc"] = 19
        self.assertNotEqual(canonical_revision(TEMPLATE.codigo, 1, payload),
                            canonical_revision(TEMPLATE.codigo, 1, other))

    def test_reject_nonfinite_and_unsafe_numbers(self):
        for value in (float("nan"), float("inf"), 2 ** 53 + 1):
            payload = fixture_payload()
            payload["body"]["brixSsc"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_revision(TEMPLATE.codigo, 1, payload)

    def test_expand_is_self_contained_shallow_and_does_not_mutate_context(self):
        block = fixture_block()
        before = copy.deepcopy(block)
        payload = expand_record(block["contexts"], block["records"][0])
        expected = fixture_payload()
        expected["header"]["plantillaId"] = TEMPLATE.id
        self.assertEqual(payload, expected)
        self.assertEqual(block, before)
        self.assertNotIn("contexts", payload)

    def test_revision_version_user_capture_and_metadata_validation(self):
        for change, error in (
            (lambda b: b["records"][0].update(revision="0" * 64), "revision_mismatch"),
            (lambda b: b["records"][0].update(payloadVersion=2), "payload_version_mismatch"),
            (lambda b: b["records"][0].update(lat=12), "header_metadata_mismatch"),
        ):
            block = fixture_block()
            change(block)
            with self.subTest(error=error), self.assertRaisesRegex(BatchRecordError, error):
                prepare_record(block["contexts"], block["records"][0], TEMPLATE, 7)
        block = fixture_block()
        with self.assertRaisesRegex(BatchRecordError, "header_user_mismatch"):
            prepare_record(block["contexts"], block["records"][0], TEMPLATE, 8)
        for date in (None, 0, "2026-10-26", True, 2 ** 53):
            block = fixture_block()
            block["contexts"][0]["header"]["fechaEjecucion"] = date
            record = block["records"][0]
            record["revision"] = canonical_revision(TEMPLATE.codigo, 1, expand_record(block["contexts"], record))
            with self.subTest(date=date), self.assertRaisesRegex(BatchRecordError, "invalid_capture_date"):
                prepare_record(block["contexts"], record, TEMPLATE, 7)


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.template_patch = patch("api.views.brix_batch_views.Plantilla.objects.get", return_value=TEMPLATE)
        self.assignment_patch = patch("api.views.brix_batch_views.UserPlantilla.objects.filter")
        self.template_patch.start()
        self.assignment = self.assignment_patch.start()
        self.assignment.return_value.exists.return_value = True
        self.addCleanup(self.template_patch.stop)
        self.addCleanup(self.assignment_patch.stop)

    def post(self, block, user=USER):
        request = APIRequestFactory().post("/api/registros/sync-batch/", block, format="json")
        if user:
            force_authenticate(request, user=user)
        return SyncBrixBatchView.as_view()(request)

    def test_permission_and_version_gate_before_writes(self):
        with patch("api.views.brix_batch_views.store_record") as store:
            self.assertIn(self.post(fixture_block(), user=None).status_code, (401, 403))
            self.assignment.return_value.exists.return_value = False
            self.assertEqual(self.post(fixture_block()).status_code, 403)
            self.assignment.return_value.exists.return_value = True
            block = fixture_block()
            block["plantillaVersion"] = 2
            self.assertEqual(self.post(block).status_code, 409)
            store.assert_not_called()

    def test_batch_remains_exclusive_to_brix_moscatel(self):
        with patch("api.views.brix_batch_views.store_record") as store:
            block = lote_fixture_block("123")
            block["key"] = "cartilla_fitosanidad"
            self.assertEqual(self.post(block).status_code, 400)
            other = SimpleNamespace(id=99, codigo="cartilla_fitosanidad", version=1)
            with patch("api.views.brix_batch_views.Plantilla.objects.get", return_value=other):
                self.assertEqual(self.post(lote_fixture_block("123")).status_code, 400)
            store.assert_not_called()

    def test_context_size_duplicate_and_record_limits_before_writes(self):
        with patch("api.views.brix_batch_views.store_record") as store:
            block = fixture_block()
            block["records"] *= 2
            self.assertEqual(self.post(block).status_code, 400)
            block["records"] *= 26
            self.assertEqual(self.post(block).status_code, 400)
            block = fixture_block()
            block["contexts"] *= 51
            self.assertEqual(self.post(block).status_code, 400)
            store.assert_not_called()

    def test_partial_error_only_acks_valid_uuid_revision(self):
        block = fixture_block()
        broken = copy.deepcopy(block["records"][0])
        broken["clientRecordId"] = str(uuid.uuid4())
        broken["revision"] = "0" * 64
        block["records"].append(broken)
        ack = dict(clientRecordId=UUID, revision=block["records"][0]["revision"],
                   status="synced", serverRegistroId=123)
        with patch("api.views.brix_batch_views.store_record", return_value=ack) as store:
            response = self.post(block)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["results"][0], ack)
            self.assertEqual(response.data["results"][1]["error"], "revision_mismatch")
            self.assertEqual(store.call_count, 1)

    def test_database_outage_does_not_repeat_fifty_connections(self):
        block = fixture_block()
        block["records"] += [dict(block["records"][0], clientRecordId=str(uuid.uuid4())) for _ in range(49)]
        with patch("api.views.brix_batch_views.store_record", side_effect=IntegrityError("synthetic")) as store:
            with patch("api.views.brix_batch_views.logger"):
                response = self.post(block)
            self.assertEqual(store.call_count, 1)
            self.assertEqual(len(response.data["results"]), 50)
            self.assertTrue(all(row["status"] == "error" for row in response.data["results"]))

    def test_out_of_range_capture_is_individual_error(self):
        block = fixture_block()
        bad = dict(block["records"][0], clientRecordId=str(uuid.uuid4()),
                   header={"fechaEjecucion": 2 ** 53})
        bad["revision"] = canonical_revision(TEMPLATE.codigo, 1, expand_record(block["contexts"], bad))
        block["records"].append(bad)
        with patch("api.views.brix_batch_views.store_record", return_value={"status": "synced"}) as store:
            response = self.post(block)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][1]["error"], "invalid_capture_date")
        self.assertEqual(store.call_count, 1)

    def test_identity_is_mandatory_and_bound_to_authenticated_user_and_template(self):
        for key, error in (("userId", "header_user_mismatch"),
                           ("plantillaId", "header_template_mismatch")):
            for value in (None, "missing", 1234, True):
                block = fixture_block()
                header = block["contexts"][0]["header"]
                if value == "missing":
                    header.pop(key)
                else:
                    header[key] = value
                record = block["records"][0]
                record["revision"] = canonical_revision(
                    TEMPLATE.codigo, 1, expand_record(block["contexts"], record),
                )
                with self.subTest(key=key, value=value):
                    with patch("api.views.brix_batch_views.store_record") as store:
                        response = self.post(block)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data["results"][0]["error"], error)
                    store.assert_not_called()

    def test_parser_rejects_over_512_kib_and_invalid_json(self):
        parser = BoundedBatchJSONParser()
        with self.assertRaises(BatchTooLarge):
            parser.parse(io.BytesIO(b" " * (512 * 1024 + 1)))
        with self.assertRaises(ParseError):
            parser.parse(io.BytesIO(b'{"value":NaN}'))


class StoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if connection.vendor != "sqlite" or connection.settings_dict["NAME"] != ":memory:":
            raise unittest.SkipTest("Solo ejecuta almacenamiento en SQLite :memory:")
        with connection.schema_editor() as editor:
            editor.create_model(PlantillaRegistro)
        with connection.cursor() as cursor:
            cursor.execute("CREATE UNIQUE INDEX test_user_uuid ON PlantillaRegistro(UserId, ClientRecordId)")

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as editor:
            editor.delete_model(PlantillaRegistro)
        super().tearDownClass()

    def setUp(self):
        PlantillaRegistro.objects.all().delete()
        # SQL datetime2 se verifica aparte; SQLite conserva las fechas del ORM.
        self.dates_patch = patch("api.services.brix_batch_sync._write_lima_dates")
        self.dates = self.dates_patch.start()
        self.addCleanup(self.dates_patch.stop)
        block = fixture_block()
        self.record = block["records"][0]
        self.payload, self.capture, self.columns = prepare_record(block["contexts"], self.record, TEMPLATE, 7)

    def store(self, record=None, payload=None, user_id=7):
        return store_record(record or self.record, payload or self.payload,
                            self.capture, self.columns, TEMPLATE, user_id)

    def test_retry_after_lost_ack_preserves_one_row_and_original_dates(self):
        first = self.store()
        original = PlantillaRegistro.objects.get()
        self.dates.reset_mock()
        ack = self.store()
        stored = PlantillaRegistro.objects.get()
        self.assertEqual(first, ack)
        self.assertEqual(PlantillaRegistro.objects.count(), 1)
        self.assertEqual(stored.CreatedAt, original.CreatedAt)
        self.assertEqual(stored.FechaEjecucion, original.FechaEjecucion)
        self.assertEqual(stored.FechaRegistro, original.FechaRegistro)
        self.assertEqual(stored.DataJson, original.DataJson)
        self.dates.assert_not_called()

    def test_string_selector_is_stored_as_int_column_and_preserved_as_json_after_retry(self):
        block = lote_fixture_block("123")
        payload, capture, columns = prepare_serialized_record(block)
        record = block["records"][0]
        ack = store_record(record, payload, capture, columns, TEMPLATE, USER.id)
        original = PlantillaRegistro.objects.get()
        self.assertIs(type(original.LoteId), int)
        self.assertEqual(original.LoteId, 123)
        self.assertEqual(json.loads(original.DataJson)["header"]["loteId"], "123")
        self.dates.reset_mock()
        self.assertEqual(store_record(record, payload, capture, columns, TEMPLATE, USER.id), ack)
        current = PlantillaRegistro.objects.get()
        self.assertEqual(PlantillaRegistro.objects.count(), 1)
        for key in ("DataJson", "LoteId", "CreatedAt", "FechaRegistro", "FechaEjecucion"):
            self.assertEqual(getattr(current, key), getattr(original, key))
        self.assertEqual(canonical_revision(TEMPLATE.codigo, 1, json.loads(current.DataJson)), record["revision"])
        self.dates.assert_not_called()

    def test_full_brix_snapshot_preserves_author_and_structural_web_query_contract(self):
        block = lote_fixture_block("123")
        record = block["records"][0]
        record["body"]["brixSsc"] = 18.5
        original = copy.deepcopy(expand_record(block["contexts"], record))
        record["revision"] = canonical_revision(TEMPLATE.codigo, 1, original)
        original_revision = record["revision"]
        payload, capture, columns = prepare_serialized_record(block)
        ack = store_record(record, payload, capture, columns, TEMPLATE, USER.id)
        self.assertEqual(ack["status"], "synced")
        stored = PlantillaRegistro.objects.get(RegistroId=ack["serverRegistroId"])
        self.assertEqual(stored.UserId, USER.id)
        self.assertEqual(stored.PlantillaId, TEMPLATE.id)
        self.assertEqual(stored.LoteId, 123)
        self.assertIs(type(stored.LoteId), int)
        self.assertEqual(stored.CampaniaId, "2026")
        self.assertEqual(stored.SyncStatus, "synced")
        self.assertEqual(stored.FechaEjecucion, datetime(2026, 10, 26, 16, 0))
        self.assertEqual(stored.Lat, Decimal("-14.019590"))
        self.assertEqual(stored.Lon, Decimal("-75.759710"))
        stored_json = json.loads(stored.DataJson)
        self.assertEqual(stored_json, original)
        self.assertEqual(stored_json["header"]["loteId"], "123")
        self.assertEqual(stored_json["header"]["gpsAccuracy"], 8.0)
        self.assertEqual(stored_json["header"]["gpsDate"], "2026-10-26T15:59:58-05:00")
        self.assertEqual(stored_json["body"], {
            "hilera": 1, "planta": 1, "variedad": 8, "corresponde": "PODA",
            "brixSsc": 18.5, "observaciones": "Prueba sintética",
        })
        self.assertEqual(canonical_revision(TEMPLATE.codigo, 1, stored_json), original_revision)

        # Mismo contexto y UUID bajo otro usuario: la identidad SQL y el filtro
        # del evaluador deben seguir separando ambas muestras.
        other = copy.deepcopy(block)
        other["contexts"][0]["header"]["userId"] = 8
        other_record = other["records"][0]
        other_record["revision"] = canonical_revision(
            TEMPLATE.codigo, 1, expand_record(other["contexts"], other_record),
        )
        other_payload, other_capture, other_columns = prepare_serialized_record(other, user_id=8)
        other_ack = store_record(other_record, other_payload, other_capture, other_columns, TEMPLATE, 8)
        self.assertEqual(other_ack["status"], "synced")
        self.assertNotEqual(other_ack["serverRegistroId"], ack["serverRegistroId"])
        matching = PlantillaRegistro.objects.filter(
            PlantillaId=TEMPLATE.id, UserId=USER.id, LoteId=123, CampaniaId="2026",
            FechaEjecucion__date=datetime(2026, 10, 26).date(), SyncStatus="synced",
            DeletedAt__isnull=True,
        )
        self.assertEqual(list(matching.values_list("RegistroId", flat=True)), [stored.RegistroId])
        self.assertEqual(json.loads(matching.get().DataJson), original)
        self.assertEqual(PlantillaRegistro.objects.count(), 2)
        self.assertFalse(matching.filter(UserId=8).exists())

    def test_1056_string_selector_samples_sync_in_50_row_blocks_and_retry_without_duplicates(self):
        blocks = [lote_fixture_block("123", start, min(50, 1056 - start)) for start in range(0, 1056, 50)]
        self.assertEqual([len(block["records"]) for block in blocks], [50] * 21 + [6])
        first_acks = {}
        with patch("api.views.brix_batch_views.Plantilla.objects.get", return_value=TEMPLATE):
            with patch("api.views.brix_batch_views.UserPlantilla.objects.filter") as assignment:
                assignment.return_value.exists.return_value = True
                for retry in (False, True):
                    for block in blocks:
                        request = APIRequestFactory().post("/api/registros/sync-batch/", block, format="json")
                        force_authenticate(request, user=USER)
                        response = SyncBrixBatchView.as_view()(request)
                        self.assertEqual(response.status_code, 200)
                        results = response.data["results"]
                        self.assertEqual(len(results), len(block["records"]))
                        for result, record in zip(results, block["records"]):
                            self.assertEqual(result["status"], "synced", result)
                            self.assertEqual(result["revision"], record["revision"])
                            identity = result["clientRecordId"]
                            if retry:
                                self.assertEqual(result, first_acks[identity])
                            else:
                                first_acks[identity] = result
                    self.assertEqual(PlantillaRegistro.objects.count(), 1056)
                    rows = list(PlantillaRegistro.objects.order_by("RegistroId").values(
                        "RegistroId", "ClientRecordId", "LoteId", "DataJson", "CreatedAt", "FechaRegistro", "FechaEjecucion",
                    ))
                    if retry:
                        self.assertEqual(rows, originals)
                        self.dates.assert_not_called()
                    else:
                        originals = rows
                        self.assertEqual(len(first_acks), 1056)
                        self.assertTrue(all(row["LoteId"] == 123 for row in rows))
                        self.assertTrue(all(json.loads(row["DataJson"])["header"]["loteId"] == "123" for row in rows))
                        for row in PlantillaRegistro.objects.order_by("RegistroId"):
                            self.assertEqual(row.UserId, USER.id)
                            self.assertEqual(row.PlantillaId, TEMPLATE.id)
                            self.assertEqual(row.CampaniaId, "2026")
                            self.assertEqual(row.SyncStatus, "synced")
                            self.assertEqual(row.Lat, Decimal("-14.019590"))
                            self.assertEqual(row.Lon, Decimal("-75.759710"))
                            data = json.loads(row.DataJson)
                            self.assertEqual(data["header"]["gpsAccuracy"], 8.0)
                            self.assertEqual(data["header"]["gpsDate"], "2026-10-26T15:59:58-05:00")
                            self.assertEqual(data["body"]["hilera"], 1)
                            self.assertEqual(data["body"]["planta"], 1)
                            self.assertEqual(data["body"]["variedad"], 8)
                            self.assertEqual(data["body"]["corresponde"], "PODA")
                            self.assertEqual(canonical_revision(TEMPLATE.codigo, 1, data),
                                             first_acks[row.ClientRecordId]["revision"])
                        self.assertEqual(self.dates.call_count, 1056)
                        self.dates.reset_mock()

    def test_tombstone_is_returned_and_never_resurrected(self):
        self.store()
        deleted = datetime(2026, 10, 27, 10, 0)
        PlantillaRegistro.objects.update(DeletedAt=deleted, SyncStatus="deleted", Estado="deleted")
        self.assertEqual(self.store()["status"], "deleted")
        stored = PlantillaRegistro.objects.get()
        self.assertEqual(stored.DeletedAt, deleted)
        self.assertEqual(stored.SyncStatus, "deleted")

    def test_legacy_lost_ack_without_header_identity_preserves_original_snapshot(self):
        first = self.store()
        for null_ids in (False, True):
            legacy = copy.deepcopy(self.payload)
            for key in ("userId", "plantillaId"):
                if null_ids:
                    legacy["header"][key] = None
                else:
                    legacy["header"].pop(key)
            legacy_json = json.dumps(legacy, ensure_ascii=False)
            PlantillaRegistro.objects.update(DataJson=legacy_json)
            original = PlantillaRegistro.objects.get()
            self.dates.reset_mock()
            with self.subTest(null_ids=null_ids):
                self.assertEqual(self.store(), first)
                stored = PlantillaRegistro.objects.get()
                self.assertEqual(PlantillaRegistro.objects.count(), 1)
                self.assertEqual(stored.DataJson, legacy_json)
                self.assertEqual(stored.CreatedAt, original.CreatedAt)
                self.assertEqual(stored.FechaRegistro, original.FechaRegistro)
                self.assertEqual(stored.FechaEjecucion, original.FechaEjecucion)
                self.dates.assert_not_called()

    def test_contradictory_legacy_header_identity_conflicts_without_rewriting(self):
        self.store()
        for key, value in (("userId", 8), ("plantillaId", 98)):
            legacy = copy.deepcopy(self.payload)
            legacy["header"][key] = value
            legacy_json = json.dumps(legacy, ensure_ascii=False)
            PlantillaRegistro.objects.update(DataJson=legacy_json)
            with self.subTest(key=key):
                self.assertEqual(self.store()["status"], "conflict")
                self.assertEqual(PlantillaRegistro.objects.get().DataJson, legacy_json)

    def test_other_template_conflicts_and_other_user_has_own_uuid(self):
        self.store()
        PlantillaRegistro.objects.update(PlantillaId=98)
        self.assertEqual(self.store()["status"], "conflict")
        self.assertEqual(self.store(user_id=8)["status"], "synced")
        self.assertEqual(PlantillaRegistro.objects.count(), 2)

    def test_changed_content_needs_current_base_revision(self):
        self.store()
        original = PlantillaRegistro.objects.get()
        payload = copy.deepcopy(self.payload)
        payload["body"]["brixSsc"] = 20
        record = dict(self.record, revision=canonical_revision(TEMPLATE.codigo, 1, payload))
        self.assertEqual(self.store(record, payload)["status"], "conflict")
        self.assertEqual(PlantillaRegistro.objects.get().DataJson, original.DataJson)
        record["baseRevision"] = self.record["revision"]
        self.assertEqual(self.store(record, payload)["status"], "synced")
        current = PlantillaRegistro.objects.get()
        self.assertEqual(json.loads(current.DataJson), payload)
        self.assertEqual(current.CreatedAt, original.CreatedAt)
        self.assertEqual(current.FechaRegistro, original.FechaRegistro)
        # Una segunda edición con la base anterior ya no puede sobrescribir.
        other = copy.deepcopy(payload)
        other["body"]["brixSsc"] = 21
        stale = dict(record, revision=canonical_revision(TEMPLATE.codigo, 1, other))
        self.assertEqual(self.store(stale, other)["status"], "conflict")

    def test_commit_or_date_failure_rolls_back_instead_of_acknowledging(self):
        self.dates.side_effect = RuntimeError("synthetic failure before commit")
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            self.store()
        self.assertEqual(PlantillaRegistro.objects.count(), 0)

    def test_unique_race_reloads_the_winner(self):
        self.store()
        with patch("api.services.brix_batch_sync._store_once") as once:
            once.side_effect = [IntegrityError("synthetic competing insert"), {"status": "synced"}]
            self.assertEqual(self.store(), {"status": "synced"})
            self.assertEqual(once.call_args_list[0].args[-1], True)
            self.assertEqual(once.call_args_list[1].args[-1], False)


class LegacyIsolationTests(unittest.TestCase):
    def test_legacy_endpoint_keeps_other_cartilla_and_string_lote_contract(self):
        from api.views.plantillas_views import SyncRegistroView

        other = SimpleNamespace(id=98, codigo="cartilla_fitosanidad", version=1)
        payload = {
            "payloadVersion": 1,
            "header": {"plantillaId": 98, "userId": USER.id, "loteId": "123", "fechaEjecucion": 1793048400000},
            "body": {"observaciones": "Prueba aislada de otra cartilla", "plantasEvaluadas": 10},
        }
        original = copy.deepcopy(payload)
        request = APIRequestFactory().post("/api/registros/sync/", {
            "clientRecordId": UUID, "templateKey": other.codigo, "payloadVersion": 1,
            "loteId": "123", "lat": -14.01959, "lon": -75.75971, "dataJson": payload,
        }, format="json")
        force_authenticate(request, user=USER)
        fake_row = SimpleNamespace(RegistroId=456, ServerRegistroId=None, save=Mock())
        with patch("api.views.plantillas_views.Plantilla.objects.get", return_value=other):
            with patch("api.views.plantillas_views.UserPlantilla.objects.filter") as assignment:
                assignment.return_value.exists.return_value = True
                with patch("api.views.plantillas_views.PlantillaRegistro.objects.filter") as rows:
                    rows.return_value.order_by.return_value.first.return_value = None
                    with patch("api.views.plantillas_views.PlantillaRegistro.objects.create", return_value=fake_row) as create:
                        with patch("api.views.plantillas_views.connection.cursor"):
                            with patch("api.services.brix_batch_sync.prepare_record", side_effect=AssertionError("batch invoked")):
                                response = SyncRegistroView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["syncStatus"], "synced")
        self.assertEqual(create.call_args.kwargs["PlantillaId"], 98)
        self.assertIs(type(create.call_args.kwargs["LoteId"]), int)
        self.assertEqual(create.call_args.kwargs["LoteId"], 123)
        self.assertEqual(json.loads(create.call_args.kwargs["DataJson"]), original)
        self.assertEqual(payload, original)


if __name__ == "__main__":
    unittest.main()
