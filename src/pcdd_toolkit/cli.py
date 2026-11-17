"""PCDD: local, dependency-free project workflow kit."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from contextlib import contextmanager
from . import __version__
from .presentation import Presentation, build_parser, detect_language, preference_path, save_language

VERSION = __version__
ASSETS = Path(__file__).resolve().parent / 'assets'
BEGIN, END = '<!-- pcdd:begin -->', '<!-- pcdd:end -->'
INTERNAL = {'.pcdd/installation.json', '.pcdd/config.json'}
LEGACY_SKILLS = ('pcdd-work', 'pcdd-review')
SKILLS = LEGACY_SKILLS + ('pcdd-commit', 'pcdd-commit-review')
VERSION_SKILLS = {'0.1.0': LEGACY_SKILLS, '0.2.0': LEGACY_SKILLS,
                  '0.3.0': SKILLS, '0.4.0': SKILLS, '0.5.0': SKILLS, VERSION: SKILLS}
CODEX_CLAUDE_ONLY = {'0.1.0', '0.2.0', '0.3.0'}
ADAPTER_FOLDERS = {'codex': '.agents', 'claude': '.claude', 'antigravity': '.agents'}


class Conflict(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return None if value is None else base64.b64encode(value).decode()


def decoded(value):
    return None if value is None else base64.b64decode(value, validate=True)


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def managed_paths(adapters, skills=SKILLS):
    paths = {'AGENTS.md', '.pcdd/core.md'} | INTERNAL
    for adapter in adapters:
        folder = ADAPTER_FOLDERS[adapter]
        paths.update(f'{folder}/skills/{skill}/SKILL.md'
                     for skill in skills)
    if 'claude' in adapters:
        paths.add('CLAUDE.md')
    return paths


class Project:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise Conflict('Project directory does not exist')

    def path(self, name):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise Conflict('Unsafe path: ' + name)
        path = self.root
        for part in relative.parts:
            path = path / part
            if path.is_symlink():
                raise Conflict('Symlink is not managed: ' + name)
        return path

    def read(self, name):
        path = self.path(name)
        if path.exists() and not path.is_file():
            raise Conflict('Expected regular file: ' + name)
        return path.read_bytes() if path.exists() else None

    def load(self, name):
        value = self.read(name)
        parsed = json.loads(value) if value else None
        if parsed is not None and not isinstance(parsed, dict):
            raise Conflict('Expected JSON object: ' + name)
        return parsed

    def write(self, name, data):
        path = self.path(name)
        if data is None:
            path.unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, filename = tempfile.mkstemp(prefix='.pcdd-write-', dir=path.parent)
        temporary = Path(filename)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @contextmanager
    def lock(self):
        lock = self.path('.pcdd/lock')
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            stream = lock.open('x')
        except FileExistsError:
            raise Conflict('Another operation or interrupted process owns .pcdd/lock; '
                           'verify it is stopped before removing that lock')
        try:
            stream.write(str(os.getpid()))
            stream.close()
            yield
        finally:
            lock.unlink(missing_ok=True)

    def pending(self):
        if self.read('.pcdd/pending.json'):
            raise Conflict('Interrupted transaction: run recover before writing')

    def transaction(self, changes):
        if not changes:
            return
        record = {name: {'before': encoded(self.read(name)), 'after': encoded(data)}
                  for name, data in changes.items()}
        self.write('.pcdd/pending.json', json_bytes(record))
        # A crash leaves the journal for explicit recovery, not a false success.
        for name, data in changes.items():
            self.write(name, data)
        self.write('.pcdd/last-update.json', json_bytes(record))
        self.write('.pcdd/pending.json', None)


def bridge(original, text):
    original = original or b''
    start, end = BEGIN.encode(), END.encode()
    if original.count(start) != original.count(end) or original.count(start) > 1:
        raise Conflict('Invalid or duplicate PCDD markers')
    block = (BEGIN + '\n' + text + '\n' + END).encode()
    if start not in original:
        separator = b'' if not original or original.endswith(b'\n') else b'\n'
        return original + separator + block + b'\n'
    left, right = original.index(start), original.index(end)
    if left > right:
        raise Conflict('Invalid PCDD marker order')
    return original[:left] + block + original[right + len(end):]


def block_hash(data):
    if data is None or data.count(BEGIN.encode()) != 1 or data.count(END.encode()) != 1:
        raise Conflict('Missing or duplicate PCDD bridge')
    left, right = data.index(BEGIN.encode()), data.index(END.encode())
    if left > right:
        raise Conflict('Invalid PCDD marker order')
    return digest(data[left:right + len(END)])


def hash_file(name, data):
    return block_hash(data) if name in ('AGENTS.md', 'CLAUDE.md') else digest(data)


def installation(project):
    manifest = project.load('.pcdd/installation.json')
    if not manifest or manifest.get('schema') != 1:
        raise Conflict('Missing or unsupported installation; run init')
    skills = VERSION_SKILLS.get(manifest.get('version'))
    if skills is None:
        raise Conflict('Invalid managed file list')
    adapters = manifest.get('adapters', [])
    supported = ('codex', 'claude') if manifest['version'] in CODEX_CLAUDE_ONLY else ADAPTER_FOLDERS
    if (not isinstance(adapters, list) or not adapters
            or any(not isinstance(a, str) or a not in supported for a in adapters)
            or len(set(adapters)) != len(adapters)):
        raise Conflict('Invalid adapters')
    expected = managed_paths(adapters, skills) - INTERNAL
    if not isinstance(manifest.get('files'), dict) or set(manifest['files']) != expected:
        raise Conflict('Invalid managed file list')
    return manifest


def verify_files(project, manifest):
    for name, expected in manifest['files'].items():
        data = project.read(name)
        if data is None or hash_file(name, data) != expected:
            raise Conflict('Managed file changed or missing: ' + name)


def install(project, args):
    project.pending()
    project.read('.pcdd/last-update.json')  # Preflight metadata destinations too.
    previous = project.load('.pcdd/installation.json')
    if args.command == 'update' and not previous:
        raise Conflict('Not installed; run init')
    if previous:
        previous = installation(project)
        verify_files(project, previous)
        adapters = previous['adapters']
        if args.adapters and args.adapters.split(',') != adapters:
            raise Conflict('Adapter changes require a separate installation plan')
    else:
        adapters = (args.adapters or 'codex,claude').split(',')
        if len(set(adapters)) != len(adapters) or any(a not in ADAPTER_FOLDERS for a in adapters):
            raise Conflict('Adapters must be a comma-separated selection of codex, claude, antigravity')
    desired = {'.pcdd/core.md': (ASSETS / 'core.md').read_bytes()}
    desired['AGENTS.md'] = bridge(project.read('AGENTS.md'),
                                'Read `.pcdd/core.md` for the workflow. Load only relevant skills.')
    if 'claude' in adapters:
        desired['CLAUDE.md'] = bridge(project.read('CLAUDE.md'),
                                     'Read `AGENTS.md` and `.pcdd/core.md` before working on this project.')
    for adapter in adapters:
        folder = ADAPTER_FOLDERS[adapter]
        for skill in SKILLS:
            desired[f'{folder}/skills/{skill}/SKILL.md'] = (ASSETS / 'skills' / skill / 'SKILL.md').read_bytes()
    owned = previous['files'] if previous else {}
    for name in desired:
        if name not in ('AGENTS.md', 'CLAUDE.md') and name not in owned and project.read(name) is not None:
            raise Conflict('Unowned file already exists: ' + name)
    if not previous:
        if project.read('.pcdd/config.json') is None:
            desired['.pcdd/config.json'] = json_bytes({'schema': 1, 'gate': [], 'database_gate': []})
    config = project.load('.pcdd/config.json')
    if previous and config is None:
        raise Conflict('Missing project configuration')
    if config is not None and (config.get('schema') != 1 or
                              not isinstance(config.get('gate'), list)):
        raise Conflict('Invalid project configuration')
    manifest = {'schema': 1, 'version': VERSION, 'adapters': adapters,
                'files': {name: hash_file(name, data) for name, data in desired.items()
                          if name not in INTERNAL}}
    desired['.pcdd/installation.json'] = json_bytes(manifest)
    changes = {name: data for name, data in desired.items() if project.read(name) != data}
    actions = {'create': [], 'update': [], 'preserve': []}
    for name in desired:
        action = 'preserve' if name not in changes else ('create' if project.read(name) is None else 'update')
        actions[action].append(name)
    if not args.dry_run:
        project.transaction(changes)
    return {'version': VERSION, 'dry_run': args.dry_run, 'files': list(changes), 'actions': actions}


def restore(project, recovery=False):
    project.read('.pcdd/last-update.json')
    project.read('.pcdd/pending.json')
    if not recovery:
        project.pending()
    source = '.pcdd/pending.json' if recovery else '.pcdd/last-update.json'
    record = project.load(source)
    if not record:
        raise Conflict('No transaction to restore')
    allowed = managed_paths(ADAPTER_FOLDERS)
    changes = {}
    for name, entry in record.items():
        if name not in allowed:
            raise Conflict('Unsafe journal path: ' + name)
        before, after = decoded(entry['before']), decoded(entry['after'])
        current = project.read(name)
        if current != after and not (recovery and current == before):
            raise Conflict('Later edit prevents restore: ' + name)
        changes[name] = before
    # Recovery is repeatable after another interruption.
    if not recovery:
        project.write('.pcdd/pending.json', json_bytes({
            name: {'before': encoded(data), 'after': record[name]['after']}
            for name, data in changes.items()}))
    for name, data in changes.items():
        project.write(name, data)
    project.write('.pcdd/last-update.json', None)
    project.write('.pcdd/pending.json', None)
    return {'restored': True}


def change_path(name):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise Conflict('Change name must use lowercase letters, digits and hyphens')
    return f'pcdd/changes/{name}.md'


def progress(project, name):
    data = project.read(change_path(name))
    if data is None:
        raise Conflict('Change document not found')
    section = re.search(r'^## Tasks\s*\n(.*?)(?=^## |\Z)', data.decode(), re.M | re.S)
    if not section:
        raise Conflict('Missing Tasks section')
    tasks = {}
    for line in section[1].splitlines():
        if not line.strip() or line.startswith('<!--'):
            continue
        match = re.fullmatch(r'- \[([ x>!])\] (T\d+) (.+)', line)
        if not match or match[2] in tasks:
            raise Conflict('Invalid or duplicate task: ' + line)
        tasks[match[2]] = {'state': match[1], 'description': match[3]}
    return tasks


def status(project, args):
    project.pending()
    installation(project)
    tasks = progress(project, args.change)
    return {'change': args.change,
            'completed': sum(t['state'] == 'x' for t in tasks.values()),
            'total': len(tasks), 'tasks': tasks,
            'acceptance': 'requires_user_confirmation'}


def main():
    argv = sys.argv[1:]
    machine = '--json' in argv
    ui = Presentation('es', machine)
    try:
        explicit = None
        for index, item in enumerate(argv):
            if item == '--lang' and index + 1 < len(argv):
                explicit = argv[index + 1]
            elif item.startswith('--lang='):
                explicit = item.split('=', 1)[1]
        ui = Presentation(detect_language(explicit), machine)
        parser = build_parser(ui, VERSION)
        args = parser.parse_args(argv)
        if args.command == 'language':
            if args.language:
                save_language(args.language)
            ui.result('language', {'language': args.language or ui.language,
                                   'path': str(preference_path()), 'saved': bool(args.language)})
            return
        run_project(args, ui)
    except (Conflict, OSError, ValueError, KeyError, TypeError) as error:
        ui.error(error, 'conflict' if isinstance(error, Conflict) else 'invalid_state')
        raise SystemExit(1)


def run_project(args, ui):
    project = Project(args.project)
    readonly = getattr(args, 'dry_run', False) or args.command in ('doctor', 'status')
    if args.command in ('init', 'update'):
        ui.logo()

    def execute():
        if args.command in ('init', 'update'):
            return install(project, args)
        elif args.command in ('rollback', 'recover'):
            return restore(project, args.command == 'recover')
        elif args.command == 'doctor':
            if project.read('.pcdd/lock') is not None:
                raise Conflict('Active or stale lock: verify owning process before removing .pcdd/lock')
            project.pending()
            manifest = installation(project)
            verify_files(project, manifest)
            config = project.load('.pcdd/config.json')
            if not config or config.get('schema') != 1 or not isinstance(config.get('gate'), list):
                raise Conflict('Invalid project configuration')
            return {'installed': manifest['version'], 'cli': VERSION,
                              'adapters': manifest['adapters'],
                              'warnings': [] if config['gate'] else ['Configure project gate before committing']}
        elif args.command == 'new':
            project.pending()
            installation(project)
            name = change_path(args.change)
            if project.read(name) is not None:
                raise Conflict('Change already exists')
            project.write(name, (ASSETS / 'change.md').read_bytes().replace(b'{{name}}', args.change.encode()))
            return {'path': name}
        else:
            return status(project, args)
    with ui.step(args.command):
        if readonly:
            report = execute()
        else:
            with project.lock():
                report = execute()
    ui.result(args.command, report)


if __name__ == '__main__':
    main()
