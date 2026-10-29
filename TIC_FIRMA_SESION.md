# Activación de sesión TIC — 29/10/2026

La configuración privada no viaja al hacer push/pull. Una API desplegada con
la clave de prueba devolvía 503 al abrir todas las cartillas TIC.

La API ahora conserva la variable DONTEC_JWT_SIGNING_KEY si es segura, o una
SECRET_KEY segura preexistente. Si ambas son de prueba, reutiliza el archivo
privado del usuario .donTec-seguridad/dontec-jwt.env o lo prepara una sola vez
con 48 bytes aleatorios. No se imprime ni se guarda en Git. El proceso usa
siempre la misma firma al reiniciar y mantiene la protección de TIC.
La carpeta se protege para la cuenta del proceso y SYSTEM en Windows.
Un fallo de permisos o archivo inválido detiene el arranque; no se admite una
firma insegura como alternativa.

Todas las cartillas siguen usando la sesión JWT habitual de la misma API.
Si cambia la firma de prueba, los celulares deben cerrar e iniciar sesión una
vez. No deben desinstalar, borrar almacenamiento ni perder registros pendientes.
Las muestras y los borradores del celular permanecen guardados.

## Solución inmediata en el servidor, incluso antes de desplegar este arreglo

Detener la API con Ctrl+C. Desde API_AGRICOLA, con la misma cuenta que inicia
el servicio, ejecutar:

    python scripts/configurar_jwt_seguro.py --aplicar
    python manage.py runserver 0.0.0.0:8000

El primer comando ya forma parte del despliegue TIC anterior. Configura solo
la firma JWT y respalda el .env anterior fuera de Git. No requiere copiar una
clave por chat ni cambiar SQL ni regenerar el APK.
Para varias instancias o cuentas de servicio, instalar la misma firma privada
mediante --importar o la variable de entorno, antes de iniciar los procesos.
Mantener la cuenta del servicio y su configuración al reiniciar.

Después de subir este cambio a main y desplegarlo, el arranque normal prepara
la firma privada cuando falta; no hace falta repetir la configuración manual.
La tabla de inventario y los permisos no cambian con esta corrección.

Pruebas: python -m unittest config.test_jwt_signing api.test_tic_views -v.
La comprobación del servidor operativo requiere reiniciar su proceso y volver
a iniciar sesión en un celular; las pruebas locales no sustituyen ese paso.


## Acceso sencillo para los usuarios

En el celular solo se requiere una cuenta activa, iniciar sesión y tener la
cartilla TIC asignada. La web deriva las acciones móviles de esa asignación
para el request actual, sin pedir permisos Django adicionales ni modificar
roles permanentes de la cuenta. Los permisos de acceso web se mantienen.
La asignación y su revocación se verifican nuevamente en cada solicitud.
No se agregan claves por usuario ni por cartilla, ni se necesita otro APK.

Desplegar los cambios de API_AGRICOLA y DASHBOARD_DONLUIS y reiniciar ambos
procesos. La configuración interna queda automática al arrancar la API.
