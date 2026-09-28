"""Bounded local execution; raw diagnostics stay private."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import signal
import subprocess
import sys
import time

from config import validate
from setup import runtime_path

ROOT = Path(__file__).resolve().parents[1]


def stop(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        process.terminate()
    else:
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def finalize(output, code, elapsed, expected, config, origin, reason):
    summary_file = output / 'summary.json'
    try:
        summary = json.loads(summary_file.read_text(encoding='utf-8'))
        enough = summary['metrics']['iterations']['values']['count'] > 0
        actual = summary['actualDurationMs'] / 1000
        duration_ok = actual >= expected - .15
        thresholds_ok = summary['status'] == 'UMBRALES CUMPLIDOS'
    except (OSError, ValueError, KeyError, TypeError):
        enough, duration_ok, thresholds_ok = False, False, False
    status = ('COMPLETADA' if code == 0 and enough and duration_ok and thresholds_ok and not reason
              else 'INCUMPLE OBJETIVOS' if code == 99 and enough and duration_ok and not reason
              else 'INCOMPLETA')
    result_code = code or (0 if status == 'COMPLETADA' else 2)
    if result_code < 0:
        result_code = 128 - result_code
    fingerprint = hashlib.sha256(json.dumps({'origin': origin.rstrip('/'), 'config': config}, sort_keys=True).encode()).hexdigest()
    execution = {'status': status, 'exitCode': result_code, 'runtimeExitCode': code,
                 'elapsedSeconds': round(elapsed, 3), 'plannedSeconds': expected,
                 'reason': reason, 'workloadFingerprint': fingerprint}
    (output / 'execution.json').write_text(json.dumps(execution, indent=2), encoding='utf-8')
    report = output / 'report.md'
    content = report.read_text(encoding='utf-8') if report.exists() else '# Informe de rendimiento\n\nNo se obtuvo un resumen válido.\n'
    content += f'\n## Ejecución\n\n**{status}** · Código de salida: {result_code}.\n'
    if reason:
        content += f'\nMotivo: {reason}.\n'
    report.write_text(content, encoding='utf-8')
    print(content)
    return result_code


def main():
    parser = argparse.ArgumentParser(description='Performance: pruebas e informes de rendimiento.')
    parser.add_argument('--script', type=Path, default=ROOT / 'assets/journey.js')
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--engine', type=Path, default=runtime_path())
    parser.add_argument('--max-vus', type=int, default=100)
    parser.add_argument('--max-duration', type=int, default=300)
    parser.add_argument('--max-rate', type=int, default=100)
    args = parser.parse_args()
    script = args.script.resolve()
    config_path = (args.config or script.parent / 'workload.json').resolve()
    try:
        config = json.loads(config_path.read_text(encoding='utf-8'))
        duration = validate(config, args.base_url, args.max_vus, args.max_duration, args.max_rate)
    except (OSError, ValueError, TypeError, AttributeError) as error:
        message = str(error) if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError) else 'No se pudo leer una configuración válida.'
        parser.error(message)
    if not script.is_file():
        parser.error('No existe el archivo de prueba indicado.')
    if not args.engine.is_file():
        parser.error('Prepara el motor local con scripts/setup.py antes de ejecutar.')
    output = args.output.resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error('El directorio de resultados ya existe. Usa uno nuevo.')
    env = {k: v for k, v in os.environ.items() if not k.startswith('K6_')}
    env['K6_NO_USAGE_REPORT'] = 'true'
    command = [str(args.engine.resolve()), 'run', '--config', str(ROOT / 'assets/engine.json'),
               '-e', f'BASE_URL={args.base_url}', '-e', f'OUTPUT_DIR={output}',
               '-e', f'CONFIG={config_path}', str(script)]
    started = time.monotonic()
    code, reason = 2, None
    process = None
    log = output / '.runtime.log'
    try:
        with log.open('x', encoding='utf-8') as stream:
            log.chmod(0o600)
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, env=env,
                                       start_new_session=os.name != 'nt')
            code = process.wait(timeout=duration + 15)
    except subprocess.TimeoutExpired:
        stop(process)
        code, reason = 124, 'Se alcanzó el tiempo máximo de ejecución'
    except KeyboardInterrupt:
        if process:
            stop(process)
        code, reason = 130, 'Prueba cancelada por el operador'
    except OSError:
        code, reason = 2, 'No se pudo iniciar el motor local'
    if log.exists():
        diagnostic = log.read_text(encoding='utf-8', errors='replace')
        token = os.environ.get('PERFORMANCE_BEARER_TOKEN')
        if token:
            diagnostic = diagnostic.replace(token, '[credencial omitida]')
        diagnostic = re.sub(r'https?://[^\s"<>]+', '[destino omitido]', diagnostic)
        log.write_text(diagnostic, encoding='utf-8')
    return finalize(output, code, time.monotonic() - started, duration, config, args.base_url, reason)


if __name__ == '__main__':
    sys.exit(main())
