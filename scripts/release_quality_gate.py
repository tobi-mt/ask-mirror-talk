#!/usr/bin/env python3
"""Deterministic release gate for the Mirror Talk WordPress theme."""
from pathlib import Path
import argparse
import json
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress" / "astra-child"


def local_checks():
    failures = []
    required = ["header.php", "footer.php", "single.php", "page.php", "archive.php", "404.php", "inc/knowledge-quality.php", "inc/editorial-composer.php"]
    for name in required:
        if not (THEME / name).exists():
            failures.append(f"missing {name}")
    css = (THEME / "mirror-talk-site.css").read_text()
    single = (THEME / "single.php").read_text()
    functions = (THEME / "functions.php").read_text()
    expectations = {
        "visible keyboard focus": ":focus-visible" in css,
        "reduced motion": "prefers-reduced-motion" in css,
        "mobile reflow": "@media (max-width:" in css,
        "44px controls": "min-block-size: 44px" in css,
        "semantic main": '<main id="primary"' in single,
        "knowledge engine loaded": "inc/knowledge-quality.php" in functions,
        "editorial composer loaded": "inc/editorial-composer.php" in functions,
        "citation brief rendered": "mirrortalk_render_citation_brief" in single,
    }
    failures.extend(label for label, passed in expectations.items() if not passed)
    return failures


def remote_checks(base):
    failures = []
    for path in ("/", "/blog/", "/ask-mirror-talk/", "/contact/", "/llms.txt", "/mirror-talk-sitemap/"):
        url = base.rstrip("/") + path
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "MirrorTalkReleaseGate/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read(2_000_000).decode("utf-8", "replace")
                if response.status != 200:
                    failures.append(f"{path}: HTTP {response.status}")
                if path in ("/", "/blog/", "/ask-mirror-talk/", "/contact/") and not re.search(r"<main\b", body, re.I):
                    failures.append(f"{path}: no main landmark")
        except Exception as error:
            failures.append(f"{path}: {error}")
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Optional staging or production origin")
    args = parser.parse_args()
    failures = local_checks() + (remote_checks(args.url) if args.url else [])
    print(json.dumps({"passed": not failures, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
