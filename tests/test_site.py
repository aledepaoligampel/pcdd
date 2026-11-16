import base64
import gzip
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PAGES = {"en": SITE / "index.html", "es": SITE / "es" / "index.html"}


class Outline(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = []
        self.attrs = []
        self.inline_scripts = []
        self.structured = []
        self._in_script = False
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        self.attrs.append((tag, a))
        if "id" in a:
            self.ids.append(a["id"])
        self._in_script = tag == "script" and "src" not in a and a.get("type") != "application/ld+json"
        self._in_ld = tag == "script" and a.get("type") == "application/ld+json"

    def handle_endtag(self, tag):
        self._in_script = False
        self._in_ld = False

    def handle_data(self, data):
        if self._in_script and data.strip():
            self.inline_scripts.append(data)
        if self._in_ld:
            self.structured.append(data)


def outline(path):
    parser = Outline()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


@unittest.skipUnless(SITE.is_dir(), "site/ is not part of this distribution")
class SiteTests(unittest.TestCase):
    def test_pages_are_generated_from_the_current_template(self):
        result = subprocess.run([sys.executable, str(ROOT / "bin" / "build_site.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_both_languages_have_the_same_structure(self):
        en, es = outline(PAGES["en"]), outline(PAGES["es"])
        self.assertEqual(en.ids, es.ids)
        for tag in ("section", "h1", "h2", "h3", "li", "button", "figure", "code", "svg"):
            self.assertEqual(en.tags.count(tag), es.tags.count(tag), tag)

    def test_language_metadata(self):
        for lang, path in PAGES.items():
            html = path.read_text(encoding="utf-8")
            self.assertIn(f'<html lang="{lang}">', html)
            self.assertIn('hreflang="en" href="https://pcdd.dev/"', html)
            self.assertIn('hreflang="es" href="https://pcdd.dev/es/"', html)
            self.assertIn('hreflang="x-default"', html)
            canonical = "https://pcdd.dev/" if lang == "en" else "https://pcdd.dev/es/"
            self.assertIn(f'<link rel="canonical" href="{canonical}">', html)

    def test_only_local_assets_are_loaded(self):
        for path in PAGES.values():
            for tag, attrs in outline(path).attrs:
                if tag == "script" and "src" in attrs:
                    self.assertTrue(attrs["src"].startswith("/"), attrs)
                if tag == "link" and attrs.get("rel") in ("stylesheet", "preload", "icon"):
                    self.assertTrue(attrs["href"].startswith("/"), attrs)
                if tag == "img":
                    self.fail("unexpected image: %s" % attrs)

    def test_pages_work_under_the_strict_content_security_policy(self):
        headers = (SITE / "_headers").read_text(encoding="utf-8")
        # Cloudflare Web Analytics injects its beacon; it is the only third party allowed.
        self.assertIn("script-src 'self' https://static.cloudflareinsights.com;", headers)
        self.assertIn("connect-src 'self' https://cloudflareinsights.com;", headers)
        self.assertNotIn("api.github.com", headers)
        self.assertIn("style-src 'self';", headers)
        self.assertIn("Strict-Transport-Security: max-age=31536000; includeSubDomains", headers)
        self.assertIn("Cross-Origin-Opener-Policy: same-origin", headers)
        for path in PAGES.values():
            parsed = outline(path)
            self.assertEqual(parsed.inline_scripts, [], path)
            for tag, attrs in parsed.attrs:
                self.assertNotIn("style", attrs, (path, tag))
                self.assertFalse(any(k.startswith("on") for k in attrs), (path, tag))

    def test_css_and_js_urls_carry_their_content_hash(self):
        for name in ("site.css", "site.js"):
            digest = hashlib.sha256((SITE / "assets" / name).read_bytes()).hexdigest()[:10]
            for path in PAGES.values():
                self.assertIn(f"/assets/{name}?v={digest}", path.read_text(encoding="utf-8"))

    def test_spanish_strings_are_translated(self):
        sys.path.insert(0, str(ROOT / "bin"))
        try:
            import build_site
        finally:
            sys.path.pop(0)
        same_on_purpose = {"x_names", "star"}  # "Star" is GitHub's own button label
        untranslated = [k for k, v in build_site.ES.items()
                        if k not in same_on_purpose and v == build_site.EN[k]]
        self.assertEqual(untranslated, [])
        attribute_keys = ("title", "description", "copy_label", "star_label", "group", "term_label",
                          "c_doc_label", "home", "footer_label", "copied_status", "copied", "works")
        for strings in (build_site.EN, build_site.ES):
            for key in attribute_keys:
                self.assertNotRegex(strings[key], r'[<>"&]', key)

    def test_transfer_size_stays_under_100_kb(self):
        shared = [SITE / "assets" / "site.css", SITE / "assets" / "site.js", SITE / "favicon.svg"]
        fonts = list((SITE / "assets" / "fonts").glob("*.woff2"))
        for path in PAGES.values():
            total = sum(len(gzip.compress(p.read_bytes(), 9)) for p in [path] + shared)
            total += sum(p.stat().st_size for p in fonts)
            self.assertLess(total, 100_000, path)

    def test_install_script(self):
        script = SITE / "install.sh"
        self.assertEqual(subprocess.run(["sh", "-n", str(script)]).returncode, 0)
        text = script.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("#!/bin/sh\n"))
        self.assertIn('"$uv" tool install --upgrade pcdd', text)
        self.assertRegex(text, re.compile(r"^main \"\$@\"\n\Z", re.M))

    def test_install_script_runs_on_linux_in_ci(self):
        workflow = (ROOT / ".github" / "workflows" / "install.yml").read_text(encoding="utf-8")
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("ubuntu-24.04-arm", workflow)
        self.assertIn("sh site/install.sh", workflow)
        self.assertIn('HOME="$(mktemp -d)"', workflow)  # starts without uv or pcdd
        self.assertIn("pcdd\" --lang en doctor", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("secrets.", workflow)
        for line in workflow.splitlines():
            if "uses:" in line:
                self.assertRegex(line, r"@[0-9a-f]{40} # v", line)

    def test_install_alternatives_do_not_break_inside_a_command(self):
        css = (SITE / "assets" / "site.css").read_text(encoding="utf-8")
        self.assertIn(".alt span{white-space:nowrap}", css)
        for path in PAGES.values():
            html = path.read_text(encoding="utf-8")
            self.assertIn("<span>npx @pcdd-dev/cli</span>", html)
            self.assertIn("<span>uv tool install pcdd</span>", html)

    def test_search_and_sharing_metadata(self):
        for lang, path in PAGES.items():
            parsed = outline(path)
            self.assertEqual(len(parsed.structured), 1)
            data = json.loads(parsed.structured[0])
            self.assertEqual(data["@type"], "SoftwareApplication")
            self.assertEqual(data["inLanguage"], lang)
            html = path.read_text(encoding="utf-8")
            self.assertIn('<meta property="og:image" content="https://pcdd.dev/og.png">', html)
            self.assertIn('<meta name="twitter:card" content="summary_large_image">', html)
        width, height = struct.unpack(">II", (SITE / "og.png").read_bytes()[16:24])
        self.assertEqual((width, height), (1200, 630))

    def test_crawler_files(self):
        robots = (SITE / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://pcdd.dev/sitemap.xml", robots)
        sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("<loc>https://pcdd.dev/</loc>", sitemap)
        self.assertIn("<loc>https://pcdd.dev/es/</loc>", sitemap)
        not_found = (SITE / "404.html").read_text(encoding="utf-8")
        self.assertIn('<meta name="robots" content="noindex">', not_found)
        self.assertEqual(outline(SITE / "404.html").inline_scripts, [])
        self.assertTrue((SITE / "llms.txt").read_text(encoding="utf-8").startswith("# PCDD\n\n> "))

    def test_star_count_is_read_from_the_same_origin(self):
        script = (SITE / "assets" / "site.js").read_text(encoding="utf-8")
        self.assertIn("fetch('/api/stars')", script)
        self.assertNotIn("api.github.com", script)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_stars_function_never_fails_and_caches(self):
        harness = r"""
const mod = await import(process.argv[1]);
const store = new Map();
globalThis.caches = { default: {
  match: async (req) => store.get(req.url),
  put: async (req, res) => { store.set(req.url, res); },
} };
const run = async (upstream) => {
  store.clear();
  let calls = 0;
  globalThis.fetch = async (url, init) => { calls += 1; return upstream(url, init); };
  const pending = [];
  const ctx = { request: new Request('https://pcdd.dev/api/stars?x=1'), env: {},
                waitUntil: (p) => pending.push(p) };
  const first = await mod.onRequestGet(ctx);
  await Promise.all(pending);
  const second = await mod.onRequestGet(ctx);
  return { status: first.status, body: await first.json(), cache: first.headers.get('cache-control'),
           type: first.headers.get('content-type'), calls, cached: (await second.json()).stars };
};
const ok = await run(async (url, init) => new Response(JSON.stringify({ stargazers_count: 42 }),
  { status: url.startsWith('https://api.github.com/repos/aledepaoligampel/pcdd') && init.headers['User-Agent'] ? 200 : 500 }));
const limited = await run(async () => new Response('{}', { status: 403 }));
const down = await run(async () => { throw new Error('offline'); });
console.log(JSON.stringify({ ok, limited, down }));
"""
        source = ROOT / "functions" / "api" / "stars.js"
        result = subprocess.run(["node", "--input-type=module", "-e", harness, source.as_uri()],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(out["ok"]["status"], 200)
        self.assertEqual(out["ok"]["body"], {"stars": 42})
        self.assertEqual(out["ok"]["calls"], 1)  # the second request is served from the cache
        self.assertEqual(out["ok"]["cached"], 42)
        self.assertIn("max-age=3600", out["ok"]["cache"])
        self.assertTrue(out["ok"]["type"].startswith("application/json"))
        for case in ("limited", "down"):
            self.assertEqual(out[case]["status"], 200, case)
            self.assertEqual(out[case]["body"], {"stars": None}, case)
            self.assertIn("max-age=300", out[case]["cache"], case)

    def test_context7_configuration(self):
        config = json.loads((ROOT / "context7.json").read_text(encoding="utf-8"))
        self.assertLessEqual(len(config["projectTitle"]), 100)
        self.assertLessEqual(len(config["description"]), 500)


if __name__ == "__main__":
    unittest.main()
