"""Fórmulas de Cosecha Uva v1, iguales al manual y al aplicativo."""
import re
from datetime import datetime

CLASSIFICATION = ('conformados', 'pampanos', 'semipaludos', 'paludos')
COLORS = ('verde', 'cremoso', 'ambar')
BERRIES = ('pudricion', 'partiduras', 'mediaLuna', 'oidium', 'danoMecanico')
DEFECTS = ('chanchitoBlanco', 'paloNegro', 'presenciaPolvo', 'presenciaAranaTela', 'bayasAcuosas', 'golpeSol', 'raquisLignificado', 'pediceloNecrosado', 'russet', 'descalibre', 'colapso')

COUNT_KEYS = CLASSIFICATION + COLORS + BERRIES + DEFECTS

def count(value):
    if value is None or value == '':
        return 0
    if isinstance(value, bool) or not re.fullmatch(r'[0-9]{1,6}', str(value)):
        raise ValueError('Las cantidades deben ser enteros de 0 a 999999.')
    return int(value)

def sample_metrics(body):
    def total(keys):
        return sum(count(body.get(key)) for key in keys)
    racimos, defectos = total(CLASSIFICATION), total(DEFECTS)
    sanos = max(0, racimos - defectos)
    restos = body.get('restosVegetales') or []
    if not isinstance(restos,list) or len(restos)>2 or len(set(restos))!=len(restos) or set(restos)-{'ZARCILLO','HOJAS'}:
        raise ValueError('Seleccione ZARCILLO, HOJAS o ninguna opción.')
    return dict(totalRacimos=racimos,totalRacimosColor=total(COLORS),
        racimosConDefectos=defectos,racimosSinDefectos=sanos,
        porcentajeConDefectos=defectos/racimos*100 if racimos else 0,
        porcentajeSinDefectos=sanos/racimos*100 if racimos else 0,
        totalBayasDefectuosas=total(BERRIES),restosVegetalesSiNo='SI' if restos else 'NO',
        restosVegetalesPresente=1 if restos else 0)

def summary(bodies):
    bodies=list(bodies)
    totals={key:0 for key in COUNT_KEYS+('totalRacimos','totalRacimosColor','racimosConDefectos','racimosSinDefectos','totalBayasDefectuosas','restosVegetalesPresente')}
    for body in bodies:
        metrics=sample_metrics(body)
        for key in COUNT_KEYS: totals[key]+=count(body.get(key))
        for key,value in metrics.items():
            if key in totals: totals[key]+=value
    n=len(bodies);racimos=totals['totalRacimos']
    return dict(totals,muestras=n,
        porcentajeConDefectos=totals['racimosConDefectos']/racimos*100 if racimos else 0,
        porcentajeSinDefectos=totals['racimosSinDefectos']/racimos*100 if racimos else 0,
        restosVegetalesPorcentaje=totals['restosVegetalesPresente']/n*100 if n else 0,
        promedios={key:totals[key]/n if n else 0 for key in COUNT_KEYS+('totalRacimos',)})

def validate_payload(payload):
    body=payload['body'];header=payload['header']
    for key in COUNT_KEYS: count(body.get(key))
    metrics=sample_metrics(body)
    if not metrics['totalRacimos']:
        raise ValueError('Ingrese al menos un racimo en la clasificación.')
    for key in ('loteId','campaniaId'):
        if header.get(key) in (None,''):
            raise ValueError('Seleccione lote y campaña.')
    for key in ('operario','supervisor'):
        value=body.get(key)
        if isinstance(value,bool) or not str(value).isdigit() or int(value)<=0:
            raise ValueError('Seleccione operario y supervisor.')
    for key,fmt in (('fecha','%d/%m/%Y'),('hora','%H:%M')):
        value=body.get(key)
        if not isinstance(value,str) or datetime.strptime(value,fmt).strftime(fmt)!=value:
            raise ValueError('Revise fecha y hora.')
    for key,limit in (('temperatura',80),('codigoLimpiador',100),('observaciones',4000)):
        value=body.get(key)
        if value is not None and (not isinstance(value,str) or len(value)>limit):
            raise ValueError('Revise '+key+'.')
    fotos=body.get('fotos') or []
    if not isinstance(fotos,list) or len(fotos)>3:
        raise ValueError('Se admiten hasta tres fotografías.')
    slots=set()
    for photo in fotos:
        if not isinstance(photo,dict) or type(photo.get('slot')) is not int or not 1<=photo['slot']<=3 or photo['slot'] in slots:
            raise ValueError('Fotografía inválida o repetida.')
        slots.add(photo['slot'])
    # Verificar, no reserializar: el hash y el JSON original deben conservarse.
    for key,value in metrics.items():
        sent=body.get(key)
        if isinstance(value,str): valid=sent==value
        else: valid=not isinstance(sent,bool) and isinstance(sent,(int,float)) and abs(sent-value)<0.000001
        if not valid: raise ValueError('El cálculo '+key+' no coincide con la muestra.')
