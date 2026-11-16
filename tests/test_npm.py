import json
import re
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NPM = ROOT / "npm"
LAUNCHER = NPM / "bin" / "pcdd.js"
NODE = shutil.which("node")
VERSION = re.search(r"__version__ = ['\"]([^'\"]+)", (ROOT / "src" / "pcdd_toolkit" / "__init__.py").read_text(encoding="utf-8")).group(1)


@unittest.skipUnless(NPM.is_dir(), "npm/ is not part of this distribution")
class NpmPackageTests(unittest.TestCase):
    def test_manifest(self):
        manifest = json.loads((NPM / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "pcdd")
        self.assertEqual(manifest["version"], VERSION)  # runs exactly this PyPI release
        self.assertEqual(manifest["bin"], {"pcdd": "bin/pcdd.js"})
        self.assertEqual(manifest["files"], ["bin/pcdd.js"])
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["repository"]["directory"], "npm")
        self.assertNotIn("dependencies", manifest)
        self.assertNotIn("scripts", manifest)  # no install hooks
        self.assertEqual((NPM / "LICENSE").read_text(encoding="utf-8"),
                         (ROOT / "LICENSE").read_text(encoding="utf-8"))
        self.assertTrue(LAUNCHER.read_text(encoding="utf-8").startswith("#!/usr/bin/env node\n"))
        self.assertTrue(os.access(LAUNCHER, os.X_OK))

    @unittest.skipUnless(shutil.which("npm"), "npm is not installed")
    def test_published_files(self):
        result = subprocess.run(["npm", "pack", "--dry-run", "--json"], cwd=NPM,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        files = sorted(f["path"] for f in json.loads(result.stdout)[0]["files"])
        self.assertEqual(files, ["LICENSE", "README.md", "bin/pcdd.js", "package.json"])


@unittest.skipUnless(NODE and LAUNCHER.exists(), "node or the launcher is missing")
class NpmLauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        # Only node on PATH: no uv unless a test adds one.
        (self.bin / "node").symlink_to(NODE)

    def fake_uv(self, directory, code=0):
        directory.mkdir(parents=True, exist_ok=True)
        uv = directory / "uv"
        uv.write_text('#!/bin/sh\nprintf "%s|" "$@"\nexit ' + str(code) + "\n", encoding="utf-8")
        uv.chmod(uv.stat().st_mode | stat.S_IEXEC)
        return uv

    def run_launcher(self, *args):
        env = {"PATH": str(self.bin), "HOME": str(self.home)}
        return subprocess.run([NODE, str(LAUNCHER), *args], capture_output=True, text=True, env=env)

    def test_runs_pcdd_through_uv_with_the_same_arguments_and_exit_code(self):
        self.fake_uv(self.bin, code=3)
        result = self.run_launcher("init", "--lang", "es", "a b")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, f"tool|run|pcdd@{VERSION}|init|--lang|es|a b|")

    def test_finds_uv_installed_but_not_yet_on_path(self):
        self.fake_uv(self.home / ".local" / "bin")
        result = self.run_launcher("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"tool|run|pcdd@{VERSION}|--version|")

    def test_forwards_termination_and_waits_for_the_child(self):
        marker = self.tmp / "cleaned"
        uv = self.bin / "uv"
        uv.write_text('#!/bin/sh\ntrap \'sleep 0.3; echo done > "%s"; exit 143\' TERM\n'
                      # Bounded so a regression cannot leave an orphan running.
                      'echo ready\ni=0; while [ $i -lt 60 ]; do sleep 0.05; i=$((i+1)); done\n' % marker,
                      encoding="utf-8")
        uv.chmod(uv.stat().st_mode | stat.S_IEXEC)
        env = {"PATH": str(self.bin), "HOME": str(self.home)}
        proc = subprocess.Popen([NODE, str(LAUNCHER)], stdout=subprocess.PIPE, text=True, env=env)
        self.assertEqual(proc.stdout.readline(), "ready\n")
        proc.terminate()
        code = proc.wait(timeout=5)
        proc.stdout.close()
        self.assertTrue(marker.exists(), "the launcher exited before uv finished cleaning up")
        self.assertIn(code, (143, -15))

    def test_explains_how_to_install_uv_when_missing(self):
        result = self.run_launcher("init")
        self.assertEqual(result.returncode, 127)
        self.assertEqual(result.stdout, "")
        self.assertIn("uv", result.stderr)
        self.assertIn("https://docs.astral.sh/uv/", result.stderr)
        self.assertIn("curl -fsSL https://pcdd.dev/install.sh | sh", result.stderr)


if __name__ == "__main__":
    unittest.main()
