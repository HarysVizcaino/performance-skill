# Performance

Skill para Claude Code y Codex que prepara pruebas de rendimiento, ejecuta recorridos HTTP y genera informes Markdown y JSON.

## Uso

En Claude Code:

```text
/performance prueba http://localhost:3000 con 50 usuarios durante 2 minutos. Consulta productos y abre sus detalles. Exige p95 menor de 500 ms.
```

En Codex:

```text
$performance prueba mi API local con 10 usuarios durante 30 segundos y genera un informe.
```

Escribe los detalles después del comando: destino, acciones, usuarios, duración y objetivos. El agente revisa el proyecto y pregunta únicamente por datos imprescindibles que falten.

## Instalación

Clona el repositorio con el nombre de carpeta `performance` en la ubicación de skills del agente.

Claude Code, instalación personal:

```sh
git clone https://github.com/HarysVizcaino/performance-skill.git ~/.claude/skills/performance
```

Codex, instalación personal:

```sh
git clone https://github.com/HarysVizcaino/performance-skill.git ~/.agents/skills/performance
```

Para instalar por proyecto, usa `.claude/skills/performance` o `.agents/skills/performance`. Conserva todos los archivos juntos. Consulta [INSTALL.md](INSTALL.md) para más detalles. El agente prepara el motor local según los permisos del entorno; el ejecutor utiliza Python 3.

## Primera versión

- Recorridos GET secuenciales con pausas y comprobaciones de estado/contenido.
- Carga por usuarios simultáneos o recorridos por segundo.
- Umbrales de latencia y errores, globales y por endpoint.
- Informes Markdown/JSON y registro del código de salida.
- Instrucciones para comparar pruebas antes y después de cambios.

La plantilla se adapta a los endpoints reales. Login, escrituras y múltiples identidades requieren ajustes del agente. Las pruebas se ejecutan dentro del alcance autorizado. Las métricas del cliente no identifican por sí solas un cuello de botella del servidor.

Validación local: cinco escenarios comprobaron ejecuciones correctas, errores HTTP, contenido incorrecto y redirecciones. Son pruebas de la plantilla, no mediciones de capacidad de una aplicación real. La integración con ambos agentes sigue el formato compartido de skills; no se ha verificado el descubrimiento automático en una sesión de Claude Code.
