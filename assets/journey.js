import http from 'k6/http';
import { check, sleep } from 'k6';
import { buildReport } from './report.js';

const config = JSON.parse(open(__ENV.CONFIG || './workload.json'));
const origin = (__ENV.BASE_URL || '').replace(/\/$/, '');
if (!/^https?:\/\/(?:\[[a-fA-F0-9:]+\]|[a-zA-Z0-9.-]+)(?::\d+)?$/.test(origin)) {
  throw new Error('BASE_URL must be an HTTP(S) origin without credentials, path or query.');
}
function positive(value, label, integer = false) {
  if (!Number.isFinite(value) || value <= 0 || (integer && !Number.isInteger(value))) {
    throw new Error(`${label} must be a positive ${integer ? 'integer' : 'number'}.`);
  }
}
if (!['vus', 'arrival'].includes(config.mode)) throw new Error('mode must be vus or arrival.');
if (!/^\d+(?:\.\d+)?(ms|s|m|h)$/.test(config.duration) || parseFloat(config.duration) <= 0) {
  throw new Error('duration must be positive, for example 10s or 2m.');
}
positive(config.p95Ms, 'p95Ms');
positive(config.p99Ms, 'p99Ms');
if (!Number.isFinite(config.errorRate) || config.errorRate < 0) throw new Error('errorRate must be nonnegative.');
if (config.errorRate > 1) throw new Error('errorRate must not exceed 1.');
if (!Array.isArray(config.routes) || config.routes.length === 0) throw new Error('routes required.');
const names = new Set();
for (const route of config.routes) {
  if (typeof route.name !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(route.name) || names.has(route.name)) throw new Error('Unique simple route names required.');
  names.add(route.name);
  if (typeof route.path !== 'string' || !route.path.startsWith('/') || route.path.startsWith('//') || /[\r\n#]/.test(route.path)) {
    throw new Error('Route path must be relative to the target origin.');
  }
  if (!Number.isInteger(route.expectedStatus) || route.expectedStatus < 200 || route.expectedStatus > 599) throw new Error('Explicit expectedStatus required.');
  if (!Number.isFinite(route.pauseSeconds) || route.pauseSeconds < 0) throw new Error('pauseSeconds must be nonnegative.');
  if (route.jsonField !== undefined && (typeof route.jsonField !== 'string' || !Object.prototype.hasOwnProperty.call(route, 'equals'))) throw new Error('jsonField requires an equals value.');
  if (config.mode === 'arrival' && route.pauseSeconds !== 0) throw new Error('Use zero pauses in arrival mode.');
}
const errorCriterion = config.errorRate === 0 ? 'rate==0' : `rate<${config.errorRate}`;
const thresholds = {
  http_reqs: ['count>0'],
  iterations: ['count>0'],
  checks: [{ threshold: 'rate==1', abortOnFail: true, delayAbortEval: '10s' }],
  http_req_duration: [`p(95)<${config.p95Ms}`, `p(99)<${config.p99Ms}`],
  http_req_failed: [{ threshold: errorCriterion, abortOnFail: true, delayAbortEval: '10s' }],
};
for (const route of config.routes) {
  thresholds[`http_req_duration{name:${route.name}}`] = [`p(95)<${config.p95Ms}`, `p(99)<${config.p99Ms}`];
  thresholds[`http_req_failed{name:${route.name}}`] = [errorCriterion];
}
let scenario;
if (config.mode === 'vus') {
  positive(config.vus, 'vus', true);
  scenario = { executor: 'constant-vus', vus: config.vus, duration: config.duration };
} else {
  for (const key of ['rate', 'preAllocatedVUs', 'maxVUs']) positive(config[key], key, true);
  if (config.maxVUs < config.preAllocatedVUs) throw new Error('maxVUs must be >= preAllocatedVUs.');
  scenario = { executor: 'constant-arrival-rate', rate: config.rate, timeUnit: '1s', duration: config.duration, preAllocatedVUs: config.preAllocatedVUs, maxVUs: config.maxVUs };
  thresholds.dropped_iterations = ['count==0'];
}
export const options = {
  scenarios: { journey: { ...scenario, gracefulStop: '5s' } },
  thresholds,
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
  systemTags: ['name', 'method', 'status', 'scenario', 'expected_response'],
};

export default function () {
  for (const route of config.routes) {
    const headers = __ENV.PERFORMANCE_BEARER_TOKEN ? { Authorization: `Bearer ${__ENV.PERFORMANCE_BEARER_TOKEN}` } : {};
    const response = http.get(`${origin}${route.path}`, {
      headers, tags: { name: route.name }, redirects: 0, timeout: '5s',
      responseCallback: http.expectedStatuses(route.expectedStatus),
    });
    check(response, { [`${route.name}: status`]: (r) => r.status === route.expectedStatus });
    if (route.jsonField !== undefined) {
      let value;
      try { value = route.jsonField.split('.').reduce((item, key) => item == null ? undefined : item[key], response.json()); } catch (_) { /* Check records failure. */ }
      check(value, { [`${route.name}: content`]: (actual) => JSON.stringify(actual) === JSON.stringify(route.equals) });
    }
    if (route.contains !== undefined) {
      check(response, { [`${route.name}: content`]: (r) => typeof r.body === 'string' && r.body.includes(route.contains) });
    }
    if (route.pauseSeconds) sleep(route.pauseSeconds);
  }
}

export function handleSummary(data) {
  const output = __ENV.OUTPUT_DIR || '.';
  const result = buildReport(data, {
    mode: config.mode, duration: config.duration,
    vus: config.mode === 'vus' ? config.vus : null,
    journeysPerSecond: config.mode === 'arrival' ? config.rate : null,
    routes: config.routes.map((route) => route.name),
  });
  return {
    stdout: result.markdown,
    [`${output}/report.md`]: result.markdown,
    [`${output}/summary.json`]: JSON.stringify(result.summary, null, 2),
  };
}
