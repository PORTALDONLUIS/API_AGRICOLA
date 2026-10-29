# Sesión persistente DonTec App

Cambio en feature/david-culqui de APP_AGRICOLA y API_AGRICOLA.

- La sesión del celular ya no vence a los 7/30 días. Se conservan las sesiones
  existentes aunque haya vencido su antigua fecha local.
- La API emite refresh firmado sin expiración temporal, identificado como
  persistent_session. El access conserva su expiración normal y se renueva.
- Al renovar, la API verifica firma, tipo de token, existencia y estado activo
  del usuario. No se aceptan access tokens como refresh ni firmas modificadas.
- Los refresh anteriores todavía válidos se convierten automáticamente.
  Si ya vencieron, se necesita iniciar sesión una última vez. No se resucitan
  credenciales expiradas. Cierre manual o borrado de datos requieren login.
- Red no disponible o error temporal del servidor no borra la sesión. Un
  rechazo de autenticación confirmado vuelve al login sin borrar muestras.
- No hay tablas nuevas, cambios de clave ni cambios en muestras o borradores.

## Activación

1. Integrar API_AGRICOLA y desplegar/reiniciar la API primero.
2. Integrar APP_AGRICOLA y generar un APK con versión/build superior al publicado.
3. Probar actualización sin desinstalar y publicar por release/version.json.
4. No revertir la API al código anterior mientras existan refresh persistentes:
   el validador anterior no admite estos tokens sin fecha.

## Validación local

API: python -m unittest api.test_persistent_session -v; python manage.py check.
App: flutter test test/persistent_session_test.dart --no-pub.
Se simulan antigüedad, migración, usuario inactivo, firma adulterada, concurrencia,
fallas temporales y cierre manual. No sustituyen prueba en celular y servidor.
