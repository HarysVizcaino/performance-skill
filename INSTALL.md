# Instalación de Performance

## Requisitos

- Claude Code o Codex con terminal habilitada.
- Git y Python 3.10+ (`python3` en macOS/Linux, `py -3` en Windows).
- Internet para la primera preparación del motor local.

Clona el repositorio en la carpeta correspondiente; el nombre final debe ser `performance`:

| Alcance | Claude Code | Codex |
|---|---|---|
| Personal | `~/.claude/skills/performance` | `~/.agents/skills/performance` |
| Proyecto | `.claude/skills/performance` | `.agents/skills/performance` |

Conserva todos los archivos. Si la carpeta ya existe, actualízala en lugar de superponer otra copia. Abre una sesión nueva tras instalar.

## Primera prueba

```text
/performance prueba mi API en http://localhost:3000 con un usuario durante 10 segundos. Revisa el proyecto para elegir un endpoint y genera un informe.
```

En Codex escribe `$performance`. Los detalles después del nombre son lenguaje natural: destino, rutas, acciones, carga, duración y objetivos.

El agente prepara la dependencia de ejecución con `python3 scripts/setup.py` desde la carpeta de la skill. El instalador descarga una versión fija, verifica su integridad y la guarda dentro de `.runtime/`; no instala paquetes globales ni solicita cuentas externas. Se respetan los permisos de tu entorno.

## Actualizar

Desde la carpeta instalada:

```sh
git pull --ff-only
python3 scripts/setup.py
```

Conserva tus pruebas personalizadas en el proyecto de la aplicación, no dentro de la instalación de la skill. El script de preparación también permite reparar una descarga incompleta.

## Resolver problemas

- **El comando no aparece:** verifica la ubicación y que `SKILL.md` esté directamente dentro de `performance`; abre una sesión nueva.
- **Falta Python:** instala Python 3.10+ y comprueba su disponibilidad en la terminal del agente.
- **No se prepara el motor:** verifica internet, permisos de escritura y plataforma compatible. El instalador no acepta descargas cuya integridad no coincida.
- **Responde con 301/302:** pide al agente que compruebe la URL canónica antes de probar. Las pruebas no siguen redirecciones automáticamente.
- **401/403:** prepara una cuenta de prueba y autenticación válida. No pegues tokens en el prompt ni los guardes en el repositorio.
- **429:** puede haber un límite de solicitudes. El informe no lo interpreta automáticamente como falta de CPU.
- **Prueba incompleta:** revisa el motivo y los tiempos; no la presentes como carga soportada.

La autenticación opcional se obtiene de `PERFORMANCE_BEARER_TOKEN` en el entorno. Los informes no contienen el token ni el cuerpo de las respuestas. El diagnóstico oculto está destinado al agente y debe revisarse antes de compartirlo.

Cada ejecución requiere una carpeta nueva. Los resultados anteriores no se sobrescriben.
