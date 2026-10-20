<?php
/**
 * Non-destructive presentation normalization for legacy editorial content.
 * Stored post content is never rewritten. Authors can opt out per document by
 * including: <!-- mirror-talk:preserve-format -->
 */
if (!defined('ABSPATH')) exit;

/** Return true only for the deliberately narrow paragraph shapes we repair. */
function mirrortalk_semantic_paragraph_attrs_are_safe($attrs) {
    $attrs = trim((string) $attrs);
    if ($attrs === '') return true;
    return (bool) preg_match('/^class=(?:"|\')wp-block-paragraph(?:\s+[^"\']*)?(?:"|\')$/i', $attrs);
}

function mirrortalk_semantic_heading_candidate($html) {
    if (preg_match('/<(?:a|img|audio|video|iframe|code|time)\b/i', $html)) return false;
    $label = trim(preg_replace('/\s+/u', ' ', wp_strip_all_tags($html)));
    $length = function_exists('mirrortalk_composer_strlen') ? mirrortalk_composer_strlen($label) : strlen($label);
    if ($label === '' || $length > 90) return false;
    $words = preg_split('/\s+/u', $label, -1, PREG_SPLIT_NO_EMPTY);
    if (count($words) < 2 || count($words) > 12 || preg_match('/[.!?,;:]$/u', $label)) return false;
    if (preg_match('/^(?:click here|read more|learn more|subscribe|share this|listen now|watch now|follow us|support us)$/iu', $label)) return false;
    return true;
}

/** Seconds and an ISO-8601 duration for a verified chapter timestamp. */
function mirrortalk_semantic_timestamp($stamp) {
    $parts = array_map('intval', explode(':', (string) $stamp));
    if (count($parts) === 2) $seconds = $parts[0] * 60 + $parts[1];
    elseif (count($parts) === 3) $seconds = $parts[0] * 3600 + $parts[1] * 60 + $parts[2];
    else return array(0, '');
    if (end($parts) > 59 || (count($parts) === 3 && $parts[1] > 59)) return array(0, '');
    $duration = 'PT' . ($seconds >= 3600 ? floor($seconds / 3600) . 'H' : '') . (floor(($seconds % 3600) / 60)) . 'M' . ($seconds % 60) . 'S';
    return array($seconds, $duration);
}

/** Classify only high-confidence, one-paragraph list/chapter items. */
function mirrortalk_semantic_item($inner) {
    $inner = trim((string) $inner);
    if ($inner === '' || preg_match('/<(?:figure|iframe|audio|video|blockquote|pre|code|table)\b/i', $inner)) return null;
    if (preg_match('/^(\d{1,2}:\d{2}(?::\d{2})?)\s*(?:[-–—|]\s*)?(.+)$/us', $inner, $match)) {
        list($seconds, $duration) = mirrortalk_semantic_timestamp($match[1]);
        $label = trim($match[2]);
        if ($duration && $label !== '') return array('type'=>'chapter', 'body'=>$label, 'stamp'=>$match[1], 'seconds'=>$seconds, 'duration'=>$duration);
    }
    if (preg_match('/^[\x{2022}\x{25CF}\x{25AA}\x{25E6}\x{2023}\x{2043}]\s+(.+)$/us', $inner, $match)) return array('type'=>'bullet', 'body'=>trim($match[1]));
    if (preg_match('/^[-*]\s+(.+)$/us', $inner, $match)) return array('type'=>'bullet', 'body'=>trim($match[1]));
    if (preg_match('/^\d{1,2}[.)]\s+(.+)$/us', $inner, $match)) return array('type'=>'number', 'body'=>trim($match[1]));
    return null;
}

/**
 * Repair consecutive legacy paragraph-items without changing their words.
 * Runs need at least two matching items, which prevents prose false positives.
 */
function mirrortalk_semantic_repair_paragraph_runs($content) {
    if (!preg_match_all('/<p(?P<attrs>\s[^>]*)?>(?P<body>.*?)<\/p>/is', (string) $content, $matches, PREG_SET_ORDER | PREG_OFFSET_CAPTURE)) return $content;
    $output = '';
    $cursor = 0;
    $run = array();
    $run_type = '';
    $run_start = 0;
    $flush = function () use (&$output, &$run, &$run_type, &$run_start, $content) {
        if (!$run) return;
        if (count($run) < 2) {
            foreach ($run as $entry) $output .= $entry['html'];
        } elseif ($run_type === 'chapter') {
            $output .= '<section class="mt-semantic-chapters" aria-label="' . esc_attr__('Episode chapters', 'astra-child') . '"><ol>';
            foreach ($run as $entry) {
                $item = $entry['item'];
                $output .= '<li data-start="' . esc_attr($item['seconds']) . '"><time datetime="' . esc_attr($item['duration']) . '">' . esc_html($item['stamp']) . '</time><span>' . wp_kses_post($item['body']) . '</span></li>';
            }
            $output .= '</ol></section>';
        } else {
            $tag = $run_type === 'number' ? 'ol' : 'ul';
            $output .= '<' . $tag . ' class="mt-semantic-list">';
            foreach ($run as $entry) $output .= '<li>' . wp_kses_post($entry['item']['body']) . '</li>';
            $output .= '</' . $tag . '>';
        }
        $run = array(); $run_type = ''; $run_start = 0;
    };
    foreach ($matches as $match) {
        $html = $match[0][0]; $start = $match[0][1];
        $between = substr($content, $cursor, $start - $cursor);
        $attrs = trim((string) ($match['attrs'][0] ?? ''));
        $item = mirrortalk_semantic_paragraph_attrs_are_safe($attrs) ? mirrortalk_semantic_item($match['body'][0]) : null;
        $only_spacing = trim(preg_replace('/<!--.*?-->/s', '', $between)) === '';
        if (!$item || ($run && (!$only_spacing || $item['type'] !== $run_type))) {
            $flush();
            $output .= $between;
        } elseif (!$run) {
            $output .= $between;
            $run_start = $start;
        }
        if ($item) {
            if (!$run) $run_type = $item['type'];
            $run[] = array('html'=>$html, 'item'=>$item);
        } else {
            $output .= $html;
        }
        $cursor = $start + strlen($html);
    }
    $flush();
    return $output . substr($content, $cursor);
}

function mirrortalk_semantic_repair_content($content) {
    // Elementor and Classic Editor occasionally stored a complete numbered
    // point (label plus several prose sentences) inside an H3/H4. That creates
    // an unusable document outline and enormous all-caps paragraphs. Repair
    // only headings inside list items that are unmistakably prose-length.
    $content = preg_replace_callback('/<li(?P<li_attrs>\s[^>]*)?>(?P<before>\s*)<h(?P<level>[2-6])(?P<h_attrs>\s[^>]*)?>(?P<body>.*?)<\/h(?P=level)\s*>(?P<after>.*?)<\/li>/is', function ($match) {
        $plain = trim(preg_replace('/\s+/u', ' ', wp_strip_all_tags($match['body'])));
        $words = preg_split('/\s+/u', $plain, -1, PREG_SPLIT_NO_EMPTY);
        $length = function_exists('mirrortalk_composer_strlen') ? mirrortalk_composer_strlen($plain) : strlen($plain);
        if ($length < 150 && count($words) < 24) return $match[0];

        $body = wp_kses_post($match['body']);
        if (preg_match('/^(.{2,100}?):\s*(.+)$/us', $body, $parts)) {
            $label = trim(wp_strip_all_tags($parts[1]));
            $label_words = preg_split('/\s+/u', $label, -1, PREG_SPLIT_NO_EMPTY);
            if (count($label_words) <= 12) $body = '<strong>' . wp_kses_post($parts[1]) . ':</strong> ' . wp_kses_post($parts[2]);
        }
        return '<li' . ($match['li_attrs'] ?? '') . '>' . ($match['before'] ?? '') . '<p class="mt-semantic-list-prose">' . $body . '</p>' . ($match['after'] ?? '') . '</li>';
    }, (string) $content);

    // Bold-only legacy paragraphs are author-created section labels. Restrict
    // conversion to plain Gutenberg paragraphs and high-confidence labels.
    $content = preg_replace_callback('/<p(?P<attrs>\s[^>]*)?>\s*<(?P<tag>strong|b)>(?P<label>.*?)<\/(?P=tag)>\s*<\/p>/is', function ($match) {
        $attrs = trim((string) ($match['attrs'] ?? ''));
        if (!mirrortalk_semantic_paragraph_attrs_are_safe($attrs) || !mirrortalk_semantic_heading_candidate($match['label'])) return $match[0];
        return '<h2 class="mt-semantic-heading">' . wp_kses_post($match['label']) . '</h2>';
    }, (string) $content);

    // Some Classic Editor and pasted documents store an entire list as one
    // paragraph separated by BR elements. Convert only when every non-empty
    // line is the same recognized item type and there are at least two lines.
    $content = preg_replace_callback('/<p(?P<attrs>\s[^>]*)?>(?P<body>(?:(?!<\/p>).)*?<br\s*\/?> (?:(?!<\/p>).)*)<\/p>/isx', function ($match) {
        $attrs = trim((string) ($match['attrs'] ?? ''));
        if (!mirrortalk_semantic_paragraph_attrs_are_safe($attrs)) return $match[0];
        $lines = array_values(array_filter(array_map('trim', preg_split('/<br\s*\/?>/i', $match['body']))));
        if (count($lines) < 2) return $match[0];
        $items = array_map('mirrortalk_semantic_item', $lines);
        if (in_array(null, $items, true)) return $match[0];
        $types = array_values(array_unique(array_map(function ($item) { return $item['type']; }, $items)));
        if (count($types) !== 1) return $match[0];
        if ($types[0] === 'chapter') {
            $html = '<section class="mt-semantic-chapters" aria-label="' . esc_attr__('Episode chapters', 'astra-child') . '"><ol>';
            foreach ($items as $item) $html .= '<li data-start="' . esc_attr($item['seconds']) . '"><time datetime="' . esc_attr($item['duration']) . '">' . esc_html($item['stamp']) . '</time><span>' . wp_kses_post($item['body']) . '</span></li>';
            return $html . '</ol></section>';
        }
        $tag = $types[0] === 'number' ? 'ol' : 'ul';
        $html = '<' . $tag . ' class="mt-semantic-list">';
        foreach ($items as $item) $html .= '<li>' . wp_kses_post($item['body']) . '</li>';
        return $html . '</' . $tag . '>';
    }, $content);
    return mirrortalk_semantic_repair_paragraph_runs($content);
}

/** Do not promote a URL the crawler has already confirmed as definitively broken. */
function mirrortalk_autolink_is_known_broken($url) {
    static $broken = null;
    if ($broken === null) {
        $broken = array();
        foreach ((array) get_option('mirrortalk_link_health', array()) as $row) {
            if (!is_array($row) || empty($row['url'])) continue;
            $state = function_exists('mirrortalk_seo_link_state') ? mirrortalk_seo_link_state($row) : '';
            if ($state === 'broken') $broken[untrailingslashit(strtolower((string) $row['url']))] = true;
        }
    }
    return isset($broken[untrailingslashit(strtolower((string) $url))]);
}

/** Remove sentence punctuation captured after a plain-text URL. */
function mirrortalk_autolink_split_suffix($candidate) {
    $candidate = (string) $candidate;
    $suffix = '';
    // Non-breaking-space entities are frequently pasted immediately after a
    // URL by the Classic Editor. They are document spacing, never URL data.
    if (preg_match('/(&(?:nbsp|#160|#x0*a0);?)$/iu', $candidate, $entity)) {
        $suffix = $entity[1];
        $candidate = substr($candidate, 0, -strlen($entity[1]));
    }
    while ($candidate !== '' && preg_match('/[.,;:!?\]\}”’\'"]$/u', $candidate, $match)) {
        $suffix = $match[0] . $suffix;
        $candidate = preg_replace('/[.,;:!?\]\}”’\'"]$/u', '', $candidate, 1);
    }
    while (substr($candidate, -1) === ')' && substr_count($candidate, ')') > substr_count($candidate, '(')) {
        $suffix = ')' . $suffix;
        $candidate = substr($candidate, 0, -1);
    }
    return array($candidate, $suffix);
}

/**
 * Link valid public web addresses in text nodes only. Existing anchors and
 * executable/preformatted content are protected, and no HTTP request is made
 * during page rendering. Link health remains the scheduled crawler's job.
 */
function mirrortalk_autolink_plain_urls($content) {
    if (stripos((string) $content, 'http') === false && stripos((string) $content, 'www.') === false && !preg_match('/\b[a-z0-9-]+\.(?:[a-z]{2,24}|xn--[a-z0-9-]{2,59})\b/i', (string) $content)) return $content;
    $tokens = wp_html_split((string) $content);
    $protected = 0;
    $tags = array('a','code','pre','script','style','textarea','button','svg');
    foreach ($tokens as &$token) {
        if ($token === '') continue;
        if ($token[0] === '<') {
            if (preg_match('/^<\s*\/\s*([a-z0-9:-]+)/i', $token, $match) && in_array(strtolower($match[1]), $tags, true)) $protected = max(0, $protected - 1);
            elseif (preg_match('/^<\s*([a-z0-9:-]+)/i', $token, $match) && in_array(strtolower($match[1]), $tags, true) && !preg_match('/\/\s*>$/', $token)) $protected++;
            continue;
        }
        if ($protected) continue;
        $token = preg_replace_callback('~(?<![@\p{L}\p{N}_])((?:https?://|www\.)[^\s<>]+|(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,24}|xn--[a-z0-9-]{2,59})(?:/[^\s<>]*)?)~iu', function ($match) {
            list($display, $suffix) = mirrortalk_autolink_split_suffix($match[1]);
            $decoded = html_entity_decode($display, ENT_QUOTES | ENT_HTML5, 'UTF-8');
            $url = preg_match('~^https?://~i', $decoded) ? $decoded : 'https://' . $decoded;
            $valid = wp_http_validate_url($url);
            if (!$valid || mirrortalk_autolink_is_known_broken($valid)) return $match[0];
            $label = sprintf(__('%s (opens in a new tab)', 'astra-child'), wp_strip_all_tags($display));
            return '<a class="mt-auto-link" href="' . esc_url($valid) . '" target="_blank" rel="noopener noreferrer external" aria-label="' . esc_attr($label) . '">' . esc_html($display) . '</a>' . $suffix;
        }, $token);
    }
    unset($token);
    return implode('', $tokens);
}

/** Make every existing external editorial anchor visibly and safely actionable. */
function mirrortalk_prepare_existing_editorial_links($content){
    $home_host=strtolower((string)wp_parse_url(home_url('/'),PHP_URL_HOST));
    return preg_replace_callback('/<a\b([^>]*)\bhref=(?:"([^"]*)"|\'([^\']*)\')([^>]*)>/i',function($match)use($home_host){
        $url=html_entity_decode((string)($match[2]!==''?$match[2]:$match[3]),ENT_QUOTES|ENT_HTML5,'UTF-8');$host=strtolower((string)wp_parse_url($url,PHP_URL_HOST));$external=$host&&$host!==$home_host;
        $attrs=trim((string)$match[1].' '.(string)$match[4]);if(!preg_match('/\bclass=/i',$attrs))$attrs.=' class="mt-editorial-link"';else$attrs=preg_replace('/\bclass=("|\')([^"\']*)(\1)/i','class=$1$2 mt-editorial-link$3',$attrs,1);
        if($external&&!preg_match('/\btarget=/i',$attrs))$attrs.=' target="_blank"';if($external){if(preg_match('/\brel=("|\')([^"\']*)(\1)/i',$attrs))$attrs=preg_replace('/\brel=("|\')([^"\']*)(\1)/i','rel=$1$2 noopener noreferrer external$3',$attrs,1);else$attrs.=' rel="noopener noreferrer external"';}
        return '<a '.trim($attrs).' href="'.esc_url($url).'">';
    },(string)$content);
}

function mirrortalk_normalize_editorial_content($content) {
    if (is_admin() || !is_singular() || !in_the_loop() || !is_main_query()) return $content;
    if (strpos((string) $content, 'mirror-talk:preserve-format') !== false) return $content;

    $post_id = get_the_ID();
    $decisions = function_exists('mirrortalk_composer_v2_decisions') ? mirrortalk_composer_v2_decisions($post_id) : array();
    if (!isset($decisions['semantic_formatting']) || !empty($decisions['semantic_formatting']['enabled'])) {
        $content = mirrortalk_semantic_repair_content($content);
    }
    if (!isset($decisions['automatic_links']) || !empty($decisions['automatic_links']['enabled'])) {
        $content = mirrortalk_autolink_plain_urls($content);
        $content = mirrortalk_prepare_existing_editorial_links($content);
    }

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
// This must precede Composer (priority 25), so its outline and section logic
// can use repaired real headings instead of adding generic replacements.
add_filter('the_content', 'mirrortalk_normalize_editorial_content', 20);
