"""Localized terminal presentation; machine responses remain language-independent."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading

LOCALES = Path(__file__).resolve().parent / 'locales'


def language_code(value):
    return re.split(r'[-_.@]', value.strip().lower())[0]


def preference_path():
    base = os.environ.get('XDG_CONFIG_HOME')
    root = Path(base) if base and Path(base).is_absolute() else Path.home() / '.config'
    return root / 'pcdd' / 'preferences.json'


def preferences():
    path = preference_path()
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Unsafe preference path')
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('language', 'auto') not in ('es', 'en', 'auto'):
        raise ValueError('Invalid language preference')
    return data


def save_language(language):
    path = preference_path()
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Unsafe preference path')
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix('.lock')
    with lock.open('x'):
        pass
    temporary = None
    try:
        data = preferences()
        data['language'] = language
        descriptor, filename = tempfile.mkstemp(prefix='.preferences-', dir=path.parent)
        temporary = Path(filename)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


def detect_language(explicit=None):
    if explicit:
        return explicit if explicit in ('es', 'en') else 'es'
    saved = preferences().get('language', 'auto')
    if saved != 'auto':
        return saved
    # POSIX precedence: the first nonempty locale owns the choice. C/POSIX
    # carries no user language, so macOS can supply the preference instead.
    selected = next((os.environ[key] for key in ('LC_ALL', 'LC_MESSAGES', 'LANG')
                     if os.environ.get(key)), '')
    code = language_code(selected)
    if code not in ('', 'c', 'posix'):
        return code if code in ('es', 'en') else 'es'
    if sys.platform == 'darwin':
        try:
            result = subprocess.run(['/usr/bin/defaults', 'read', '-g', 'AppleLanguages'],
                                    capture_output=True, text=True, timeout=1)
            matches = re.findall(r'[\s(" ,]([a-z]{2,3})(?:[-_][A-Za-z0-9]+)*', result.stdout)
            if result.returncode == 0 and matches:
                return matches[0] if matches[0] in ('es', 'en') else 'es'
        except (OSError, subprocess.TimeoutExpired):
            pass
    return 'es'


def safe_print(text, stream=sys.stdout, **kwargs):
    encoding = stream.encoding or 'utf-8'
    # Keep redirects and ASCII-only terminals usable, including paths/accents.
    print(text.encode(encoding, errors='replace').decode(encoding), file=stream, **kwargs)


class Presentation:
    def __init__(self, language='es', machine=False):
        self.language = language
        self.machine = machine
        self.messages = json.loads((LOCALES / (language + '.json')).read_text(encoding='utf-8'))

    def text(self, key, **values):
        return self.messages[key].format(**values)

    def styled(self, text, tone, stream=None):
        stream = stream or sys.stdout
        if (self.machine or not stream.isatty() or 'NO_COLOR' in os.environ
                or os.environ.get('TERM', '') in ('', 'dumb')):
            return text
        codes = {'brand': '1;36', 'success': '32', 'warning': '33',
                 'error': '31', 'secondary': '2'}
        return '\x1b[' + codes[tone] + 'm' + text + '\x1b[0m'

    def logo(self):
        if self.machine:
            return
        symbol = '›_'
        try:
            symbol.encode(sys.stdout.encoding or 'utf-8')
        except UnicodeEncodeError:
            symbol = '>_'
        safe_print('\n  ' + self.styled(symbol + ' pcdd', 'brand') +
                   '\n  Progressive Change-Driven Development\n  ' +
                   self.styled(self.text('tagline'), 'secondary') + '\n')

    @contextmanager
    def step(self, command):
        enabled = (not self.machine and sys.stdout.isatty() and sys.stderr.isatty()
                   and os.environ.get('TERM', '') != 'dumb' and 'NO_COLOR' not in os.environ)
        if not enabled:
            yield
            return
        message = self.text('working_' + command)
        stopped = threading.Event()

        def animate():
            frames = '|/-\\'
            index = 0
            while not stopped.is_set():
                safe_print('\r  ' + frames[index % 4] + ' ' + message,
                           stream=sys.stderr, end='', flush=True)
                index += 1
                stopped.wait(0.08)
        worker = threading.Thread(target=animate, daemon=True)
        worker.start()
        try:
            yield
        finally:
            stopped.set()
            worker.join()
            safe_print('\r' + ' ' * (len(message) + 5) + '\r', stream=sys.stderr,
                       end='', flush=True)

    def result(self, command, data):
        if self.machine:
            print(json.dumps(data, ensure_ascii=True))
            return
        if command in ('init', 'update'):
            safe_print(self.styled(self.text('preview'), 'warning') if data['dry_run']
                       else self.styled(self.text('ready'), 'success'))
            if not data['files']:
                safe_print(self.styled(self.text('unchanged'), 'secondary'))
            for action, paths in data['actions'].items():
                for path in paths:
                    tone = {'create': 'success', 'update': 'warning', 'preserve': 'secondary'}[action]
                    safe_print('  ' + self.styled(self.text(action), tone) + '  ' + path)
            safe_print('\n' + self.styled(self.text('preserved'), 'secondary'))
            safe_print(self.text('apply') if data['dry_run'] else self.text('next'))
        elif command == 'doctor':
            safe_print(self.styled(self.text('healthy', version=data['installed']), 'success'))
            for warning in data['warnings']:
                safe_print(self.styled(self.text('gate_warning'), 'warning'))
        elif command in ('rollback', 'recover'):
            safe_print(self.styled(self.text('restored'), 'success'))
        elif command == 'new':
            safe_print(self.text('change_created', path=data['path']))
        elif command == 'language':
            safe_print(self.text('language_saved' if data['saved'] else 'language_current',
                                 language=data['language'], path=data['path']))
        elif command == 'time':
            safe_print(self.text('progress', done=data['completed'], total=data['total'],
                                 seconds=data['recorded_seconds']))
            if data['open_interval_seconds'] is not None:
                safe_print(self.text('open_interval', seconds=data['open_interval_seconds']))
            if data['incomplete_intervals']:
                safe_print(self.text('incomplete', count=data['incomplete_intervals']))
            safe_print(self.text('acceptance'))

    def error(self, error, code='conflict'):
        message = str(error)
        if self.machine:
            print(json.dumps({'error': {'code': code, 'message': message}}, ensure_ascii=True))
            return
        translations = self.messages['errors']
        translated = None
        for prefix in sorted(translations, key=len, reverse=True):
            if message.startswith(prefix):
                translated = translations[prefix] + message[len(prefix):]
                break
        if translated is None:
            translated = self.text('unexpected')
            if isinstance(error, OSError) and error.filename:
                translated += ' ' + str(error.filename)
        safe_print(self.styled('PCDD: ' + translated, 'error', sys.stderr), stream=sys.stderr)
        safe_print(self.text('error_hint'), stream=sys.stderr)


def build_parser(ui, version):
    class Formatter(argparse.HelpFormatter):
        def _format_usage(self, usage, actions, groups, prefix):
            return super()._format_usage(usage, actions, groups,
                                         ui.text('usage') + ': ' if prefix is None else prefix)

    class Parser(argparse.ArgumentParser):
        def __init__(self, *args, **kwargs):
            kwargs.update(add_help=False, formatter_class=Formatter, allow_abbrev=False)
            super().__init__(*args, **kwargs)
            self._positionals.title = ui.text('commands')
            self._optionals.title = ui.text('options')
            self.add_argument('-h', '--help', action='help', help=ui.text('help'))
            self.add_argument('--lang', choices=['es', 'en'], default=argparse.SUPPRESS,
                              help=ui.text('lang_help'))
            self.add_argument('--json', action='store_true', default=argparse.SUPPRESS,
                              help=ui.text('json_help'))

        def error(self, message):
            if not ui.machine:
                self.print_usage(sys.stderr)
            ui.error(ValueError('Invalid arguments; run pcdd --help'), 'arguments')
            raise SystemExit(2)

        def print_help(self, file=None):
            if ui.machine:
                print(json.dumps({'help': self.format_help()}, ensure_ascii=True))
            else:
                safe_print(self.format_help(), stream=file or sys.stdout, end='')

    class Version(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print(json.dumps({'version': version}) if ui.machine else version)
            parser.exit()

    parser = Parser(prog='pcdd', description=ui.text('description'))
    parser.add_argument('--version', action=Version, nargs=0, help=ui.text('version_help'))
    parser.add_argument('--project', default='.', help=ui.text('project_help'))
    subs = parser.add_subparsers(dest='command', required=True)
    for command in ('init', 'update', 'doctor', 'rollback', 'recover', 'new', 'time', 'language'):
        child = subs.add_parser(command, help=ui.text('command_' + command),
                                description=ui.text('command_' + command))
        if command in ('init', 'update'):
            child.add_argument('--dry-run', action='store_true', help=ui.text('dry_help'))
            child.add_argument('--adapters', help=ui.text('adapters_help'))
        elif command == 'new':
            child.add_argument('change', help=ui.text('change_help'))
        elif command == 'time':
            child.add_argument('action', choices=['start', 'pause', 'stop', 'abandon', 'status'],
                               help=ui.text('time_help'))
            child.add_argument('change', help=ui.text('change_help'))
        elif command == 'language':
            child.add_argument('language', nargs='?', choices=['es', 'en', 'auto'],
                               help=ui.text('preference_help'))
    return parser
