"""Compare two complete runs of exactly the same configured workload."""
import argparse
import json
from pathlib import Path


def compare(before, after):
    runs = []
    for folder in (before, after):
        execution = json.loads((folder / 'execution.json').read_text(encoding='utf-8'))
        summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
        if execution['status'] not in ('COMPLETADA', 'INCUMPLE OBJETIVOS'):
            raise ValueError('No se pueden comparar ejecuciones incompletas.')
        runs.append((execution, summary))
    if not runs[0][0].get('workloadFingerprint') or runs[0][0]['workloadFingerprint'] != runs[1][0].get('workloadFingerprint'):
        raise ValueError('Destino o configuración diferentes: las pruebas no son comparables.')
    lines = ['# Comparación de rendimiento', '', '| Métrica | Antes | Después | Cambio (%) |', '|---|---:|---:|---:|']
    for name, metric, field in [('Solicitudes/s', 'http_reqs', 'rate'), ('p95 (ms)', 'http_req_duration', 'p(95)'),
                                ('p99 (ms)', 'http_req_duration', 'p(99)'), ('Tasa de errores', 'http_req_failed', 'rate')]:
        a, b = [run[1]['metrics'][metric]['values'][field] for run in runs]
        change = f'{(b-a)/a*100:+.2f}' if a else 'N/D (base cero)'
        lines.append(f'| {name} | {a:.4f} | {b:.4f} | {change} |')
    lines += ['', 'Mismo destino y configuración. Verifica además dataset, caché, identidades y recursos del generador; la huella no acredita igualdad del entorno.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compara dos informes de Performance.')
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    args = parser.parse_args()
    try:
        print(compare(args.before, args.after))
    except (OSError, ValueError, KeyError, TypeError):
        parser.exit(2, 'No se pudieron comparar las pruebas: verifica que estén completas, tengan el mismo destino/configuración y contengan todas las métricas.\n')
