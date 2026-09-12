from pathlib import Path


THEME_DIR = Path(__file__).parents[1] / "wordpress" / "astra-child"


def test_heavy_widget_assets_are_scoped_to_widget_pages():
    php = (THEME_DIR / "ask-mirror-talk.php").read_text()

    assert "has_shortcode((string) $post->post_content, 'ask_mirror_talk')" in php
    assert "is_page('ask-mirror-talk')" in php
    assert "if (!$has_widget_shortcode && !$is_widget_page)" in php
    assert "ask-mirror-talk-redesign.css" in php
    assert "array('ask-mirror-talk', 'ask-mirror-talk-premium')" in php


def test_blocked_notifications_are_only_explained_on_request():
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    denied_branch = js.split("if (Notification.permission === 'denied')", 1)[1][:500]
    assert "if (!explicitlyRequested) return;" in denied_branch


def test_onboarding_prefill_updates_dependent_interface():
    js = (THEME_DIR / "ask-mirror-talk-premium.js").read_text()

    assert "input.dispatchEvent(new Event('input', { bubbles: true }))" in js
    assert "questions are sent anonymously to create an answer" in js


def test_singular_citation_copy_and_question_coach_are_grammatical():
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    assert "support${count === 1 ? 's' : ''} this reflection" in js
    assert "What is one practical first step to ${howToAction}?" in js
    assert "What is the first step I should take with ${topic}?" not in js


def test_audio_preview_avoids_eager_full_download():
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    assert "previewAudio.preload = 'metadata'" in js


def test_redesign_is_scoped_and_accessibility_aware():
    css = (THEME_DIR / "ask-mirror-talk-redesign.css").read_text()

    assert css.count(".ask-mirror-talk") >= 40
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "@media (prefers-contrast: more)" in css
    assert "button:focus-visible" in css


def test_light_premium_surfaces_have_explicit_readable_text_colors():
    css = (THEME_DIR / "ask-mirror-talk-redesign.css").read_text()
    fixture = (Path(__file__).parent / "fixtures" / "premium_redesign_preview.html").read_text()

    assert ".ask-mirror-talk .amt-stats-prompt-text" in css
    assert "color: #2b2433" in css
    assert ".ask-mirror-talk .amt-stats-prompt-subtext" in css
    assert "color: #62596b" in css
    assert ".ask-mirror-talk .amt-stats-prompt-kicker" in css
    assert "color: #6b536f" in css
    assert ".ask-mirror-talk .amt-heading-controls" in css
    assert "background: rgba(24, 15, 31, 0.34)" in css
    assert ".ask-mirror-talk #ask-mirror-talk-input::placeholder" in css
    assert "color: #706777" in css
    assert ".ask-mirror-talk .amt-form-note" in css
    assert ".ask-mirror-talk .amt-workflow-label" in css
    assert "font-size: 11px" in css
    assert "amt-badge-count" in fixture
    assert "amt-stats-prompt-text" in fixture
