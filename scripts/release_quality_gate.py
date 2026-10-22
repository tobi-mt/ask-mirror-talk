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
    required = ["header.php", "footer.php", "single.php", "page.php", "archive.php", "404.php", "listen.php", "listen-everywhere.js", "link-hub.php", "link-hub.css", "link-hub.js", "inc/link-hub.php", "inc/listen-everywhere.php", "inc/knowledge-quality.php", "inc/intelligence-pipeline.php", "inc/editorial-composer.php", "inc/rss-editorial-ingestion.php", "inc/editorial-presentations.php", "inc/page-one-growth.php"]
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
        "resilient intelligence pipeline loaded": "inc/intelligence-pipeline.php" in functions,
        "editorial composer loaded": "inc/editorial-composer.php" in functions,
        "citation brief rendered": "mirrortalk_render_citation_brief" in single,
        "listen route loaded": "inc/listen-everywhere.php" in functions,
        "listen route canonical": "mirror_listen" in (THEME / "inc" / "intelligence-seo.php").read_text(),
        "owned link hub loaded": "inc/link-hub.php" in functions,
        "owned link hub route": "mirror_links" in (THEME / "inc" / "link-hub.php").read_text(),
        "owned link hub canonical": "mirror_links" in (THEME / "inc" / "intelligence-seo.php").read_text(),
        "owned link hub measured": "link_hub_action" in (THEME / "inc" / "intelligence-dashboard.php").read_text(),
        "unverified platforms hidden": "'enabled'=>0" in (THEME / "inc" / "listen-everywhere.php").read_text(),
        "pipeline stages isolated": all(marker in (THEME / "inc" / "intelligence-pipeline.php").read_text() for marker in ("intelligence_quality_stage", "intelligence_recommendations_stage", "intelligence_knowledge_stage")),
        "pipeline watchdog enabled": "mirrortalk_pipeline_watchdog" in (THEME / "inc" / "intelligence-pipeline.php").read_text(),
        "RSS editorial pipeline loaded": "inc/rss-editorial-ingestion.php" in functions,
        "RSS drafts stay unpublished": "'post_status'=>'draft'" in (THEME / "inc" / "rss-editorial-ingestion.php").read_text(),
        "RSS background batches bounded": "MIRRORTALK_RSS_INGESTION_BATCH" in (THEME / "inc" / "rss-editorial-ingestion.php").read_text(),
        "RSS source evidence protected": "editorial-review-required" in (THEME / "inc" / "rss-editorial-ingestion.php").read_text(),
        "RSS workflow runs automatically": "mirrortalk_rss_ingestion_daily" in (THEME / "inc" / "rss-editorial-ingestion.php").read_text(),
        "RSS publication has quality gate": "mirrortalk_rss_ingestion_publish_if_ready" in (THEME / "inc" / "rss-editorial-ingestion.php").read_text(),
        "editorial presentations loaded": "inc/editorial-presentations.php" in functions,
        "content-led archive profiles": "mirrortalk_editorial_profile" in (THEME / "inc" / "editorial-presentations.php").read_text(),
        "cinematic major-conversation gate": "mirrortalk_is_major_conversation" in (THEME / "inc" / "editorial-presentations.php").read_text(),
        "legacy semantic formatter loaded": "inc/content-normalizer.php" in functions,
        "semantic headings repaired": "mirrortalk_semantic_heading_candidate" in (THEME / "inc" / "content-normalizer.php").read_text(),
        "semantic lists repaired": "mirrortalk_semantic_repair_paragraph_runs" in (THEME / "inc" / "content-normalizer.php").read_text(),
        "semantic chapters accessible": "mt-semantic-chapters" in css and "Episode chapters" in (THEME / "inc" / "content-normalizer.php").read_text(),
        "semantic repair runs before composer": "'mirrortalk_normalize_editorial_content', 20" in (THEME / "inc" / "content-normalizer.php").read_text(),
        "plain URLs are safely linkified": all(marker in (THEME / "inc" / "content-normalizer.php").read_text() for marker in ("mirrortalk_autolink_plain_urls", "wp_http_validate_url", "noopener noreferrer external", "mirrortalk_autolink_is_known_broken")),
        "URL whitespace entities stay outside links": "(?:nbsp|#160|#x0*a0)" in (THEME / "inc" / "content-normalizer.php").read_text(),
        "automatic links are reversible": "'automatic_links'" in (THEME / "inc" / "editorial-composer-v2.php").read_text(),
        "page-one growth loaded": "inc/page-one-growth.php" in functions,
        "page-one opportunities prioritize positions 4-20": "$position >= 4 && $position <= 20" in (THEME / "inc" / "page-one-growth.php").read_text(),
        "page-one changes are reversible": "mirrortalk_page_one_restore" in (THEME / "inc" / "page-one-growth.php").read_text(),
        "cannibalization stays review-led": "editorial_review" in (THEME / "inc" / "page-one-growth.php").read_text(),
        "broken links require GET confirmation": "mirrortalk_seo_confirm_link" in (THEME / "inc" / "seo-platform.php").read_text(),
        "broken links are cleaned per source": "md5($post->ID . '|' . $url)" in (THEME / "inc" / "seo-platform.php").read_text(),
        "broken-link cleanup is bounded": "mirrortalk_seo_cleanup_broken_links_continue" in (THEME / "inc" / "seo-platform.php").read_text(),
    }
    failures.extend(label for label, passed in expectations.items() if not passed)
    return failures


def remote_checks(base):
    failures = []
    for path in ("/", "/listen/", "/listen-connect/", "/podcast-episodes/", "/blog/", "/ask-mirror-talk/", "/contact/", "/llms.txt", "/mirror-talk-sitemap/"):
        url = base.rstrip("/") + path
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "MirrorTalkReleaseGate/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read(2_000_000).decode("utf-8", "replace")
                if response.status != 200:
                    failures.append(f"{path}: HTTP {response.status}")
                if path in ("/", "/listen/", "/listen-connect/", "/podcast-episodes/", "/blog/", "/ask-mirror-talk/", "/contact/") and not re.search(r"<main\b", body, re.I):
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
