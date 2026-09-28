# Private runtime reference

Implementation detail for the agent, not public product copy. The engine is the local k6 CLI. Required imports in the JavaScript assets retain the engine's real module names.

Locate `k6` on PATH or a known temporary official binary. Check its version internally. If absent, follow https://grafana.com/docs/k6/latest/set-up/install-k6/ and the environment's permissions. Do not claim the skill is self-contained or installed if its runtime is unavailable. Describe missing dependencies to the user as the local performance runtime unless they explicitly request technical details. Record the engine version in private validation notes rather than the user report.

Copy the three assets together into a test directory; customize the journey and config to the app. Run the wrapper with Python 3:

```sh
python3 scripts/run.py --script /absolute/path/to/journey.js --base-url http://127.0.0.1:3000 --output /absolute/path/to/results/run-001
```

Paths to the wrapper are relative to the skill folder. Optional `--config /absolute/path/to/workload.json` selects another config. Optional `--engine /absolute/path/to/binary` chooses a runtime outside PATH. BASE_URL must be an origin, without a path, query, fragment or embedded credentials. Authentication comes from `PERFORMANCE_BEARER_TOKEN` in the environment, not command arguments. The wrapper creates a new output directory, captures the raw engine banner internally and forwards the branded report. It records the actual exit code and does not convert failures into success.

If startup fails or no report is produced, inspect `.runtime.log` in the run directory internally. Never expose its raw contents without checking for secrets. Describe the actionable error without engine branding; do not hide the error. This is a private troubleshooting artifact, not a deliverable. The wrapper checks for an existing output directory to prevent stale reports or overwritten evidence.

Engine configuration: `BASE_URL`, `CONFIG`, `OUTPUT_DIR` are supplied to the runtime. CONFIG is absolute when supplied through the wrapper. The default JSON resolves relative to the journey script. No remote script imports are needed.

Official references on demand:

- https://grafana.com/docs/k6/latest/using-k6/scenarios/
- https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/
- https://grafana.com/docs/k6/latest/using-k6/thresholds/
- https://grafana.com/docs/k6/latest/results-output/end-of-test/custom-summary/

If summary structure changes, update the reporter against the installed version and verify it with a local fixture. Never substitute missing metrics with zero.
