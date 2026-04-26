#!/usr/bin/env python3
"""Render and validate Ask Mirror Talk reflection card fixtures.

This is a pre-package safety gate for the share-card renderer. It intentionally
uses the same browser/canvas path as real users instead of trying to reimplement
the layout logic in Python.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "reflection_card_fixture_runner.html"
DEFAULT_OUT_DIR = Path("/tmp/amt-reflection-card-validation")
QR_PAYLOAD = "https://mirrortalkpodcast.com/ask-mirror-talk?ref=card_qr"
PNG_SIZE = (1080, 1350)

FAMILIES = [
    "editorial",
    "editorial_serene",
    "poster",
    "spotlight",
    "minimal",
    "atmospheric",
    "gradient_immersive",
    "neon_contemplative",
    "prismatic_quote",
]

FIXTURES = [
    "faith_fragment",
    "faith_complete",
    "gratitude_prompt_fragment",
    "gratitude_complete",
    "healing_commitments_fragment",
    "healing_commitments_complete",
    "relationships_medium",
    "leadership_long",
    "selfworth_medium",
    "courage_short",
    "inner_peace_empty",
    "saved_reflection_long_note",
    "journal_reflection_long_note",
]

META_PROMPT_PATTERNS = [
    "what likely stayed with you",
    "what stayed with me most from today's reflection",
    "what stayed with me most from today\u2019s reflection",
    "today's reflection on",
    "today\u2019s reflection on",
]

DANGLING_ENDINGS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "because",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "or",
    "that",
    "the",
    "to",
    "with",
    "without",
    "your",
}

SOURCE_GROUNDED_PREFIXES = ("saved_", "journal_")

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "already",
    "before",
    "being",
    "between",
    "could",
    "does",
    "doing",
    "down",
    "each",
    "even",
    "every",
    "feels",
    "from",
    "have",
    "into",
    "itself",
    "just",
    "like",
    "likely",
    "more",
    "most",
    "need",
    "other",
    "others",
    "perhaps",
    "really",
    "should",
    "some",
    "still",
    "that",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "today",
    "toward",
    "under",
    "when",
    "where",
    "while",
    "with",
    "without",
    "worth",
    "would",
    "your",
    "youre",
    "youve",
    "yourself",
}


@dataclass
class RenderedCase:
    fixture: str
    family: str
    png_path: Path
    debug: dict[str, Any]


@dataclass
class CaseFailure:
    fixture: str
    family: str
    reason: str


def find_chrome(explicit: str | None = None) -> str:
    candidates = [
        explicit,
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise SystemExit(
        "Could not find Chrome. Set CHROME_PATH or pass --chrome /path/to/chrome."
    )


def parse_list(value: str | None, allowed: list[str]) -> list[str]:
    if not value or value == "all":
        return allowed[:]
    selected = [item.strip() for item in value.split(",") if item.strip()]
    unknown = sorted(set(selected) - set(allowed))
    if unknown:
        raise SystemExit(f"Unknown values: {', '.join(unknown)}")
    return selected


def build_url(fixture: str, family: str | None) -> str:
    url = RUNNER.as_uri() + f"?fixture={quote(fixture)}"
    if family:
        url += f"&family={quote(family)}"
    return url


def extract_debug_and_png(dom_path: Path, png_path: Path) -> dict[str, Any]:
    dom = dom_path.read_text(errors="ignore")
    img_match = re.search(r'src="data:image/png;base64,([^"]+)"', dom)
    if not img_match:
        raise ValueError("card image data URL missing")
    png_path.write_bytes(base64.b64decode(img_match.group(1)))

    pre_match = re.search(
        r'<pre[^>]*id="fixture-debug"[^>]*>(.*?)</pre>',
        dom,
        flags=re.S,
    )
    if not pre_match:
        raise ValueError("fixture debug JSON missing")
    debug_text = html.unescape(pre_match.group(1)).strip()
    return json.loads(debug_text)


def render_case(
    chrome: str,
    fixture: str,
    family: str | None,
    out_dir: Path,
    timeout: float,
) -> RenderedCase:
    family_label = family or "auto"
    profile = tempfile.mkdtemp(prefix="amt-card-chrome.")
    dom_path = out_dir / f"{fixture}__{family_label}.html"
    png_path = out_dir / f"{fixture}__{family_label}.png"
    log_path = out_dir / f"{fixture}__{family_label}.log"
    dom_path.unlink(missing_ok=True)
    png_path.unlink(missing_ok=True)

    cmd = [
        chrome,
        "--headless=new",
        "--use-mock-keychain",
        "--disable-gpu",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--disable-extensions",
        "--disable-default-apps",
        "--no-service-autorun",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        f"--user-data-dir={profile}",
        "--virtual-time-budget=12000",
        "--timeout=30000",
        "--window-size=1300,1600",
        "--dump-dom",
        build_url(fixture, family),
    ]
    env = os.environ.copy()
    env["HOME"] = "/tmp"
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(ROOT),
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate(timeout=3)

    dom_path.write_text(stdout or "")
    log_path.write_text(stderr or "")

    shutil.rmtree(profile, ignore_errors=True)
    if "data:image/png;base64" not in (stdout or "") or "fixture-debug" not in (stdout or ""):
        tail = ""
        if log_path.exists():
            tail = "\n".join(log_path.read_text(errors="ignore").splitlines()[-12:])
        timeout_note = " after timeout" if timed_out else ""
        raise RuntimeError(f"Chrome did not render fixture{timeout_note}. Log tail:\n{tail}")

    debug = extract_debug_and_png(dom_path, png_path)
    return RenderedCase(fixture, family_label, png_path, debug)


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def normalise_for_compare(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def stem_term(term: str) -> str:
    value = term.lower().strip("'")
    if len(value) > 6 and value.endswith("ing"):
        value = value[:-3]
    elif len(value) > 5 and value.endswith("ed"):
        value = value[:-2]
    elif len(value) > 5 and value.endswith("es"):
        value = value[:-2]
    elif len(value) > 4 and value.endswith("s"):
        value = value[:-1]
    return value


def significant_terms(text: str) -> set[str]:
    terms = set()
    for raw in re.findall(r"[A-Za-z][A-Za-z']+", str(text or "").lower()):
        term = stem_term(raw.replace("’", "'").replace("'", ""))
        if len(term) < 4 or term in STOPWORDS:
            continue
        terms.add(term)
    return terms


def is_source_grounded(headline: str, source_text: str) -> bool:
    headline_terms = significant_terms(headline)
    source_terms = significant_terms(source_text)
    if not headline_terms or not source_terms:
        return False
    overlap = headline_terms & source_terms
    return len(overlap) >= 2 and (len(overlap) / max(1, min(len(headline_terms), len(source_terms)))) >= 0.35


def is_complete_sentence(text: str) -> bool:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(clean) < 24:
        return False
    if "..." in clean or "\u2026" in clean:
        return False
    if clean[-1] not in ".!?":
        return False
    words = re.findall(r"[A-Za-z']+", clean)
    if len(words) < 5:
        return False
    if words and words[-1].lower().strip("'") in DANGLING_ENDINGS:
        return False
    lower = clean.lower()
    if any(pattern in lower for pattern in META_PROMPT_PATTERNS):
        return False
    return True


def validate_text(
    fixture: str,
    family: str,
    label: str,
    text: str,
    failures: list[CaseFailure],
) -> None:
    if not is_complete_sentence(text):
        failures.append(CaseFailure(fixture, family, f"{label} is not a complete shareable sentence: {text!r}"))


def validate_case(case: RenderedCase) -> list[CaseFailure]:
    failures: list[CaseFailure] = []
    debug = case.debug
    rendered = debug.get("rendered") or {}
    normalized = debug.get("normalized") or {}
    footer = debug.get("footer") or {}

    try:
        if png_dimensions(case.png_path) != PNG_SIZE:
            failures.append(CaseFailure(case.fixture, case.family, f"PNG dimensions are {png_dimensions(case.png_path)}, expected {PNG_SIZE}"))
    except Exception as exc:  # noqa: BLE001 - this is a validator, keep failure readable
        failures.append(CaseFailure(case.fixture, case.family, f"PNG validation failed: {exc}"))

    if case.png_path.stat().st_size < 80_000:
        failures.append(CaseFailure(case.fixture, case.family, f"PNG looks suspiciously small: {case.png_path.stat().st_size} bytes"))

    actual_family = rendered.get("family")
    if not actual_family:
        failures.append(CaseFailure(case.fixture, case.family, "rendered family missing"))
    elif case.family != "auto" and actual_family != case.family:
        failures.append(CaseFailure(case.fixture, case.family, f"rendered family mismatch: {actual_family}"))

    headline = rendered.get("headline") or debug.get("shareHeadline") or ""
    validate_text(case.fixture, case.family, "headline", headline, failures)

    question = normalized.get("question") or ""
    if question and normalise_for_compare(question) == normalise_for_compare(headline):
        failures.append(CaseFailure(case.fixture, case.family, "headline repeats the original question"))

    if case.fixture.startswith(SOURCE_GROUNDED_PREFIXES):
        source_text = " ".join(
            str(normalized.get(key) or "")
            for key in ("answer", "excerpt", "question")
        )
        if not is_source_grounded(headline, source_text):
            failures.append(CaseFailure(case.fixture, case.family, f"headline is complete but not source-grounded: {headline!r}"))

    supporting = rendered.get("supportingExcerpt") or ""
    if rendered.get("showExcerpt") and supporting:
        validate_text(case.fixture, case.family, "supporting excerpt", supporting, failures)

    if not footer:
        failures.append(CaseFailure(case.fixture, case.family, "QR footer did not render"))
    else:
        if footer.get("label") != "Scan to reflect":
            failures.append(CaseFailure(case.fixture, case.family, f"QR footer label mismatch: {footer.get('label')!r}"))
        if footer.get("qrPayload") != QR_PAYLOAD:
            failures.append(CaseFailure(case.fixture, case.family, f"QR payload mismatch: {footer.get('qrPayload')!r}"))
        if footer.get("qrMatrixSize") != 33:
            failures.append(CaseFailure(case.fixture, case.family, f"QR matrix size mismatch: {footer.get('qrMatrixSize')!r}"))

    qr_payload = debug.get("qrPayload")
    qr_matrix = debug.get("qrMatrix") or {}
    if qr_payload != QR_PAYLOAD:
        failures.append(CaseFailure(case.fixture, case.family, f"fixture QR payload mismatch: {qr_payload!r}"))
    if qr_matrix.get("size") != 33 or qr_matrix.get("mask") not in range(8):
        failures.append(CaseFailure(case.fixture, case.family, f"fixture QR matrix invalid: {qr_matrix!r}"))

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", help="Path to Chrome/Chromium binary")
    parser.add_argument("--fixtures", default="all", help="Comma-separated fixture names, or 'all'")
    parser.add_argument("--families", default="all", help="Comma-separated family names, or 'all'")
    parser.add_argument("--include-auto", action="store_true", help="Also test the automatic family picker")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Where to write rendered PNG/HTML artifacts")
    parser.add_argument("--timeout", type=float, default=18.0, help="Seconds to wait for each fixture render")
    parser.add_argument("--keep-going", action="store_true", help="Continue rendering after failures")
    args = parser.parse_args()

    chrome = find_chrome(args.chrome)
    fixtures = parse_list(args.fixtures, FIXTURES)
    families = parse_list(args.families, FAMILIES)
    if args.include_auto:
        families = [None] + families

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total = len(fixtures) * len(families)
    failures: list[CaseFailure] = []
    rendered_count = 0

    print(f"Reflection card validation: {total} render(s)", flush=True)
    print(f"Chrome: {chrome}", flush=True)
    print(f"Artifacts: {out_dir}", flush=True)

    for fixture in fixtures:
        for family in families:
            family_label = family or "auto"
            try:
                case = render_case(chrome, fixture, family, out_dir, args.timeout)
                case_failures = validate_case(case)
                rendered_count += 1
                if case_failures:
                    failures.extend(case_failures)
                    print(f"FAIL {fixture} / {family_label}: {case_failures[0].reason}", flush=True)
                    if not args.keep_going:
                        raise SystemExit(report_failures(rendered_count, total, failures))
                else:
                    headline = (case.debug.get("rendered") or {}).get("headline", "")
                    print(f"OK   {fixture} / {family_label}: {headline}", flush=True)
            except SystemExit:
                raise
            except Exception as exc:  # noqa: BLE001 - convert tool errors into readable failures
                failures.append(CaseFailure(fixture, family_label, str(exc)))
                print(f"FAIL {fixture} / {family_label}: {exc}", flush=True)
                if not args.keep_going:
                    raise SystemExit(report_failures(rendered_count, total, failures))

    return report_failures(rendered_count, total, failures)


def report_failures(rendered_count: int, total: int, failures: list[CaseFailure]) -> int:
    print("", flush=True)
    print(f"Rendered {rendered_count}/{total} case(s)", flush=True)
    if not failures:
        print("All reflection card fixtures passed.", flush=True)
        return 0
    print(f"{len(failures)} validation failure(s):", flush=True)
    for failure in failures:
        print(f"- {failure.fixture} / {failure.family}: {failure.reason}", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
