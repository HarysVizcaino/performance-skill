import contextlib
import copy
import hashlib
import http.server
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import config
import run
import setup
import compare

BASE = json.loads((ROOT / 'assets/workload.json').read_text())
ENGINE = Path(os.environ.get('PERFORMANCE_TEST_ENGINE', str(setup.runtime_path())))


class ConfigTests(unittest.TestCase):
    def test_defaults_and_zero_errors(self):
        self.assertEqual(config.validate(BASE, 'http://localhost:3000'), 10)
        value = copy.deepcopy(BASE)
        value['errorRate'] = 0
        config.validate(value, 'https://example.com')

    def test_refuses_invalid_workload_before_traffic(self):
        for field, value in [('vus', 101), ('vus', True), ('duration', '0s'), ('duration', '6m'),
                             ('errorRate', -1), ('errorRate', float('nan')), ('routes', []), ('mode', 'invalid')]:
            workload = copy.deepcopy(BASE)
            workload[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                config.validate(workload, 'http://localhost')

    def test_refuses_credentialed_and_non_origin_urls(self):
        for origin in ['https://name:password@example.com', 'https://example.com/?token=secret',
                       'file:///tmp/file', 'https://example.com/path', 'https://example.com:bad', '//example.com']:
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                config.validate(BASE, origin)

    def test_arrival_and_route_guards(self):
        value = copy.deepcopy(BASE)
        value.update(mode='arrival', rate=5, preAllocatedVUs=2, maxVUs=3)
        with self.assertRaises(ValueError):
            config.validate(value, 'http://localhost')
        value['routes'][0]['pauseSeconds'] = 0
        config.validate(value, 'http://localhost')
        value['routes'][0]['path'] = '//another.example/path'
        with self.assertRaises(ValueError):
            config.validate(value, 'http://localhost')

    def test_checksum_rejects_tampered_download(self):
        digest = hashlib.sha256(b'official bytes').hexdigest()
        setup.verify(b'official bytes', digest)
        with self.assertRaises(ValueError):
            setup.verify(b'changed bytes', digest)


class ExecutionTests(unittest.TestCase):
    def test_missing_summary_never_passes(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            result = run.finalize(Path(folder), 0, 10, 10, BASE, 'http://localhost', None)
            self.assertEqual(result, 2)
            self.assertEqual(json.loads((Path(folder) / 'execution.json').read_text())['status'], 'INCOMPLETA')

    def test_short_summary_never_passes(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            path = Path(folder)
            (path/'summary.json').write_text(json.dumps({'metrics': {'iterations': {'values': {'count': 10}}},
                                                        'actualDurationMs': 100, 'status': 'UMBRALES CUMPLIDOS'}))
            self.assertEqual(run.finalize(path, 0, .1, 10, BASE, 'http://localhost', None), 2)

    def test_timeout_and_cancel_stop_child_and_record_status(self):
        for error, expected in [(subprocess.TimeoutExpired('engine', 25), 124), (KeyboardInterrupt(), 130)]:
            with self.subTest(code=expected), tempfile.TemporaryDirectory() as folder:
                path = Path(folder)
                engine = path/'engine'
                engine.touch()
                workload = path/'input.json'
                workload.write_text(json.dumps(BASE))
                process = Mock()
                process.wait.side_effect = error
                args = ['run.py', '--base-url', 'http://localhost', '--output', str(path/'result'),
                        '--engine', str(engine), '--config', str(workload)]
                with patch.object(sys, 'argv', args), patch.object(run.subprocess, 'Popen', return_value=process), patch.object(run, 'stop') as stop, contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(run.main(), expected)
                    stop.assert_called_once_with(process)
                data = json.loads((path/'result/execution.json').read_text())
                self.assertEqual(data['status'], 'INCOMPLETA')

    def test_stop_terminates_actual_process(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=os.name != 'nt')
        run.stop(child)
        self.assertIsNotNone(child.poll())


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/slow':
            time.sleep(.3)
        status = 503 if self.path == '/error' else 302 if self.path == '/redirect' else 200
        body = ('<html>Performance demo</html>' if self.path == '/' else json.dumps({'status': 'wrong' if self.path == '/wrong' else 'ok'})).encode()
        self.send_response(status)
        self.send_header('Content-Length', str(len(body)))
        if status == 302:
            self.send_header('Location', '/health')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


@unittest.skipUnless(ENGINE.is_file(), 'Prepare the local runtime for integration tests.')
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def perform(self, directory, name, path='/health', mode='vus', duration='1s', contains=None):
        workload = copy.deepcopy(BASE)
        workload.update(duration=duration, mode=mode)
        workload['routes'][0].update(path=path, pauseSeconds=.05 if mode == 'vus' else 0)
        if contains:
            workload['routes'][0].pop('jsonField')
            workload['routes'][0].pop('equals')
            workload['routes'][0]['contains'] = contains
        if mode == 'arrival':
            workload.update(rate=5, preAllocatedVUs=2, maxVUs=3)
        config_path = directory/f'{name}.json'
        config_path.write_text(json.dumps(workload))
        target = directory/name
        command = [sys.executable, str(ROOT/'scripts/run.py'), '--base-url', self.origin,
                   '--output', str(target), '--config', str(config_path), '--engine', str(ENGINE)]
        # These environment overrides must not change the workload or leak auth.
        env = {**os.environ, 'K6_VUS': '9999', 'K6_HTTP_DEBUG': 'full', 'PERFORMANCE_BEARER_TOKEN': 'private-test-token'}
        result = subprocess.run(command, capture_output=True, text=True, timeout=35, encoding='utf-8', env=env)
        self.assertNotIn('k6', (result.stdout + result.stderr).lower())
        for filename in ['report.md', 'summary.json', 'execution.json', '.runtime.log']:
            self.assertNotIn('private-test-token', (target/filename).read_text(encoding='utf-8'))
        return result, target

    def test_http_content_redirects_and_html(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, path, expected, contains in [('pass', '/health', 0, None), ('content', '/wrong', 99, None),
                                                  ('http', '/error', 99, None), ('redirect', '/redirect', 99, None),
                                                  ('html', '/', 0, 'Performance demo')]:
                with self.subTest(name=name):
                    result, target = self.perform(Path(folder), name, path, contains=contains)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                    status = json.loads((target/'execution.json').read_text())['status']
                    self.assertEqual(status, 'COMPLETADA' if expected == 0 else 'INCUMPLE OBJETIVOS')

    def test_arrivals(self):
        with tempfile.TemporaryDirectory() as folder:
            result, _ = self.perform(Path(folder), 'arrival', mode='arrival')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_abort_is_incomplete(self):
        with tempfile.TemporaryDirectory() as folder:
            result, target = self.perform(Path(folder), 'abort', '/error', duration='30s')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads((target/'execution.json').read_text())['status'], 'INCOMPLETA')

    def test_comparison_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            _, a = self.perform(directory, 'before')
            _, b = self.perform(directory, 'after')
            self.assertIn('p95', compare.compare(a, b))
            data = json.loads((b/'execution.json').read_text())
            data['workloadFingerprint'] = 'different'
            (b/'execution.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                compare.compare(a, b)
            original = (a/'execution.json').read_bytes()
            result = subprocess.run([sys.executable, str(ROOT/'scripts/run.py'), '--base-url', self.origin,
                                     '--output', str(a), '--engine', str(ENGINE)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(original, (a/'execution.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
