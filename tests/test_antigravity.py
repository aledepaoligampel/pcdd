import base64
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'pcdd.py'
SKILLS = ('pcdd-work', 'pcdd-review', 'pcdd-commit', 'pcdd-commit-review')


class AntigravityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()
        self.env = dict(os.environ, XDG_CONFIG_HOME=str(Path(self.temp.name) / 'config'))

    def run_cli(self, *args, ok=True, cli=CLI):
        result = subprocess.run([sys.executable, str(cli), '--json', '--project',
                                 str(self.root), *args], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        self.assertEqual(result.stderr, '')
        return json.loads(result.stdout)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()
                and p.name != 'last-update.json'}

    def changed_distribution(self):
        target = Path(self.temp.name) / 'kit'
        target.mkdir()
        for name in ('pcdd.py', 'presentation.py'):
            shutil.copy2(CLI.parent / name, target / name)
        for name in ('assets', 'locales'):
            shutil.copytree(CLI.parent / name, target / name)
        with (target / 'assets/core.md').open('ab') as stream:
            stream.write(b'\nUpdated instructions for testing.\n')
        return target / 'pcdd.py'

    def test_selected_adapters_share_files_and_remain_idempotent(self):
        adapters = ('codex', 'claude', 'antigravity')
        for count in range(1, 4):
            for selected in itertools.combinations(adapters, count):
                with self.subTest(selected=selected):
                    self.root = Path(self.temp.name) / '-'.join(selected)
                    self.root.mkdir()
                    args = ('init', '--adapters', ','.join(selected))
                    self.run_cli(*args, '--dry-run')
                    self.assertEqual(list(self.root.iterdir()), [])
                    self.run_cli(*args)
                    report = self.run_cli('doctor')
                    self.assertEqual(report['adapters'], list(selected))
                    self.assertEqual(report['installed'], '0.4.0')
                    for folder, enabled in (
                            ('.agents', 'codex' in selected or 'antigravity' in selected),
                            ('.claude', 'claude' in selected)):
                        for skill in SKILLS:
                            path = self.root / folder / 'skills' / skill / 'SKILL.md'
                            self.assertEqual(path.exists(), enabled)
                            if enabled:
                                self.assertEqual(path.read_bytes(),
                                                 (CLI.parent / 'assets/skills' / skill / 'SKILL.md').read_bytes())
                    self.assertEqual((self.root / 'CLAUDE.md').exists(), 'claude' in selected)
                    manifest = json.loads((self.root / '.pcdd/installation.json').read_text())
                    paths = set(self.snapshot()) - {'.pcdd/config.json', '.pcdd/installation.json'}
                    self.assertEqual(set(manifest['files']), paths)
                    self.assertEqual((self.root / 'AGENTS.md').read_text().count('<!-- pcdd:begin -->'), 1)
                    before = self.snapshot()
                    self.assertEqual(self.run_cli(*args)['files'], [])
                    self.assertEqual(self.run_cli('update')['files'], [])
                    self.assertEqual(before, self.snapshot())

    def test_update_and_rollback_preserve_shared_files_and_project_content(self):
        (self.root / 'AGENTS.md').write_bytes(b'Own instructions\r\n')
        self.run_cli('init', '--adapters', 'codex,antigravity')
        config = self.root / '.pcdd/config.json'
        config.write_text('{"schema":1,"gate":["make ready"],"custom":42}')
        self.run_cli('new', 'example')
        before = self.snapshot()
        candidate = self.changed_distribution()
        self.run_cli('update', '--dry-run', cli=candidate)
        self.assertEqual(before, self.snapshot())
        self.run_cli('update', cli=candidate)
        self.run_cli('doctor', cli=candidate)
        self.assertEqual(config.read_bytes(), before['.pcdd/config.json'])
        self.assertEqual((self.root / 'AGENTS.md').read_bytes(), before['AGENTS.md'])
        self.run_cli('rollback', cli=candidate)
        self.assertEqual(before, self.snapshot())
        self.run_cli('doctor')

    def test_partial_update_recovers_antigravity_inventory(self):
        self.run_cli('init', '--adapters', 'antigravity')
        before = self.snapshot()
        candidate = self.changed_distribution()
        self.run_cli('update', cli=candidate)
        journal = json.loads((self.root / '.pcdd/last-update.json').read_text())
        name = '.pcdd/core.md'
        (self.root / name).write_bytes(base64.b64decode(journal[name]['before']))
        (self.root / '.pcdd/pending.json').write_text(json.dumps(journal))
        self.run_cli('doctor', ok=False)
        self.run_cli('recover', cli=candidate)
        self.assertEqual(before, self.snapshot())
        self.run_cli('doctor')

    def test_conflicts_and_symlinks_are_rejected_before_writes(self):
        path = self.root / '.agents/skills/pcdd-work/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_bytes((CLI.parent / 'assets/skills/pcdd-work/SKILL.md').read_bytes())
        before = self.snapshot()
        for args in (('init', '--dry-run'), ('init',)):
            report = self.run_cli(*args, '--adapters', 'antigravity', ok=False)
            self.assertIn('Unowned file', report['error']['message'])
            self.assertEqual(before, self.snapshot())
        path.unlink()
        outside = Path(self.temp.name) / 'outside'
        outside.write_text('Customer content')
        path.symlink_to(outside)
        self.run_cli('init', '--adapters', 'antigravity', ok=False)
        self.assertTrue(path.is_symlink())
        self.assertEqual(outside.read_text(), 'Customer content')
        self.assertFalse((self.root / 'AGENTS.md').exists())

    def test_legacy_03_upgrade_preserves_selection_and_rolls_back(self):
        self.run_cli('init', '--adapters', 'codex,claude')
        path = self.root / '.pcdd/installation.json'
        manifest = json.loads(path.read_text())
        manifest['version'] = '0.3.0'
        path.write_text(json.dumps(manifest))
        before = self.snapshot()
        self.run_cli('doctor')
        self.run_cli('update', '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.run_cli('update')
        report = self.run_cli('doctor')
        self.assertEqual(report['installed'], '0.4.0')
        self.assertEqual(report['adapters'], ['codex', 'claude'])
        self.run_cli('rollback')
        self.assertEqual(before, self.snapshot())
        self.run_cli('doctor')

    def test_existing_selection_is_not_changed_implicitly(self):
        self.run_cli('init', '--adapters', 'codex')
        before = self.snapshot()
        for command in ('init', 'update'):
            report = self.run_cli(command, '--adapters', 'codex,antigravity', ok=False)
            self.assertIn('Adapter changes', report['error']['message'])
            self.assertEqual(before, self.snapshot())
        self.assertEqual(self.run_cli('doctor')['adapters'], ['codex'])

    def test_legacy_manifest_cannot_claim_antigravity_and_duplicates_are_invalid(self):
        self.run_cli('init', '--adapters', 'antigravity')
        path = self.root / '.pcdd/installation.json'
        manifest = json.loads(path.read_text())
        for version, adapters in (('0.3.0', ['antigravity']),
                                  ('0.4.0', ['antigravity', 'antigravity'])):
            manifest.update(version=version, adapters=adapters)
            path.write_text(json.dumps(manifest))
            before = self.snapshot()
            self.run_cli('doctor', ok=False)
            self.run_cli('update', ok=False)
            self.assertEqual(before, self.snapshot())

    def test_help_and_validation_include_antigravity_in_both_languages(self):
        for lang in ('es', 'en'):
            report = self.run_cli('--lang', lang, 'init', '--help')
            self.assertIn('antigravity', json.dumps(report))
            for selected in ('unknown', 'antigravity,antigravity', 'codex,antigravity,'):
                error = self.run_cli('--lang', lang, 'init', '--adapters', selected, ok=False)
                self.assertIn('antigravity', error['error']['message'])
        self.assertEqual(self.snapshot(), {})


if __name__ == '__main__':
    unittest.main()
