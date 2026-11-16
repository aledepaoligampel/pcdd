import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'src' / 'pcdd_toolkit'
PYPROJECT = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
VERSION = re.search(r"__version__ = '([^']+)'", (PACKAGE / '__init__.py').read_text()).group(1)


def installed_files(project):
    return {str(p.relative_to(project)): p.read_bytes()
            for p in project.rglob('SKILL.md')} | {
        '.pcdd/core.md': (project / '.pcdd/core.md').read_bytes()}


class PackagingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.project = self.base / 'project'
        self.project.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def assert_distributes_sources(self, command, env=None):
        def run(*args):
            result = subprocess.run([*command, '--json', '--project', str(self.project), *args],
                                    capture_output=True, text=True, cwd=self.base, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)
        run('init', '--adapters', 'codex,claude,antigravity')
        self.assertEqual(run('doctor')['installed'], VERSION)
        run('new', 'sample')
        self.assertTrue((self.project / 'pcdd/changes/sample.md').exists())
        for path, data in installed_files(self.project).items():
            source = PACKAGE / 'assets' / ('core.md' if path.endswith('core.md')
                                           else 'skills/' + Path(path).parent.name + '/SKILL.md')
            self.assertEqual(data, source.read_bytes(), path)
        for language in ('es', 'en'):
            result = subprocess.run([*command, '--lang', language, '--help'],
                                    capture_output=True, text=True, cwd=self.base, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_version_has_single_source(self):
        self.assertIn('version = { attr = "pcdd_toolkit.__version__" }', PYPROJECT)
        self.assertIn('pcdd = "pcdd_toolkit.cli:main"', PYPROJECT)
        self.assertIn('license = "MIT"', PYPROJECT)
        self.assertIn('dependencies = []', PYPROJECT)
        self.assertTrue((ROOT / 'LICENSE').read_text().startswith('MIT License'))

    def test_package_data_covers_every_data_file(self):
        globs = re.findall(r'"([^"]+)"', re.search(r'pcdd_toolkit = \[(.*?)\]', PYPROJECT).group(1))
        for path in PACKAGE.rglob('*'):
            if path.is_file() and path.suffix not in ('.py', '.pyc'):
                relative = path.relative_to(PACKAGE)
                self.assertTrue(any(relative.match(pattern) and
                                    len(relative.parts) == len(Path(pattern).parts)
                                    for pattern in globs), relative)

    def test_package_runs_outside_checkout(self):
        site = self.base / 'site'
        shutil.copytree(PACKAGE, site / 'pcdd_toolkit', ignore=shutil.ignore_patterns('__pycache__'))
        env = dict(os.environ, PYTHONPATH=str(site))
        self.assert_distributes_sources([sys.executable, '-m', 'pcdd_toolkit'], env)

    @unittest.skipUnless(os.environ.get('PCDD_WHEEL_TEST') == '1',
                         'set PCDD_WHEEL_TEST=1 to build and install a wheel (needs network)')
    def test_wheel_installs_console_command(self):
        venv = self.base / 'venv'
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
        python = venv / 'bin' / 'python'
        subprocess.run([str(python), '-m', 'pip', 'install', '-q', '--upgrade', 'pip'], check=True)
        source = self.base / 'source'
        source.mkdir()
        for name in ('pyproject.toml', 'README.md', 'LICENSE'):
            shutil.copy2(ROOT / name, source / name)
        shutil.copytree(PACKAGE, source / 'src/pcdd_toolkit', ignore=shutil.ignore_patterns('__pycache__'))
        wheels = self.base / 'wheels'
        subprocess.run([str(python), '-m', 'pip', 'wheel', '-q', '--no-deps', '-w', str(wheels), str(source)],
                       check=True, cwd=self.base)
        wheel = next(wheels.glob(f'pcdd-{VERSION}-*.whl'))
        subprocess.run([str(python), '-m', 'pip', 'install', '-q', str(wheel)], check=True)
        command = venv / 'bin' / 'pcdd'
        version = subprocess.run([str(command), '--version'], capture_output=True, text=True, check=True)
        self.assertIn(VERSION, version.stdout)
        self.assert_distributes_sources([str(command)], dict(os.environ, PYTHONPATH=''))


if __name__ == '__main__':
    unittest.main()
