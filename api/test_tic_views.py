"""Pruebas sin SQL ni red: python -m unittest api.test_tic_views -v"""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch, MagicMock
from django.conf import settings
if not settings.configured:
    settings.configure(SECRET_KEY='tic-tests-synthetic-only', INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes'], DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}, REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':[], 'UNAUTHENTICATED_USER':None})
    import django
    django.setup()
from rest_framework.test import APIRequestFactory, force_authenticate
from api.views.tic_views import puente_tic, identidad_tic

class TicBridgeTests(unittest.TestCase):
    def setUp(self):
        signing = patch('api.views.tic_views.api_settings', SimpleNamespace(ALGORITHM='HS256', SIGNING_KEY='synthetic-tic-test-key-with-more-than-32-bytes-only'))
        assignments = patch('api.views.tic_views.plantillas_tic_activas', return_value=['cartilla_tic_equipos'])
        assignments.start()
        self.addCleanup(assignments.stop)
        signing.start()
        self.addCleanup(signing.stop)

    @patch('api.views.tic_views.requests.request')
    def test_clave_de_prueba_bloquea_tic_sin_afectar_otros_endpoints(self, remote):
        with patch('api.views.tic_views.api_settings.SIGNING_KEY', 'django-insecure-...'):
            self.assertEqual(puente_tic(self.request(), recurso='catalogo').status_code,503)
            self.assertEqual(identidad_tic(self.request()).status_code,503)
        remote.assert_not_called()

    def request(self, method='get', data=None, active=True):
        factory=APIRequestFactory()
        req=getattr(factory,method)('/api/tic/asignaciones/catalogo/', data or {}, format='multipart', HTTP_AUTHORIZATION='Bearer test-signed')
        force_authenticate(req, user=SimpleNamespace(pk=9,username='DCULQUI',active=active,is_authenticated=True))
        return req
    @patch('api.views.tic_views.requests.request')
    def test_transmite_token_y_pdf_sin_redireccion(self, remote):
        remote.return_value=Mock(status_code=200, content=b'%PDF-test', headers={'Content-Type':'application/pdf','Content-Disposition':'attachment; filename="tic.pdf"'})
        result=puente_tic(self.request(), recurso='pdf', ident='equipo/1')
        self.assertEqual(result.status_code,200)
        self.assertTrue(result.content.startswith(b'%PDF-'))
        self.assertEqual(remote.call_args.kwargs['headers']['Authorization'],'Bearer test-signed')
        self.assertFalse(remote.call_args.kwargs['allow_redirects'])
    @patch('api.views.tic_views.requests.request')
    def test_no_admite_html_como_pdf(self, remote):
        remote.return_value=Mock(status_code=200, content=b'<html>login</html>', headers={'Content-Type':'text/html'})
        self.assertEqual(puente_tic(self.request(), recurso='pdf', ident='equipo/1').status_code,503)
    @patch('api.views.tic_views.requests.request')
    def test_post_conserva_ram_repetida(self, remote):
        remote.return_value=Mock(status_code=200,content=b'{"ok":true}',headers={'Content-Type':'application/json'})
        result=puente_tic(self.request('post',{'ram_capacidad':['8','16'],'operacion_id':'uuid'}), recurso='confirmar')
        self.assertEqual(result.status_code,200)
        self.assertEqual([v for k,v in remote.call_args.kwargs['data'] if k=='ram_capacidad'],['8','16'])
    @patch('api.views.tic_views.requests.request')
    def test_usuario_inactivo_y_destino_invalido_no_llegan_a_web(self, remote):
        self.assertEqual(puente_tic(self.request(active=False),recurso='catalogo').status_code,403)
        self.assertEqual(puente_tic(self.request(),recurso='pdf',ident='../secreto').status_code,404)
        self.assertEqual(puente_tic(self.request(),recurso='otra').status_code,404)
        remote.assert_not_called()
    def test_identidad_resuelve_el_id_real_de_portal(self):
        cursor=MagicMock()
        cursor.__enter__.return_value.fetchone.return_value=(4023,'DCULQUI')
        con=MagicMock(); con.cursor.return_value=cursor
        with patch('django.db.connections', {'PORTAL_AEI':con}):
            response=identidad_tic(self.request())
        self.assertEqual(response.data,{'id':4023,'username':'DCULQUI','tic_templates':['cartilla_tic_equipos']})
        self.assertEqual(cursor.__enter__.return_value.execute.call_args.args[1],['DCULQUI'])
    def test_sin_sesion_no_autentica(self):
        request=APIRequestFactory().get('/api/tic/identidad/')
        self.assertEqual(identidad_tic(request).status_code,403)
