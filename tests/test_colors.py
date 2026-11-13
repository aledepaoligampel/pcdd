import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest

CLI = Path(__file__).resolve().parents[1] / 'pcdd.py'


@unittest.skipUnless(os.name == 'posix', 'PTY requires POSIX')
class ColorTests(unittest.TestCase):
    def terminal(self, *args, override=None):
        import pty
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, TERM='xterm-256color', LANG='es_AR.UTF-8',
                       XDG_CONFIG_HOME=directory + '/settings')
            env.pop('NO_COLOR', None)
            env.update(override or {})
            master, slave = pty.openpty()
            process = subprocess.Popen([sys.executable, str(CLI), '--project', directory,
                                        '--lang', 'es', *args], env=env,
                                       stdin=slave, stdout=slave, stderr=slave)
            output = b''
            try:
                deadline = time.monotonic() + 5
                while True:
                    ready, _, _ = select.select([master], [], [], 0.05)
                    if ready:
                        output += os.read(master, 4096)
                    elif process.poll() is not None:
                        break
                    if time.monotonic() > deadline:
                        self.fail('CLI did not finish')
            finally:
                os.close(slave)
                os.close(master)
                if process.poll() is None:
                    process.kill()
                    process.wait()
            return process.returncode, output.decode()

    def test_interactive_preview_has_colored_logo_and_resets(self):
        code, output = self.terminal('init', '--dry-run')
        self.assertEqual(code, 0)
        self.assertIn('\x1b[1;36m›_ pcdd\x1b[0m', output)
        self.assertIn('\x1b[33mVista previa', output)
        self.assertIn('\x1b[0m', output)

    def test_success_and_errors_keep_meaning_without_color(self):
        code, output = self.terminal('init')
        self.assertEqual(code, 0)
        self.assertIn('\x1b[32mPCDD está listo.\x1b[0m', output)
        code, output = self.terminal('doctor')
        self.assertEqual(code, 1)
        self.assertIn('\x1b[31mPCDD:', output)
        self.assertIn('pcdd init', output)

    def test_machine_and_opt_out_remain_plain_even_in_terminal(self):
        for override in ({'NO_COLOR': ''}, {'TERM': 'dumb'}):
            code, output = self.terminal('init', '--dry-run', override=override)
            self.assertEqual(code, 0)
            self.assertNotIn('\x1b', output)
            self.assertIn('Vista previa', output)
        code, output = self.terminal('init', '--dry-run', '--json')
        self.assertEqual(code, 0)
        self.assertNotIn('\x1b', output)
        self.assertTrue(json.loads(output)['dry_run'])
