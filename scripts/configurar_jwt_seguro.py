"""Configurar firma JWT sin imprimir la clave. Con --aplicar modifica solo esa variable."""
import argparse
import os
import re
import secrets
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

VAR = 'DONTEC_JWT_SIGNING_KEY'
BASE = Path(__file__).resolve().parents[1]
ENV = BASE / '.env'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--aplicar', action='store_true')
parser.add_argument('--importar', type=Path, help='Archivo privado con la misma clave preparada en la laptop')
args = parser.parse_args()
if subprocess.run(['git','ls-files','--error-unmatch','.env'], cwd=str(BASE), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('.env está registrado en Git. Detenido para no publicar secretos.')
raw = ENV.read_text(encoding='utf-8-sig') if ENV.exists() else ''
pattern = re.compile(r'^' + VAR + r'=(.*)$', re.MULTILINE)
found = pattern.search(raw)
old = found.group(1).strip().strip('\"\'') if found else ''
def valido(key):
    return len(key.encode('utf-8')) >= 48 and bool(re.fullmatch(r'[A-Za-z0-9_-]+', key)) and not key.startswith(('django-insecure','synthetic'))
if not args.aplicar:
    print('Solo revisión. Firma privada local configurada:', valido(old))
    raise SystemExit(0)
private = Path.home() / '.donTec-seguridad'
private.mkdir(exist_ok=True)
if os.name == 'nt':
    principal = os.environ.get('USERDOMAIN','') + '\\' + os.environ['USERNAME']
    subprocess.run(['icacls',str(private),'/inheritance:r','/grant:r',principal+':(OI)(CI)F','SYSTEM:(OI)(CI)F'], check=True, stdout=subprocess.DEVNULL)
if args.importar:
    incoming = args.importar.read_text(encoding='utf-8-sig')
    match = pattern.search(incoming)
    if not match or not valido(match.group(1).strip()):
        raise SystemExit('Archivo de firma no válido. No se modificó .env.')
    key = match.group(1).strip()
else:
    key = old if valido(old) else secrets.token_urlsafe(48)
if ENV.exists():
    shutil.copy2(str(ENV), str(private / ('api-env-respaldo-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.env')))
if found:
    updated = pattern.sub(lambda match: VAR + '=' + key, raw)
else:
    updated = raw.rstrip('\n') + '\n' + VAR + '=' + key + '\n'
ENV.write_text(updated,encoding='utf-8')
transfer = private / 'dontec-jwt.env'
transfer.write_text(VAR+'='+key+'\n',encoding='utf-8')
(private / 'INSTALAR_EN_SERVIDOR.txt').write_text(
    'Copiar dontec-jwt.env de forma privada al servidor. No subirlo a GitHub.\n'
    'En API_AGRICOLA ejecutar: python scripts/configurar_jwt_seguro.py --aplicar --importar "RUTA_PRIVADA/dontec-jwt.env"\n'
    'Reiniciar API. Los celulares deben iniciar sesión una vez; sus muestras/borradores se conservan.\n',encoding='utf-8')
print('Firma JWT segura configurada. No se mostraron ni publicaron claves.')
print('Archivo privado para instalar la misma firma en servidor:',transfer)
