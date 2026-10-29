"""Puente autenticado de cartillas TIC hacia el inventario único de DonTec Web."""
import os
import logging
import re

import requests
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.settings import api_settings
from config.jwt_signing import segura


def plantillas_tic_activas(usuario):
    from api.models import UserPlantilla
    return list(UserPlantilla.objects.filter(user_id=usuario.pk, estado='Activo', deleted_at__isnull=True,
        plantilla__is_active=True, plantilla__deleted_at__isnull=True, plantilla__codigo__startswith='cartilla_tic_')
        .values_list('plantilla__codigo', flat=True))


def configuracion_segura_tic():
    if not str(api_settings.ALGORITHM).startswith('HS'):
        return True
    return segura(api_settings.SIGNING_KEY)


def configuracion_pendiente():
    logging.getLogger(__name__).error('La API no terminó la preparación segura de sesiones TIC; revisar la configuración de arranque. No se habilitó una firma insegura.')
    return Response({'error': 'El servicio de Asignaciones TIC no está disponible. Tus borradores siguen guardados. Comunícate con el área TIC.'}, status=503)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def identidad_tic(request):
    if not configuracion_segura_tic():
        return configuracion_pendiente()
    if not getattr(request.user, 'active', False):
        return Response({'error': 'Usuario inactivo.'}, status=403)
    # El JWT autentica la cuenta de la app; la identidad web se resuelve en
    # PORTAL_AEI por su usuario validado, sin asumir que los IDs coinciden.
    from django.db import connections
    with connections['PORTAL_AEI'].cursor() as cursor:
        cursor.execute('SELECT id, username FROM dbo.user_user WHERE username = %s AND active = 1', [request.user.username])
        row = cursor.fetchone()
    if not row:
        return Response({'error': 'Cuenta web no activa.'}, status=403)
    response = Response({'id': row[0], 'username': row[1], 'tic_templates': plantillas_tic_activas(request.user)})
    response['Cache-Control'] = 'private, no-store'
    return response


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def puente_tic(request, recurso, ident=''):
    if not configuracion_segura_tic():
        return configuracion_pendiente()
    if not getattr(request.user, 'active', False):
        return Response({'error': 'Usuario inactivo.'}, status=403)
    permitidos = {'catalogo', 'formulario', 'equipos', 'trabajadores', 'recursos', 'detalle', 'documentos', 'pdf', 'confirmar', 'estado'}
    if recurso not in permitidos or (ident and not re.fullmatch(r'[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)*', ident)):
        return Response({'error': 'Operación no válida.'}, status=404)
    if request.method == 'POST' and recurso != 'confirmar':
        return Response({'error': 'Operación no válida.'}, status=405)
    if int(request.META.get('CONTENT_LENGTH') or 0) > 23 * 1024 * 1024:
        return Response({'error': 'El envío supera el tamaño permitido.'}, status=413)
    base = os.environ.get('DONTEC_TIC_WEB_URL', 'http://127.0.0.1:7000').rstrip('/')
    url = base + '/tic/asignaciones/movil/' + recurso + '/' + (ident + '/' if ident else '')
    headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION', ''), 'Accept': 'application/json, application/pdf'}
    data, files = None, None
    if request.method == 'POST':
        # Multipart: conservar valores repetidos de RAM/discos y fotos temporales.
        if not request.content_type.startswith('multipart/form-data'):
            return Response({'error': 'Se requiere un formulario multipart.'}, status=400)
        data = [(k, v) for k, valores in request.POST.lists() for v in valores]
        if any(f.size > 10 * 1024 * 1024 for f in request.FILES.values()):
            return Response({'error': 'Cada evidencia admite 10 MB.'}, status=400)
        files = [(k, (f.name, f.file, f.content_type)) for k, valores in request.FILES.lists() for f in valores]
    try:
        remote = requests.request(request.method, url, headers=headers,
            params=[(k, v) for k, valores in request.GET.lists() for v in valores],
            data=data, files=files or None, timeout=(4, 45), allow_redirects=False)
    except requests.RequestException:
        return Response({'error': 'No se pudo confirmar con DonTec Web. El borrador se conserva; reintenta la misma operación para evitar duplicados.'}, status=503)
    # Nunca devolver HTML de acceso ni una redirección como si fuera un PDF.
    tipo = remote.headers.get('Content-Type', '')
    if not (tipo.startswith('application/json') or tipo.startswith('application/pdf')):
        return Response({'error': 'El servidor web no tiene disponible la integración TIC. Revisa su despliegue.'}, status=503)
    response = HttpResponse(remote.content, status=remote.status_code, content_type=tipo)
    if 'Content-Disposition' in remote.headers:
        response['Content-Disposition'] = remote.headers['Content-Disposition']
    response['Cache-Control'] = 'private, no-store'
    return response
