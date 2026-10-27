"""Cosecha Uva: SQLite en memoria; sin conexiones ni credenciales reales."""
import json
import uuid
from types import SimpleNamespace
from unittest.mock import patch
from api import test_brix_batch as legacy
from api.services.cosecha_uva import sample_metrics
from api.services.brix_batch_codec import canonical_revision
from api.services.brix_batch_sync import prepare_record,BatchRecordError
from api.models import PlantillaRegistro
from rest_framework.test import APIRequestFactory,force_authenticate
from api.views.brix_batch_views import SyncBrixBatchView

TEMPLATE=SimpleNamespace(id=101,codigo='cartilla_cosecha_uva',version=1)
def block(start=1,size=50):
    rows=[]
    for i in range(start,start+size):
        body=dict(conformados=i%7+1,paloNegro=1,pudricion=2,operario='3',supervisor='4',
            fecha='27/10/2026',hora='09:00',restosVegetales=['HOJAS'],
            fotos=[{'slot':1,'localPath':'offline/photo.jpg','serverUrl':None}])
        body.update(sample_metrics(body))
        payload=dict(payloadVersion=1,header=dict(userId=7,plantillaId=101,loteId='123',
            campaniaId='2026',fechaEjecucion=1793109600000,lat=-14.01959,lon=-75.75971),body=body)
        rows.append(dict(clientRecordId=str(uuid.UUID(int=i)),payloadVersion=1,context=0,
            revision=canonical_revision(TEMPLATE.codigo,1,payload),body=body))
    return dict(protocolVersion=1,plantillaId=101,key=TEMPLATE.codigo,plantillaVersion=1,
        contexts=[dict(header=payload['header'],body={})],records=rows)

class CosechaStoreTests(legacy.StoreTests):
    def post_cosecha(self,data,assigned=True):
        request=APIRequestFactory().post('/api/registros/sync-batch/',data,format='json')
        force_authenticate(request,user=legacy.USER)
        with patch('api.views.brix_batch_views.Plantilla.objects.get',return_value=TEMPLATE), \
             patch('api.views.brix_batch_views.UserPlantilla.objects.filter') as permissions:
            permissions.return_value.exists.return_value=assigned
            return SyncBrixBatchView.as_view()(request)

    def test_1500_cosecha_samples_retry_without_duplicates_and_preserve_photos(self):
        packets=[block(i,min(50,1501-i)) for i in range(1,1501,50)]
        for packet in packets:
            response=self.post_cosecha(packet)
            self.assertEqual(response.status_code,200,response.data)
            self.assertTrue(all(r['status']=='synced' for r in response.data['results']))
        self.assertEqual(PlantillaRegistro.objects.count(),1500)
        for packet in packets:
            response=self.post_cosecha(packet)
            self.assertTrue(all(r['status']=='synced' for r in response.data['results']))
        self.assertEqual(PlantillaRegistro.objects.count(),1500)
        stored=json.loads(PlantillaRegistro.objects.order_by('RegistroId').first().DataJson)
        self.assertEqual(stored['body'],packets[0]['records'][0]['body'])
        self.assertEqual(stored['header']['loteId'],'123')
        self.assertEqual(stored['body']['fotos'][0]['localPath'],'offline/photo.jpg')
        self.assertEqual(stored['body']['totalBayasDefectuosas'],2)

    def test_new_cartilla_requires_assignment_and_matching_template(self):
        response=self.post_cosecha(block(size=1),assigned=False)
        self.assertEqual(response.status_code,403)
        data=block(size=1);data['key']='cartilla_brix_moscatel'
        self.assertEqual(self.post_cosecha(data).status_code,400)
        self.assertEqual(PlantillaRegistro.objects.count(),0)

    def test_invalid_formula_rejected_before_writing(self):
        data=block(size=1);data['records'][0]['body']['totalRacimos']=999
        payload=dict(payloadVersion=1,header=data['contexts'][0]['header'],body=data['records'][0]['body'])
        data['records'][0]['revision']=canonical_revision(TEMPLATE.codigo,1,payload)
        response=self.post_cosecha(data)
        self.assertEqual(response.data['results'][0]['status'],'error')
        self.assertEqual(PlantillaRegistro.objects.count(),0)
