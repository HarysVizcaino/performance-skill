"""Run the performance workflow and display only the product report."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description='Performance: pruebas locales e informes de rendimiento.')
    parser.add_argument('--script', required=True, type=Path)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--engine', default=shutil.which('k6'))
    args = parser.parse_args()
    if not args.engine:
        parser.error('No se encontró el motor local de rendimiento. El agente debe preparar la dependencia.')
    script = args.script.resolve()
    if not script.is_file():
        parser.error('No existe el archivo de prueba indicado.')
    if args.config and not args.config.is_file():
        parser.error('No existe la configuración indicada.')
    output = args.output.resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error('El directorio de resultados ya existe. Usa uno nuevo para esta ejecución.')
    command = [args.engine, 'run', '-e', f'BASE_URL={args.base_url}', '-e', f'OUTPUT_DIR={output}']
    if args.config:
        command += ['-e', f'CONFIG={args.config.resolve()}']
    command.append(str(script))
    log = output / '.runtime.log'
    try:
        with log.open('x') as stream:
            log.chmod(0o600)
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                    env={**os.environ, 'K6_NO_USAGE_REPORT': 'true'})
    except OSError:
        print('No se pudo iniciar el motor local de rendimiento.', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('Prueba interrumpida; los resultados pueden estar incompletos.', file=sys.stderr)
        return 130
    (output / 'execution.json').write_text(json.dumps({'exitCode': result.returncode}, indent=2))
    report = output / 'report.md'
    if report.is_file():
        print(report.read_text())
    else:
        print('La prueba no generó un informe. El agente debe revisar el diagnóstico interno.', file=sys.stderr)
    print(f'Código de salida: {result.returncode}.')
    return (result.returncode if result.returncode >= 0 else 128 - result.returncode) or (0 if report.is_file() else 2)


if __name__ == '__main__':
    sys.exit(main())
