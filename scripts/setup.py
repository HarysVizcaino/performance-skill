"""Install the pinned, verified runtime in the skill's private directory."""
import hashlib
import io
import os
from pathlib import Path
import platform
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '2.3.0'
HASHES = {
    'linux-amd64': '39c3117b6af817592dcd0ce4242105c0a7af10948c2a425306f0be8f7a8a8ab1',
    'linux-arm64': '5ca3433e8201da72a284aaa241a1bb5fb47f4abb4e384d39410ddd8062f49b90',
    'macos-amd64': 'c83bb16f54f0676afa4ea235fd757f3892d307dbd1bd201450de83af31986654',
    'macos-arm64': 'b2417a3038edc5fe81dc178a889237724b595c5c9cfed875822008e46e862c7d',
    'windows-amd64': '112276d495e5741c968e2bc09ea6196099c1275bd6db9ee0875d173c7148ce43',
}


def verify(data, digest):
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('La descarga no supera la verificación de integridad.')


def runtime_path():
    return ROOT / '.runtime' / VERSION / ('engine.exe' if os.name == 'nt' else 'engine')


def install():
    system = {'Darwin': 'macos', 'Linux': 'linux', 'Windows': 'windows'}.get(platform.system())
    machine = {'x86_64': 'amd64', 'AMD64': 'amd64', 'arm64': 'arm64', 'aarch64': 'arm64'}.get(platform.machine())
    key = f'{system}-{machine}'
    if key not in HASHES:
        raise ValueError('Plataforma no compatible con esta instalación automática.')
    extension = 'tar.gz' if system == 'linux' else 'zip'
    archive = f'k6-v{VERSION}-{key}.{extension}'
    url = f'https://github.com/grafana/k6/releases/download/v{VERSION}/{archive}'
    request = urllib.request.Request(url, headers={'User-Agent': 'Performance/0.1.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(150 * 1024 * 1024 + 1)
    if len(data) > 150 * 1024 * 1024:
        raise ValueError('La descarga supera el tamaño permitido.')
    verify(data, HASHES[key])
    member = f'k6-v{VERSION}-{key}/k6' + ('.exe' if system == 'windows' else '')
    # Read only the executable; never extract archive-controlled paths.
    if extension == 'zip':
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            binary = bundle.read(member)
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as bundle:
            entry = bundle.getmember(member)
            if not entry.isfile():
                raise ValueError('El archivo de ejecución no es regular.')
            binary = bundle.extractfile(entry).read()
    target = runtime_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix('.download')
    temp.write_bytes(binary)
    temp.chmod(0o700)
    temp.replace(target)
    return target


if __name__ == '__main__':
    try:
        install()
        print('Performance: motor local preparado.')
    except Exception:
        print('No se pudo preparar el motor. Comprueba red, permisos y plataforma; la descarga debe superar la verificación de integridad.')
        raise SystemExit(2)
