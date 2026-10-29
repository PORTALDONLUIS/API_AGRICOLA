"""Firma JWT persistente por servidor, sin claves privadas dentro de Git."""
import os
import secrets
import subprocess
import time
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

VARIABLE = 'DONTEC_JWT_SIGNING_KEY'


def segura(key):
    raw = key if isinstance(key, bytes) else str(key or '').encode('utf-8')
    return len(raw) >= 32 and not raw.startswith(b'django-insecure-') and b'...' not in raw


def _proteger(directorio):
    if os.name != 'nt':
        directorio.chmod(0o700)
        return
    dominio = os.environ.get('USERDOMAIN', '')
    nombre = os.environ.get('USERNAME', '')
    if not nombre:
        raise ImproperlyConfigured('No se identificó la cuenta del proceso para proteger la firma JWT.')
    principal = (dominio + '\\' if dominio else '') + nombre
    subprocess.run(['icacls', str(directorio), '/inheritance:r', '/grant:r',
                    principal + ':(OI)(CI)F', 'SYSTEM:(OI)(CI)F'], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)


def _leer(archivo):
    # Otro proceso puede estar terminando la primera escritura de 64 caracteres.
    for _ in range(10):
        contenido = archivo.read_text(encoding='utf-8-sig')
        for linea in contenido.splitlines():
            if linea.startswith(VARIABLE + '='):
                key = linea.split('=', 1)[1].strip().strip('\"\'')
                if segura(key):
                    return key
        if contenido.strip():
            break
        time.sleep(0.05)
    raise ImproperlyConfigured('La firma JWT privada no es válida. Ejecuta scripts/configurar_jwt_seguro.py --aplicar con la cuenta que inicia la API. No se sobrescribió el archivo privado.')


def resolver_firma(secret_key, entorno=None, directorio_privado=None):
    entorno = os.environ if entorno is None else entorno
    configurada = entorno.get(VARIABLE)
    if segura(configurada):
        return configurada
    # Conservar una firma preexistente segura evita cierres de sesión innecesarios.
    if segura(secret_key):
        return secret_key
    carpeta = Path(directorio_privado) if directorio_privado is not None else Path.home() / '.donTec-seguridad'
    archivo = carpeta / 'dontec-jwt.env'
    try:
        carpeta.mkdir(mode=0o700, parents=True, exist_ok=True)
        _proteger(carpeta)
        if archivo.exists():
            return _leer(archivo)
        key = secrets.token_urlsafe(48)
        try:
            fd = os.open(str(archivo), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return _leer(archivo)
        with os.fdopen(fd, 'w', encoding='utf-8') as destino:
            destino.write(VARIABLE + '=' + key + '\n')
            destino.flush()
            os.fsync(destino.fileno())
        return key
    except (OSError, subprocess.SubprocessError) as error:
        raise ImproperlyConfigured('No se pudo preparar la firma JWT privada. Revisa permisos de .donTec-seguridad con la cuenta que inicia la API; no se usará una clave insegura.') from error
