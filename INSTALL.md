# Instalación y uso

La carpeta completa `performance` es la skill. Conserva la carpeta completa con sus recursos internos. El agente administra el motor local de pruebas siguiendo su referencia interna. No necesitas una cuenta de servicios externos.

Instalación por proyecto:

- Codex: copia la carpeta en `.agents/skills/performance/`.
- Claude Code: copia la carpeta en `.claude/skills/performance/`.

Instalación personal:

- Codex: `~/.agents/skills/performance/`.
- Claude Code: `~/.claude/skills/performance/`.

Usa la misma fuente para ambas copias. No dependas de metadatos exclusivos de un agente. Las políticas de permisos de cada entorno siguen aplicándose. Reinicia la sesión si no aparece tras copiarla.

Ejemplo de petición:

> /performance prueba mi API local con 10 usuarios durante 30 segundos. Consulta productos y abre sus detalles. Exige p95 inferior a 500 ms y genera un informe.

> $performance prueba http://localhost:3000 con 50 usuarios durante 2 minutos; menos del 1 % de errores.

Todo lo que escribas después del comando describe la prueba. Puedes indicar URL, endpoints, acciones, usuarios, duración y objetivos en lenguaje natural. El agente revisa el proyecto para completar el contexto y solo pregunta por datos imprescindibles que falten.

En Codex también puedes invocar `$performance`; en Claude Code, `/performance`.

La plantilla incluye `/health` con JSON `{"status":"ok"}` como ejemplo. Adapta `workload.json` antes de usarla. Para otro tipo de respuesta, elimina `jsonField`/`equals` y añade comprobaciones de negocio adecuadas al script.

Para llegadas constantes, usa `mode: "arrival"`, `rate: 2`, `preAllocatedVUs: 2`, `maxVUs: 5` y `pauseSeconds: 0` en cada ruta. `rate` representa recorridos por segundo, no solicitudes por segundo.

Guarda la autenticación en la variable de entorno `PERFORMANCE_BEARER_TOKEN`; nunca la pongas en el comando de ejemplo ni en el JSON. La plantilla básica comparte esa identidad. Recorridos multiusuario y operaciones de escritura requieren adaptar el script.

Los informes se crean en `OUTPUT_DIR`, que debe existir. Usa una carpeta nueva por ejecución para no sobrescribir evidencia. El resultado de umbrales debe acompañarse del código de salida de la ejecución y la confirmación de ejecución completa.

Fuentes de compatibilidad: https://developers.openai.com/codex/skills/ y https://code.claude.com/docs/en/skills.
