import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'pcdd.py'


class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        self.env = dict(os.environ, XDG_CONFIG_HOME=str(self.root / 'config'),
                        LANG='es_AR.UTF-8', LC_ALL='', LC_MESSAGES='', LANGUAGE='',
                        TERM='dumb', NO_COLOR='1')

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, ok=True, env=None):
        result = subprocess.run([sys.executable, str(CLI), '--project', str(self.project), *args],
                                env=env or self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def test_human_preview_is_spanish_and_readonly(self):
        result = self.run_cli('init', '--dry-run')
        self.assertIn('cada cambio, el proceso justo.', result.stdout)
        self.assertIn('Vista previa', result.stdout)
        self.assertIn('AGENTS.md', result.stdout)
        self.assertNotIn('\x1b', result.stdout + result.stderr)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_explicit_language_overrides_environment_on_either_side_of_command(self):
        for args in [('init', '--dry-run', '--lang', 'en'),
                     ('--lang', 'en', 'init', '--dry-run')]:
            result = self.run_cli(*args)
            self.assertIn('each change, just enough.', result.stdout)
            self.assertIn('Preview', result.stdout)

    def test_saved_preference_and_auto_reset_preserve_other_settings(self):
        config = self.root / 'config/pcdd/preferences.json'
        config.parent.mkdir(parents=True)
        config.write_text('{"custom":42}')
        self.run_cli('language', 'en')
        self.assertEqual(json.loads(config.read_text())['custom'], 42)
        self.assertIn('Preview', self.run_cli('init', '--dry-run').stdout)
        self.assertIn('Vista previa', self.run_cli('init', '--dry-run', '--lang', 'es').stdout)
        self.run_cli('language', 'auto')
        self.assertIn('Vista previa', self.run_cli('init', '--dry-run').stdout)
        self.assertFalse((self.project / '.pcdd').exists())

    def test_json_is_one_document_independent_of_language(self):
        reports = []
        for lang in ('es', 'en'):
            result = self.run_cli('init', '--dry-run', '--json', '--lang', lang)
            reports.append(json.loads(result.stdout))
            self.assertEqual(result.stderr, '')
            self.assertNotIn('pcdd\n', result.stdout)
        self.assertEqual(reports[0], reports[1])
        self.assertIn('files', reports[0])
        self.assertTrue(reports[0]['dry_run'])

    def test_errors_are_localized_and_json_errors_are_parseable(self):
        result = self.run_cli('doctor', '--lang', 'es', ok=False)
        self.assertIn('pcdd init', result.stderr)
        self.assertIn('instalación', result.stderr)
        result = self.run_cli('doctor', '--json', ok=False)
        self.assertEqual(result.stderr, '')
        self.assertEqual(json.loads(result.stdout)['error']['code'], 'conflict')
        result = self.run_cli('unknown', '--lang', 'es', '--json', ok=False)
        self.assertEqual(json.loads(result.stdout)['error']['code'], 'arguments')

    def test_help_is_localized_at_root_and_command(self):
        for args in [('--lang', 'es', '--help'), ('init', '--lang', 'es', '--help')]:
            result = self.run_cli(*args)
            self.assertIn('Opciones', result.stdout)
            self.assertIn('idioma', result.stdout)
            self.assertTrue(result.stdout.startswith('Uso: pcdd '), result.stdout)
        self.assertIn('Options', self.run_cli('--lang', 'en', '--help').stdout)

    def test_environment_precedence_and_unsupported_language_fallback(self):
        env = dict(self.env, LC_ALL='en_US.UTF-8', LANG='es_AR.UTF-8')
        self.assertIn('Preview', self.run_cli('init', '--dry-run', env=env).stdout)
        env = dict(self.env, LC_ALL='fr_FR.UTF-8', LANG='en_US.UTF-8')
        self.assertIn('Vista previa', self.run_cli('init', '--dry-run', env=env).stdout)

    def test_init_summary_and_idempotent_run(self):
        (self.project / 'AGENTS.md').write_text('Personal instructions\n')
        result = self.run_cli('init', '--lang', 'es')
        self.assertIn('listo', result.stdout)
        self.assertIn('Crear', result.stdout)
        self.assertIn('Actualizar', result.stdout)
        self.assertTrue((self.project / 'AGENTS.md').read_text().startswith('Personal instructions\n'))
        result = self.run_cli('init', '--lang', 'es')
        self.assertIn('Sin cambios', result.stdout)
        self.assertIn('Conservar', result.stdout)

    def test_unsupported_explicit_language_fails_before_writes(self):
        self.run_cli('init', '--lang', 'fr', ok=False)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_ascii_output_can_render_without_encoding_failure(self):
        result = self.run_cli('init', '--dry-run', '--lang', 'en',
                              env=dict(self.env, PYTHONIOENCODING='ascii'))
        self.assertIn('>_ pcdd', result.stdout)

    @unittest.skipUnless(os.name == 'posix', 'PTY requires POSIX')
    def test_animation_only_on_interactive_terminal_and_finishes_before_result(self):
        import pty
        import select
        import time
        for suppress in (False, True):
            master, slave = pty.openpty()
            env = dict(self.env, TERM='xterm-256color')
            if not suppress:
                env.pop('NO_COLOR', None)
            process = subprocess.Popen([sys.executable, str(CLI), '--project', str(self.project),
                                        'init', '--dry-run', '--lang', 'en'],
                                       env=env, stdin=slave, stdout=slave, stderr=slave)
            try:
                output = b''
                deadline = time.monotonic() + 5
                while True:
                    ready, _, _ = select.select([master], [], [], 0.05)
                    if ready:
                        output += os.read(master, 4096)
                    elif process.poll() is not None:
                        break
                    if time.monotonic() > deadline:
                        self.fail('Interactive CLI did not exit')
            finally:
                os.close(slave)
                os.close(master)
                if process.poll() is None:
                    process.kill()
                    process.wait()
            self.assertEqual(process.returncode, 0)
            if suppress:
                self.assertNotIn(b'\r  | ', output)
            else:
                self.assertIn(b'\r  | ', output)
                self.assertLess(output.index(b'\r  | '), output.index(b'Preview'))

    def test_json_help_and_version_stay_machine_readable(self):
        help_data = json.loads(self.run_cli('--json', '--help').stdout)
        self.assertIn('help', help_data)
        version = json.loads(self.run_cli('--json', '--version').stdout)
        self.assertIn('version', version)

    def test_language_preference_rejects_symlink_and_keeps_target(self):
        config = self.root / 'config/pcdd/preferences.json'
        config.parent.mkdir(parents=True)
        outside = self.root / 'own.json'
        outside.write_text('{"language":"es"}')
        config.symlink_to(outside)
        self.run_cli('language', 'en', '--lang', 'es', ok=False)
        self.assertEqual(outside.read_text(), '{"language":"es"}')

    def test_ascii_system_locale_still_supports_json_and_utf8_preferences(self):
        config = self.root / 'config/pcdd/preferences.json'
        config.parent.mkdir(parents=True)
        config.write_text('{"language":"en","note":"español"}', encoding='utf-8')
        env = dict(self.env, LC_ALL='C', PYTHONUTF8='0', PYTHONCOERCECLOCALE='0')
        result = self.run_cli('--json', '--version', env=env)
        self.assertIn('version', json.loads(result.stdout))
        self.assertEqual(result.stderr, '')
        result = self.run_cli('init', '--dry-run', env=env)
        self.assertIn('Preview', result.stdout)

    def test_abbreviations_are_rejected_instead_of_silently_misinterpreted(self):
        for options in [('--j',), ('--la', 'en')]:
            self.run_cli('init', '--dry-run', *options, ok=False)
        self.assertEqual(list(self.project.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
