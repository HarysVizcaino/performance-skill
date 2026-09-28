// Pure JavaScript: usable by the runtime without remote imports or Node dependencies.
export function buildReport(data, workload) {
  if (!data.metrics || !data.metrics.http_reqs || !data.metrics.http_reqs.values) {
    throw new Error('Unsupported or empty performance summary: inspect this version before reporting results.');
  }
  const metrics = {};
  const thresholdRows = [];
  for (const [name, metric] of Object.entries(data.metrics)) {
    if (!/^(http_reqs|http_req_duration|http_req_failed|checks|iterations|iteration_duration|vus|vus_max|dropped_iterations)(\{|$)/.test(name)) continue;
    metrics[name] = { values: metric.values, thresholds: metric.thresholds || {} };
    for (const [expression, result] of Object.entries(metric.thresholds || {})) {
      thresholdRows.push({ metric: name, expression, ok: result.ok });
    }
  }
  const value = (name, field) => metrics[name]?.values?.[field];
  const format = (n) => Number.isFinite(n) ? n.toFixed(2) : 'N/D';
  const sufficient = value('http_reqs', 'count') > 0 && value('iterations', 'count') > 0;
  const status = !sufficient || thresholdRows.length === 0 || thresholdRows.some((r) => typeof r.ok !== 'boolean')
    ? 'INCONCLUSO' : thresholdRows.every((r) => r.ok) ? 'UMBRALES CUMPLIDOS' : 'UMBRALES INCUMPLIDOS';
  const summary = { schema: 'performance/v1', generatedAt: new Date().toISOString(), workload,
    actualDurationMs: data.state?.testRunDurationMs ?? null, status, metrics };
  const lines = [
    '# Informe de rendimiento', '', `Resultado de umbrales: **${status}**.`, '',
    'Los umbrales evalúan las muestras recibidas. El apartado Ejecución confirma si la prueba finalizó o quedó incompleta.', '',
    `Modelo: ${workload.mode}. Duración prevista: ${workload.duration}. Duración observada: ${format(summary.actualDurationMs)} ms.`,
    workload.mode === 'vus' ? `Usuarios configurados: ${workload.vus}.` : `Recorridos previstos por segundo: ${workload.journeysPerSecond}.`, '',
    '| Medición | Valor |', '|---|---:|',
    `| Solicitudes | ${format(value('http_reqs', 'count'))} |`,
    `| Solicitudes/s observadas | ${format(value('http_reqs', 'rate'))} |`,
    `| Recorridos completados | ${format(value('iterations', 'count'))} |`,
    `| p95 HTTP (ms) | ${format(value('http_req_duration', 'p(95)'))} |`,
    `| p99 HTTP (ms) | ${format(value('http_req_duration', 'p(99)'))} |`,
    `| Errores HTTP (%) | ${format(value('http_req_failed', 'rate') * 100)} |`,
    `| Checks correctos (%) | ${format(value('checks', 'rate') * 100)} |`,
    `| Iteraciones descartadas | ${workload.mode === 'vus' ? 'No aplica' : format(value('dropped_iterations', 'count'))} |`, '',
    '## Por endpoint', '', '| Endpoint | p95 (ms) | p99 (ms) | Errores (%) |', '|---|---:|---:|---:|',
    ...workload.routes.map((name) => `| ${name} | ${format(value(`http_req_duration{name:${name}}`, 'p(95)'))} | ${format(value(`http_req_duration{name:${name}}`, 'p(99)'))} | ${format(value(`http_req_failed{name:${name}}`, 'rate') * 100)} |`), '',
    '## Umbrales', '', '| Métrica | Criterio | Cumple |', '|---|---|---|',
    ...thresholdRows.map((r) => `| ${r.metric} | ${r.expression} | ${r.ok === true ? 'Sí' : r.ok === false ? 'No' : 'N/D'} |`), '',
    '## Alcance', '',
    'Estos datos describen exclusivamente la carga ensayada. No prueban capacidad máxima ni identifican por sí solos un cuello de botella de CPU, memoria o base de datos. Percentiles de pruebas cortas tienen pocas muestras.', '',
  ];
  return { summary, markdown: lines.join('\n') };
}
