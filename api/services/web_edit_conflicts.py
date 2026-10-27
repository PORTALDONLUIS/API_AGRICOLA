"""Translate only the known SQL protection errors, without exposing SQL details."""
def web_edit_conflict(error):
    text=str(error)
    if '(51012)' in text or 'El lote fue corregido en WEB' in text:
        return 'El lote fue corregido en DonTec Web. Actualice la muestra desde la nube antes de volver a sincronizar.'
    if '(51010)' in text or 'La muestra tiene correcciones WEB' in text:
        return 'La muestra fue corregida en DonTec Web. Actualice su copia antes de volver a sincronizar.'
    return None
