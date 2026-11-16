import base64
import gzip
import hashlib
import re
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
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        self.attrs.append((tag, a))
        if "id" in a:
            self.ids.append(a["id"])
        self._in_script = tag == "script" and "src" not in a

    def handle_endtag(self, tag):
        self._in_script = False

    def handle_data(self, data):
        if self._in_script and data.strip():
            self.inline_scripts.append(data)


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
        self.assertIn("script-src 'self';", headers)
        self.assertIn("style-src 'self';", headers)
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
        same_on_purpose = {"x_names"}
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


if __name__ == "__main__":
    unittest.main()
