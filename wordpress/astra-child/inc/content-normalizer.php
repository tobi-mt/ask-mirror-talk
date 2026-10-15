<?php
/**
 * Non-destructive presentation normalization for legacy editorial content.
 * Stored post content is never rewritten. Authors can opt out per document by
 * including: <!-- mirror-talk:preserve-format -->
 */
if (!defined('ABSPATH')) exit;

function mirrortalk_normalize_editorial_content($content) {
    if (is_admin() || !is_singular() || !in_the_loop() || !is_main_query()) return $content;
    if (strpos((string) $content, 'mirror-talk:preserve-format') !== false) return $content;

    // A post already has its one document H1 in single.php. Old articles often
    // pasted another H1 into the body; render it as H2 without altering storage.
    if (is_singular('post')) {
        $content = preg_replace('/<h1(\s[^>]*)?>/i', '<h2$1>', (string) $content);
        $content = preg_replace('/<\/h1\s*>/i', '</h2>', (string) $content);
    }

    // Repair skipped heading levels at render time. The template/page H1 is
    // level one; editorial content may move only one level deeper at a time.
    $last_heading = 1;
    $content = preg_replace_callback('/<h([2-6])(\s[^>]*)?>(.*?)<\/h\1\s*>/is', function ($match) use (&$last_heading) {
        $requested = (int) $match[1];
        $level = min($requested, $last_heading + 1);
        $level = max(2, $level);
        $last_heading = $level;
        return '<h' . $level . ($match[2] ?? '') . '>' . $match[3] . '</h' . $level . '>';
    }, (string) $content);

    // Remove only truly empty legacy paragraphs. Paragraphs containing media,
    // anchors, shortcodes or non-breaking content remain untouched.
    $content = preg_replace('/<p(?:\s[^>]*)?>\s*(?:&nbsp;|&#160;|\x{00a0})?\s*<\/p>/iu', '', (string) $content);

    // Legacy provider embeds frequently omit a title. Supply a truthful,
    // generic accessible name at render time without rewriting stored content
    // or guessing the identity of a speaker, episode or video.
    $content = preg_replace_callback('/<iframe\b(?![^>]*\btitle=)([^>]*)>/i', function ($match) {
        return '<iframe title="' . esc_attr__('Embedded media', 'astra-child') . '"' . $match[1] . '>';
    }, (string) $content);
    return $content;
}
add_filter('the_content', 'mirrortalk_normalize_editorial_content', 30);
