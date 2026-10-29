import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from .jwt_signing import resolver_firma, segura, VARIABLE


class FirmaJWTTests(unittest.TestCase):
    def test_conserva_variable_segura_sin_tocar_archivos(self):
        key = 'synthetic-private-key-only-for-this-unit-test-123456789'
        with patch('config.jwt_signing._proteger') as proteger:
            self.assertEqual(resolver_firma('django-insecure-...', {VARIABLE:key}), key)
            proteger.assert_not_called()

    def test_conserva_secret_key_segura_existente(self):
        key = 'synthetic-legacy-secret-only-for-testing-1234567890'
        with patch('config.jwt_signing._proteger') as proteger:
            self.assertEqual(resolver_firma(key, {}), key)
            proteger.assert_not_called()

    def test_generacion_persistencia_y_reinicio(self):
        with tempfile.TemporaryDirectory(prefix='tic-jwt-test-') as ruta:
            carpeta = Path(ruta) / 'privado'
            key = resolver_firma('django-insecure-...', {}, carpeta)
            self.assertTrue(segura(key))
            self.assertGreaterEqual(len(key), 64)
            self.assertEqual(resolver_firma('django-insecure-...', {}, carpeta), key)
            self.assertTrue((carpeta/'dontec-jwt.env').exists())

    def test_reutiliza_archivo_transferido_previamente(self):
        with tempfile.TemporaryDirectory(prefix='tic-jwt-test-') as ruta:
            key = 'synthetic-existing-file-key-test-only-123456789012345'
            Path(ruta,'dontec-jwt.env').write_text(VARIABLE+'='+key+'\n',encoding='utf-8')
            self.assertEqual(resolver_firma('django-insecure-...',{},ruta),key)

    def test_configuracion_de_prueba_no_se_usa_para_firmar(self):
        with tempfile.TemporaryDirectory(prefix='tic-jwt-test-') as ruta:
            key = resolver_firma('django-insecure-...', {VARIABLE:'django-insecure-...'}, ruta)
            self.assertTrue(segura(key))
            self.assertNotEqual(key, 'django-insecure-...')

    def test_archivo_invalido_no_se_sobrescribe(self):
        with tempfile.TemporaryDirectory(prefix='tic-jwt-test-') as ruta:
            p = Path(ruta,'dontec-jwt.env'); p.write_text(VARIABLE+'=corta',encoding='utf-8')
            with self.assertRaises(ImproperlyConfigured):
                resolver_firma('django-insecure-...',{},ruta)
            self.assertEqual(p.read_text(encoding='utf-8'),VARIABLE+'=corta')

    def test_fallo_de_permisos_no_activa_una_firma_insegura(self):
        with tempfile.TemporaryDirectory(prefix='tic-jwt-test-') as ruta:
            with patch('config.jwt_signing._proteger',side_effect=PermissionError('denegado')):
                with self.assertRaises(ImproperlyConfigured):
                    resolver_firma('django-insecure-...',{},ruta)
            self.assertFalse(Path(ruta,'dontec-jwt.env').exists())

    def test_varios_procesos_de_arranque_reutilizan_la_misma_clave(self):
        with tempfile.TemporaryDirectory(prefix='tic-jwt-test-') as ruta:
            with patch('config.jwt_signing._proteger'):
                with ThreadPoolExecutor(max_workers=5) as pool:
                    claves = list(pool.map(lambda _: resolver_firma('django-insecure-...',{},ruta),range(5)))
            self.assertEqual(len(set(claves)),1)
            self.assertTrue(segura(claves[0]))

    def test_valida_placeholder_y_tamano(self):
        for key in ('',None,'corta','django-insecure-'+('x'*64),('x'*40)+'...'):
            self.assertFalse(segura(key))
        self.assertTrue(segura(b'x'*32))
