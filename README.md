# Performance

**Describe la prueba. Recibe un informe de rendimiento.**

Una skill para Claude Code y Codex que convierte instrucciones en lenguaje natural en pruebas HTTP reproducibles para tu web o API, ejecutadas desde tu computadora.

```text
/performance prueba mi web con hasta 100 usuarios simultáneos durante 2 minutos. Navega por la página principal y los artículos. No envíes formularios. Genera un informe.
```

En Codex, usa `$performance` seguido de los mismos detalles.

## Instalar

Necesitas Git, Python 3.10 o posterior y Claude Code o Codex con acceso a una terminal. La primera preparación requiere internet. No necesitas una cuenta de un servicio de pruebas; el uso del agente y de tu infraestructura conserva sus costos habituales.

**Claude Code** — macOS/Linux:

```sh
git clone https://github.com/HarysVizcaino/performance-skill.git ~/.claude/skills/performance
```

**Codex** — macOS/Linux:

```sh
git clone https://github.com/HarysVizcaino/performance-skill.git ~/.agents/skills/performance
```

En Windows PowerShell usa, respectivamente:

```powershell
git clone https://github.com/HarysVizcaino/performance-skill.git "$HOME/.claude/skills/performance"
git clone https://github.com/HarysVizcaino/performance-skill.git "$HOME/.agents/skills/performance"
```

Instala solo la copia del agente que utilices, o ambas si usas los dos. Abre una sesión nueva y escribe `/performance` o `$performance`. El agente prepara la dependencia local la primera vez, sujeto a los permisos del entorno.

Para instalar por proyecto, actualizar o resolver problemas, consulta [Instalación](INSTALL.md).

## Qué puedes pedir

**Probar una web**

```text
/performance prueba https://mi-web.example con 20 usuarios durante 1 minuto. Consulta la portada y dos artículos existentes. Exige p95 inferior a 800 ms y menos del 1 % de errores.
```

**Probar una API local**

```text
$performance revisa este proyecto y prueba el catálogo en http://localhost:3000 con 10 usuarios durante 30 segundos. Comprueba que las respuestas incluyan productos.
```

**Comparar una optimización**

```text
/performance repite la prueba anterior después del cambio de caché y compara los resultados.
```

Usa un destino propio o para el que tengas autorización. El agente determina rutas a partir del proyecto o de una inspección ligera del sitio; prepara primero una prueba pequeña y aumenta la carga dentro de los límites que indiques. Una respuesta HTTP correcta debe corresponder también al contenido esperado.

## Qué recibes

- Un **informe Markdown** con solicitudes por segundo, p95/p99, errores y resultados por endpoint.
- Un resumen **JSON** para conservar evidencia y comparar ejecuciones.
- Un resultado explícito: **completada**, **incumple objetivos** o **incompleta**.
- Comparaciones antes/después con controles de destino y configuración.

Los usuarios simulados recorren las páginas con pausas. **100 usuarios no equivale a 100 solicitudes por segundo.** Si necesitas un ritmo fijo, pide recorridos por segundo.

## Alcance de la versión 0.1.0

Funciona con recorridos HTTP GET, comprobaciones de estado, texto HTML y campos JSON, una identidad bearer opcional, usuarios concurrentes y llegadas constantes. Incluye ejemplos para [web](examples/website.json) y [API](examples/api.json).

Mide respuestas HTTP: no ejecuta JavaScript de la página, no renderiza un navegador ni mide Core Web Vitals. Un sitio que devuelve el mismo HTML vacío para todas las rutas necesita validar sus APIs o adaptar la prueba. Login interactivo, escrituras y múltiples identidades requieren adaptar el script.

Los límites predeterminados del ejecutor son 100 usuarios y 5 minutos por ejecución; para llegadas constantes, hasta 100 recorridos/s con un máximo de 100 usuarios. El agente ajusta estos límites únicamente al alcance autorizado. Los errores y las respuestas incorrectas pueden detener una prueba. Un límite superior no garantiza que la carga sea adecuada para todos los servidores.

## Calidad y compatibilidad

La suite prueba configuraciones inválidas, integridad de descargas, cancelación, tiempo máximo, respuestas incorrectas, redirecciones, páginas HTML, autenticación sin exposición en informes, comparación y protección de resultados anteriores. Las integraciones se ejecutan únicamente contra un servidor local de prueba.

La automatización de GitHub valida macOS, Ubuntu y Windows. El instalador contempla macOS y Linux en ARM64/x64 y Windows x64. Consulta el resultado de [Actions](https://github.com/HarysVizcaino/performance-skill/actions) para conocer qué combinaciones pasaron; no todas las arquitecturas se prueban en cada ejecución. El formato de skill sigue las convenciones de ambos agentes; las pruebas automatizadas no sustituyen una sesión interactiva en cada uno.

## Contribuir

Reporta problemas con sistema operativo, versión de Performance y pasos para reproducirlos. Comparte informes revisados; evita tokens, datos personales y archivos de diagnóstico internos.

Para ejecutar la suite desde el repositorio:

```sh
python3 scripts/setup.py
python3 -m unittest discover -s tests -v
```

En Windows utiliza `py -3` en lugar de `python3`. No se incluyen binarios en el repositorio ni en los paquetes publicados.

## Licencia

[MIT](LICENSE) · Copyright (c) 2026 Harys Vizcaino.

La licencia cubre los archivos de este repositorio. Las dependencias descargadas por separado conservan sus propias licencias.
