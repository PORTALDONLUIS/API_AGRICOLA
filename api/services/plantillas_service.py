from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from api.models import Plantilla, UserPlantilla

def _parse_since(since_str: str):
    if not since_str:
        return None
    dt = parse_datetime(since_str)
    if not dt:
        return None
    if timezone.is_naive(dt):
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def obtener_plantillas_asignadas(user, since_str=None):
    since = _parse_since(since_str)

    up_qs = UserPlantilla.objects.filter(user=user).select_related("plantilla")

    print("🔎 USER:", user.id)
    print("🔎 TOTAL ASIGNACIONES (antes since):", up_qs.count())

    if since:
        up_qs = up_qs.filter(
            Q(updated_at__gte=since) |
            Q(deleted_at__gte=since) |
            Q(plantilla__updated_at__gte=since) |
            Q(plantilla__deleted_at__gte=since)
        )
        print("🔎 TOTAL ASIGNACIONES (con since):", up_qs.count())

    up_list = list(up_qs)
    print("📦 up_list LEN:", len(up_list))

    plantillas = [x.plantilla for x in up_list]
    print("📦 plantillas LEN:", len(plantillas))

    if plantillas:
        p = plantillas[0]
        print("🧪 EJEMPLO PLANTILLA:",
              p.id, p.codigo, p.nombre, p.is_active)

    return {
        "serverTime": timezone.now(),
        "plantillas": plantillas,
        "assignment_by_plantilla": {x.plantilla_id: x for x in up_list},
        "deleted": {
            "plantillas": [p.id for p in plantillas if p.deleted_at],
            "assignments": [x.id for x in up_list if x.deleted_at],
        },
    }

