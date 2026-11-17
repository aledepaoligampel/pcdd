import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'pcdd.py'
PACKAGE = CLI.parent / 'src' / 'pcdd_toolkit'


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, ok=True, cli=CLI):
        result = subprocess.run([sys.executable, str(cli), '--json', '--project', str(self.root), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_preview_is_read_only_and_init_is_idempotent(self):
        self.run_cli('init', '--dry-run')
        self.assertEqual(self.snapshot(), {})
        self.run_cli('init')
        before = self.snapshot()
        self.run_cli('init')
        self.assertEqual(before, self.snapshot())
        report = json.loads(self.run_cli('doctor').stdout)
        self.assertEqual(report['adapters'], ['codex', 'claude'])
        self.assertTrue(report['warnings'])

    def test_wrong_json_shape_returns_structured_error_without_writes(self):
        self.run_cli('init')
        self.run_cli('new', 'example')
        cases = [
            ('.pcdd/config.json', ('update', '--dry-run')),
            ('.pcdd/installation.json', ('doctor',)),
            ('.pcdd/last-update.json', ('rollback',)),
        ]
        for name, command in cases:
            path = self.root / name
            original = path.read_bytes() if path.exists() else None
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                for value in ([1], 'invalid', 1, True):
                    with self.subTest(name=name, value=value):
                        path.write_text(json.dumps(value))
                        before = self.snapshot()
                        result = self.run_cli(*command, ok=False)
                        self.assertIn('error', json.loads(result.stdout))
                        self.assertEqual(result.stderr, '')
                        self.assertEqual(before, self.snapshot())
            finally:
                if original is None:
                    path.unlink()
                else:
                    path.write_bytes(original)

    def test_preserves_user_instructions_and_config(self):
        original = b'# Project\r\n\r\nKeep this exactly.\r\n'
        (self.root / 'AGENTS.md').write_bytes(original)
        (self.root / 'CLAUDE.md').write_text('My Claude instructions')
        self.run_cli('init')
        self.assertTrue((self.root / 'AGENTS.md').read_bytes().startswith(original))
        with (self.root / 'AGENTS.md').open('ab') as stream:
            stream.write(b'\nCustomer addition\n')
        config = self.root / '.pcdd/config.json'
        config.write_text('{"schema":1,"gate":["custom test"],"custom":true}')
        before = self.snapshot()
        self.run_cli('update')
        self.assertEqual(before, self.snapshot())

    def test_managed_conflict_never_overwrites(self):
        self.run_cli('init')
        (self.root / '.pcdd/core.md').write_text('My customization')
        before = self.snapshot()
        self.run_cli('update', ok=False)
        self.assertEqual(before, self.snapshot())
        self.run_cli('doctor', ok=False)

    def test_unowned_skill_and_symlinks_are_not_adopted(self):
        path = self.root / '.agents/skills/pcdd-work'
        path.mkdir(parents=True)
        (path / 'SKILL.md').write_text('Customer skill')
        self.run_cli('init', ok=False)
        self.assertFalse((self.root / 'AGENTS.md').exists())
        (self.root / 'AGENTS.md').symlink_to(path / 'SKILL.md')
        self.run_cli('init', '--dry-run', ok=False)
        self.assertEqual((path / 'SKILL.md').read_text(), 'Customer skill')

    def test_malformed_markers_and_path_traversal_fail(self):
        (self.root / 'AGENTS.md').write_text('<!-- pcdd:begin -->\nmissing end')
        self.run_cli('init', ok=False)
        (self.root / 'AGENTS.md').unlink()
        self.run_cli('init')
        self.run_cli('new', '../outside', ok=False)

    def test_single_adapter(self):
        self.run_cli('init', '--adapters', 'codex')
        self.assertFalse((self.root / '.claude').exists())
        self.assertFalse((self.root / 'CLAUDE.md').exists())
        self.run_cli('doctor')

    def test_rollback_preserves_changes_and_refuses_later_edits(self):
        (self.root / 'AGENTS.md').write_text('Original')
        self.run_cli('init')
        self.run_cli('new', 'example')
        self.run_cli('rollback')
        self.assertEqual((self.root / 'AGENTS.md').read_text(), 'Original')
        self.assertTrue((self.root / 'pcdd/changes/example.md').exists())
        self.run_cli('init')
        with (self.root / 'AGENTS.md').open('a') as stream:
            stream.write('\nLater edit')
        before = self.snapshot()
        self.run_cli('rollback', ok=False)
        self.assertEqual(before, self.snapshot())

    def test_update_new_assets_and_rollback(self):
        self.run_cli('init')
        old = (self.root / '.pcdd/core.md').read_bytes()
        with tempfile.TemporaryDirectory() as distribution:
            dist = Path(distribution)
            shutil.copy(CLI, dist / 'pcdd.py')
            shutil.copytree(PACKAGE, dist / 'src/pcdd_toolkit',
                            ignore=shutil.ignore_patterns('__pycache__'))
            (dist / 'src/pcdd_toolkit/assets/core.md').write_bytes(old + b'\nNew release rule\n')
            before = self.snapshot()
            self.run_cli('update', '--dry-run', cli=dist / 'pcdd.py')
            self.assertEqual(before, self.snapshot())
            self.run_cli('update', cli=dist / 'pcdd.py')
        self.assertIn(b'New release rule', (self.root / '.pcdd/core.md').read_bytes())
        self.run_cli('doctor')
        self.run_cli('rollback')
        self.assertEqual(old, (self.root / '.pcdd/core.md').read_bytes())
        self.run_cli('doctor')

    def test_recovers_partial_transaction_and_rejects_modified_files(self):
        self.run_cli('init')
        journal = self.root / '.pcdd/last-update.json'
        pending = self.root / '.pcdd/pending.json'
        pending.write_bytes(journal.read_bytes())
        (self.root / 'CLAUDE.md').unlink()  # interruption before writing one file
        self.run_cli('doctor', ok=False)
        self.run_cli('update', ok=False)
        self.run_cli('recover')
        self.assertFalse((self.root / 'AGENTS.md').exists())
        self.assertFalse(pending.exists())

    def test_forged_journal_cannot_write_arbitrary_path(self):
        self.run_cli('init')
        target = self.root / 'private.txt'
        target.write_text('Private')
        (self.root / '.pcdd/pending.json').write_text(json.dumps({
            'private.txt': {'before': None, 'after': 'UHJpdmF0ZQ=='}}))
        self.run_cli('recover', ok=False)
        self.assertEqual(target.read_text(), 'Private')

    def test_status_reports_task_progress_without_writes(self):
        self.run_cli('init')
        self.run_cli('new', 'example')
        change = self.root / 'pcdd/changes/example.md'
        change.write_text('# Example\n\n## Tasks\n\n- [x] T1 (S1) Done\n'
                          '- [>] T2 (S2) Working\n\n## Evidence\nT1 passed\n')
        before = self.snapshot()
        report = json.loads(self.run_cli('status', 'example').stdout)
        self.assertEqual(before, self.snapshot())
        self.assertEqual((report['change'], report['completed'], report['total']), ('example', 1, 2))
        self.assertEqual(report['acceptance'], 'requires_user_confirmation')
        self.assertNotIn('recorded_seconds', report)
        (self.root / '.pcdd/lock').write_text('other-process')
        before = self.snapshot()
        self.run_cli('status', 'example')
        self.assertEqual(before, self.snapshot())
        change.write_text('## Tasks\n- [x] T1 duplicate\n- [ ] T1 duplicate\n')
        self.run_cli('status', 'example', ok=False)

    def test_time_command_is_removed_and_old_records_are_untouched(self):
        self.run_cli('init')
        self.run_cli('new', 'example')
        record = self.root / '.pcdd/time/example.json'
        record.parent.mkdir(parents=True)
        for content in ('not json', json.dumps({'schema': 1, 'seconds': 10, 'sessions': 1,
                                                'active': 1.0, 'incomplete': 0})):
            record.write_text(content)
            before = self.snapshot()
            self.run_cli('time', 'status', 'example', ok=False)
            self.run_cli('status', 'example')
            self.run_cli('doctor')
            self.assertEqual(before, self.snapshot())

    def test_existing_lock_blocks_writes(self):
        self.run_cli('init')
        (self.root / '.pcdd/lock').write_text('other-process')
        before = self.snapshot()
        self.run_cli('update', ok=False)
        self.assertEqual(before, self.snapshot())

    def test_foreign_temporary_file_is_preserved(self):
        metadata = self.root / '.pcdd'
        metadata.mkdir()
        foreign = metadata / 'core.md.pcdd-tmp'
        foreign.write_text('User file')
        self.run_cli('init')
        self.assertEqual(foreign.read_text(), 'User file')
        self.run_cli('doctor')

    def test_doctor_reports_stale_or_active_lock(self):
        self.run_cli('init')
        (self.root / '.pcdd/lock').write_text('other-process')
        self.run_cli('doctor', ok=False)

    def test_invalid_transaction_destination_fails_before_project_writes(self):
        (self.root / '.pcdd/last-update.json').mkdir(parents=True)
        before = self.snapshot()
        self.run_cli('init', '--dry-run', ok=False)
        self.run_cli('init', ok=False)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.root / 'AGENTS.md').exists())

    def test_missing_configuration_blocks_update(self):
        self.run_cli('init')
        (self.root / '.pcdd/config.json').unlink()
        before = self.snapshot()
        self.run_cli('update', ok=False)
        self.assertEqual(before, self.snapshot())

    def test_recover_preflights_all_journal_destinations(self):
        self.run_cli('init')
        last = self.root / '.pcdd/last-update.json'
        (self.root / '.pcdd/pending.json').write_bytes(last.read_bytes())
        last.unlink()
        last.mkdir()
        before = self.snapshot()
        self.run_cli('recover', ok=False)
        self.assertEqual(before, self.snapshot())


if __name__ == '__main__':
    unittest.main()
