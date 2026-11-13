import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'pcdd.py'
COMMIT_SKILLS = ('pcdd-commit', 'pcdd-commit-review')


class CommitSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, XDG_CONFIG_HOME=str(self.root / 'preferences'))

    def run_cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(CLI), '--json', '--project',
                                 str(self.root), *args], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        self.assertEqual(result.stderr, '')
        return json.loads(result.stdout)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def legacy_installation(self, version='0.2.0', adapters=('codex', 'claude')):
        # Persisted schema-1 public format, independent of the implementation.
        files = {'.pcdd/core.md': b'Previous core\n',
                 'AGENTS.md': b'<!-- pcdd:begin -->\nPrevious bridge\n<!-- pcdd:end -->'}
        for adapter in adapters:
            folder = '.agents' if adapter == 'codex' else '.claude'
            for skill in ('pcdd-work', 'pcdd-review'):
                files[f'{folder}/skills/{skill}/SKILL.md'] = b'Previous skill\n'
        if 'claude' in adapters:
            files['CLAUDE.md'] = b'<!-- pcdd:begin -->\nPrevious Claude bridge\n<!-- pcdd:end -->'
        manifest = {'schema': 1, 'version': version, 'adapters': list(adapters),
                    'files': {name: hashlib.sha256(data).hexdigest()
                              for name, data in files.items()}}
        files['.pcdd/installation.json'] = json.dumps(manifest).encode()
        files['.pcdd/config.json'] = b'{"schema":1,"gate":["make ready"],"custom":42}'
        files['pcdd/changes/existing.md'] = '## Tasks\n- [ ] T1 (S1) Continuar\n\n## Log\n«sí»\n'.encode()
        files['.agents/skills/git-commit/SKILL.md'] = b'My existing commit skill\n'
        for name, data in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return files

    def test_fresh_install_distributes_four_skills_per_selected_adapter(self):
        for adapters in ('codex', 'claude', 'codex,claude'):
            with self.subTest(adapters=adapters), tempfile.TemporaryDirectory() as tmp:
                self.root = Path(tmp)
                self.run_cli('init', '--adapters', adapters)
                for adapter, folder in (('codex', '.agents'), ('claude', '.claude')):
                    for skill in COMMIT_SKILLS:
                        path = self.root / folder / 'skills' / skill / 'SKILL.md'
                        self.assertEqual(path.exists(), adapter in adapters.split(','))
                        if path.exists():
                            self.assertEqual(path.read_bytes(),
                                             (CLI.parent / 'assets/skills' / skill / 'SKILL.md').read_bytes())
                self.run_cli('doctor')

    def test_legacy_update_preview_preserves_content_and_rollback_restores_inventory(self):
        for version in ('0.1.0', '0.2.0'):
            for adapters in (('codex',), ('claude',), ('codex', 'claude')):
                with self.subTest(version=version, adapters=adapters), tempfile.TemporaryDirectory() as tmp:
                    self.root = Path(tmp)
                    before = self.legacy_installation(version, adapters)
                    self.run_cli('doctor')
                    preview = self.run_cli('update', '--dry-run')
                    self.assertEqual(self.snapshot(), before)
                    folder = '.agents' if 'codex' in adapters else '.claude'
                    self.assertIn(f'{folder}/skills/pcdd-commit/SKILL.md', preview['actions']['create'])
                    self.run_cli('update')
                    self.run_cli('doctor')
                    for name in ('.pcdd/config.json', 'pcdd/changes/existing.md',
                                 '.agents/skills/git-commit/SKILL.md'):
                        self.assertEqual((self.root / name).read_bytes(), before[name])
                    after = self.snapshot()
                    self.run_cli('update')
                    self.assertEqual(self.snapshot(), after)
                    self.run_cli('rollback')
                    self.assertEqual(self.snapshot(), before)
                    self.run_cli('doctor')

    def test_update_rejects_unowned_new_skill_even_when_content_matches(self):
        self.legacy_installation()
        target = self.root / '.agents/skills/pcdd-commit/SKILL.md'
        target.parent.mkdir(parents=True)
        asset = CLI.parent / 'assets/skills/pcdd-commit/SKILL.md'
        target.write_bytes(asset.read_bytes() if asset.exists() else b'Customer commit skill')
        before = self.snapshot()
        for args in (('update', '--dry-run'), ('update',), ('init',)):
            result = self.run_cli(*args, ok=False)
            self.assertIn('Unowned file', result['error']['message'])
            self.assertEqual(self.snapshot(), before)

    def test_update_rejects_symlink_at_new_skill_path(self):
        self.legacy_installation()
        target = self.root / '.claude/skills/pcdd-commit-review/SKILL.md'
        target.parent.mkdir(parents=True)
        outside = self.root / 'customer.txt'
        outside.write_text('Customer content')
        target.symlink_to(outside)
        before = self.snapshot()
        self.run_cli('update', ok=False)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(target.is_symlink())

    def test_current_manifest_cannot_hide_missing_commit_skills(self):
        self.run_cli('init')
        path = self.root / '.pcdd/installation.json'
        manifest = json.loads(path.read_text())
        for name in list(manifest['files']):
            if any(f'/skills/{skill}/' in name for skill in COMMIT_SKILLS):
                del manifest['files'][name]
                (self.root / name).unlink()
        path.write_text(json.dumps(manifest))
        before = self.snapshot()
        self.run_cli('doctor', ok=False)
        self.run_cli('update', ok=False)
        self.assertEqual(self.snapshot(), before)

    def test_partial_legacy_inventory_is_rejected(self):
        self.legacy_installation()
        path = self.root / '.pcdd/installation.json'
        manifest = json.loads(path.read_text())
        del manifest['files']['.agents/skills/pcdd-work/SKILL.md']
        path.write_text(json.dumps(manifest))
        before = self.snapshot()
        self.run_cli('update', ok=False)
        self.assertEqual(self.snapshot(), before)

    def test_interrupted_upgrade_recovers_previous_inventory(self):
        before = self.legacy_installation()
        self.run_cli('update')
        journal = json.loads((self.root / '.pcdd/last-update.json').read_text())
        new_skill = '.claude/skills/pcdd-commit-review/SKILL.md'
        self.assertIn(new_skill, journal)
        # Reproduce a crash with some destinations still holding their old bytes.
        (self.root / new_skill).unlink()
        manifest = '.pcdd/installation.json'
        (self.root / manifest).write_bytes(base64.b64decode(journal[manifest]['before']))
        (self.root / '.pcdd/pending.json').write_text(json.dumps(journal))
        self.run_cli('doctor', ok=False)
        self.run_cli('recover')
        self.assertEqual(self.snapshot(), before)
        self.run_cli('doctor')

    def test_rollback_refuses_later_edits_to_new_skill(self):
        self.legacy_installation()
        self.run_cli('update')
        target = self.root / '.agents/skills/pcdd-commit/SKILL.md'
        self.assertTrue(target.exists())
        target.write_text('User edit after upgrade')
        before = self.snapshot()
        self.run_cli('rollback', ok=False)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
