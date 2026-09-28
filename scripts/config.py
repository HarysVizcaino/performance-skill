"""Validate workload before starting any traffic."""
import math
import re
from urllib.parse import urlsplit


def seconds(value):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)(ms|s|m|h)', str(value))
    if not match:
        raise ValueError('Duración inválida: usa 10s, 2m o 1h.')
    result = float(match[1]) * {'ms': .001, 's': 1, 'm': 60, 'h': 3600}[match[2]]
    if not math.isfinite(result) or result <= 0:
        raise ValueError('La duración debe ser positiva.')
    return result


def number(value, label, minimum=0, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum or (integer and int(value) != value):
        raise ValueError(f'{label}: valor numérico inválido.')
    return value


def validate(config, origin, max_vus=100, max_duration=300, max_rate=100):
    try:
        parsed = urlsplit(origin)
        invalid = (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None
                   or parsed.password is not None or parsed.path not in ('', '/') or parsed.query or parsed.fragment
                   or any(c.isspace() for c in origin) or '\\' in origin)
        _ = parsed.port
    except ValueError:
        invalid = True
    if invalid:
        raise ValueError('El destino debe ser un origen HTTP(S), sin credenciales, ruta ni parámetros.')
    duration = seconds(config.get('duration'))
    if duration > max_duration:
        raise ValueError('La duración supera el límite autorizado del ejecutor.')
    mode = config.get('mode')
    if mode == 'vus':
        if number(config.get('vus'), 'Usuarios', 1, True) > max_vus:
            raise ValueError('La carga supera el límite autorizado de usuarios.')
    elif mode == 'arrival':
        if number(config.get('rate'), 'Recorridos/s', 1, True) > max_rate:
            raise ValueError('La tasa supera el límite autorizado.')
        initial = number(config.get('preAllocatedVUs'), 'Usuarios iniciales', 1, True)
        ceiling = number(config.get('maxVUs'), 'Usuarios máximos', 1, True)
        if initial > ceiling or ceiling > max_vus:
            raise ValueError('El número de usuarios de llegada excede sus límites.')
    else:
        raise ValueError('El modelo debe ser vus o arrival.')
    for key in ('p95Ms', 'p99Ms'):
        number(config.get(key), key, .001)
    if config['p99Ms'] < config['p95Ms']:
        raise ValueError('El límite p99 debe ser igual o mayor que p95.')
    if number(config.get('errorRate'), 'Tasa de errores') > 1:
        raise ValueError('La tasa de errores debe estar entre 0 y 1.')
    routes = config.get('routes')
    if not isinstance(routes, list) or not 1 <= len(routes) <= 50:
        raise ValueError('Configura entre 1 y 50 pasos por recorrido.')
    names = set()
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError('Cada paso debe ser un objeto.')
        name = route.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name) or name in names:
            raise ValueError('Los pasos necesitan nombres únicos y simples (hasta 64 caracteres).')
        names.add(name)
        path = route.get('path')
        if not isinstance(path, str) or not path.startswith('/') or path.startswith('//') or any(c in path for c in '\r\n#\\'):
            raise ValueError('Cada ruta debe pertenecer al origen indicado.')
        if not 200 <= number(route.get('expectedStatus'), 'Estado HTTP', 200, True) <= 599:
            raise ValueError('Estado HTTP inválido.')
        pause = number(route.get('pauseSeconds'), 'Pausa')
        if pause > 30 or (mode == 'arrival' and pause != 0):
            raise ValueError('Usa pausas de hasta 30 segundos, o cero para llegadas constantes.')
        if 'jsonField' in route and (not isinstance(route['jsonField'], str) or not route['jsonField'] or 'equals' not in route):
            raise ValueError('La comprobación JSON requiere un campo y un valor esperado.')
        if 'contains' in route and (not isinstance(route['contains'], str) or not route['contains']):
            raise ValueError('La comprobación de contenido necesita texto no vacío.')
    return duration
