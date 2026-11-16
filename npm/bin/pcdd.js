#!/usr/bin/env node
// Runs the PCDD command-line tool (a Python package on PyPI) through uv, pinned to
// the release that matches this package's version:
//   npx @pcdd-dev/cli@X.Y.Z <args>  ->  uv tool run pcdd@X.Y.Z <args>
'use strict';

const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { version } = require('../package.json');
const ARGS = ['tool', 'run', 'pcdd@' + version, ...process.argv.slice(2)];

function candidates() {
  const exe = process.platform === 'win32' ? 'uv.exe' : 'uv';
  let home = '';
  try { home = os.homedir(); } catch (e) { /* no home directory */ }
  const dirs = [
    process.env.UV_INSTALL_DIR,
    process.env.XDG_BIN_HOME,
    home && path.join(home, '.local', 'bin'),
    home && path.join(home, '.cargo', 'bin'),
  ];
  return dirs.filter(Boolean).map((dir) => path.join(dir, exe));
}

function missingUv() {
  process.stderr.write([
    'pcdd: uv is required to run PCDD from npm (https://docs.astral.sh/uv/).',
    '',
    'Install PCDD with uv in one step:',
    '  curl -fsSL https://pcdd.dev/install.sh | sh',
    '',
    'Or install uv yourself and run npx @pcdd-dev/cli again:',
    '  macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh',
    '  Windows:     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"',
    '',
  ].join('\n'));
  process.exit(127);
}

// The terminal already delivers Ctrl+C and Ctrl+\ to uv; wait for it to finish.
// Termination requests sent only to this process are forwarded to uv.
const IGNORED = ['SIGINT', 'SIGQUIT'];
const FORWARDED = ['SIGTERM', 'SIGHUP'];
let child = null;
const handlers = {};
for (const sig of IGNORED) handlers[sig] = () => {};
for (const sig of FORWARDED) handlers[sig] = () => { if (child) child.kill(sig); };
for (const sig of Object.keys(handlers)) {
  try { process.on(sig, handlers[sig]); } catch (e) { /* unsupported on this platform */ }
}

function finish(code, signal) {
  for (const sig of Object.keys(handlers)) process.removeListener(sig, handlers[sig]);
  if (signal) {
    if (process.platform !== 'win32') {
      try { process.kill(process.pid, signal); } catch (e) { /* fall through */ }
    }
    process.exit(128 + (os.constants.signals[signal] || 0));
  }
  process.exit(code === null ? 1 : code);
}

function run(uv, fallbacks) {
  child = spawn(uv, ARGS, { stdio: 'inherit' });
  child.on('error', (err) => {
    if (err.code === 'ENOENT') {
      if (fallbacks.length) return run(fallbacks[0], fallbacks.slice(1));
      return missingUv();
    }
    process.stderr.write('pcdd: could not run ' + uv + ': ' + err.message + '\n');
    process.exit(1);
  });
  child.on('exit', finish);
}

run('uv', candidates().filter((file) => fs.existsSync(file)));
