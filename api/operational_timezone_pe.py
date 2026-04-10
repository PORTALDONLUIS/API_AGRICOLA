"""Zona operativa Perú (UTC−5, IANA America/Lima; sin DST)."""

from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from typing import Optional, Union
from zoneinfo import ZoneInfo

TZ_PERU = ZoneInfo("America/Lima")


def fecha_ejecucion_en_zona_peru_desde_epoch_ms(
    ms: Optional[Union[int, float]],
) -> Optional[datetime]:
    """
    Epoch UTC en ms (como envía el móvil) → datetime **en America/Lima** con la
    hora civil real (-5): misma hora de reloj que vio el usuario al guardar
    si el dispositivo tenía la hora correcta.
    """
    if ms is None:
        return None
    try:
        x = float(ms)
    except (TypeError, ValueError):
        return None
    if x <= 0:
        return None
    sec = x / 1000.0
    try:
        # Wall clock en Perú para ese instante universal
        return datetime.fromtimestamp(sec, tz=TZ_PERU)
    except (OverflowError, ValueError, OSError):
        return None


def fecha_ejecucion_naive_lima_desde_epoch_ms(
    ms: Optional[Union[int, float]],
) -> Optional[datetime]:
    """Misma hora que en Perú, **sin** tzinfo, para escribir literal en SQL Server."""
    aware = fecha_ejecucion_en_zona_peru_desde_epoch_ms(ms)
    if aware is None:
        return None
    return aware.replace(tzinfo=None)


def instante_naive_lima_desde_utc_aware(ahora_utc_aware: datetime) -> datetime:
    """Convierte un instante UTC (p. ej. timezone.now()) a reloj civil Perú naive."""
    if ahora_utc_aware.tzinfo is None:
        ahora_utc_aware = ahora_utc_aware.replace(tzinfo=dt_timezone.utc)
    return ahora_utc_aware.astimezone(TZ_PERU).replace(tzinfo=None)
