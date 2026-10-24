<?php
/**
 * The Living Question — a reusable Question of the Day experience.
 *
 * The API is the source of truth. A deterministic local fallback ensures that
 * the card remains meaningful during a short API outage and is present in the
 * initial HTML for accessibility, resilience and crawler comprehension.
 */

if (!defined('ABSPATH')) exit;

function mirrortalk_qotd_fallbacks() {
    return array(
        array('question' => __('What would become possible if you trusted your next small step?', 'astra-child'), 'theme' => __('Purpose', 'astra-child')),
        array('question' => __('What are you carrying today that deserves a gentler response?', 'astra-child'), 'theme' => __('Self-compassion', 'astra-child')),
        array('question' => __('Where might honesty create more freedom in your life right now?', 'astra-child'), 'theme' => __('Clarity', 'astra-child')),
        array('question' => __('What boundary could protect what matters without closing your heart?', 'astra-child'), 'theme' => __('Relationships', 'astra-child')),
        array('question' => __('What is this season teaching you that comfort could not?', 'astra-child'), 'theme' => __('Growth', 'astra-child')),
        array('question' => __('What would courage look like if it did not have to look dramatic?', 'astra-child'), 'theme' => __('Courage', 'astra-child')),
        array('question' => __('What are you ready to understand rather than judge?', 'astra-child'), 'theme' => __('Healing', 'astra-child')),
        array('question' => __('Which quiet truth keeps asking for your attention?', 'astra-child'), 'theme' => __('Inner wisdom', 'astra-child')),
    );
}

function mirrortalk_get_question_of_the_day() {
    $utc_date = gmdate('Y-m-d');
    $cache_key = 'mirrortalk_qotd_' . str_replace('-', '', $utc_date);
    $cached = get_transient($cache_key);
    if (is_array($cached) && !empty($cached['question'])) return $cached;

    $response = wp_remote_get(
        'https://ask-mirror-talk-production.up.railway.app/api/question-of-the-day',
        array('timeout' => 2, 'redirection' => 1, 'headers' => array('Accept' => 'application/json'))
    );
    if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
        $payload = json_decode((string) wp_remote_retrieve_body($response), true);
        $question = sanitize_text_field((string) ($payload['question'] ?? ''));
        $theme = sanitize_text_field((string) ($payload['theme'] ?? ''));
        if ($question !== '') {
            $result = array(
                'question' => wp_html_excerpt($question, 500, ''),
                'theme' => wp_html_excerpt($theme, 80, ''),
                'date' => sanitize_text_field((string) ($payload['date'] ?? $utc_date)),
                'source' => 'api',
            );
            set_transient($cache_key, $result, DAY_IN_SECONDS + 2 * HOUR_IN_SECONDS);
            return $result;
        }
    }

    $fallbacks = mirrortalk_qotd_fallbacks();
    $fallback = $fallbacks[((int) gmdate('z')) % count($fallbacks)];
    $fallback['date'] = $utc_date;
    $fallback['source'] = 'fallback';
    set_transient($cache_key, $fallback, 30 * MINUTE_IN_SECONDS);
    return $fallback;
}

function mirrortalk_qotd_answer_url($question) {
    return add_query_arg(
        array(
            'autoask' => $question,
            'utm_source' => 'website',
            'utm_medium' => 'living_question',
            'utm_campaign' => gmdate('Y-m-d'),
        ),
        home_url('/ask-mirror-talk/')
    ) . '#ask-mirror-talk-form';
}

function mirrortalk_render_question_of_the_day($context = 'inline', $echo = true) {
    $qotd = mirrortalk_get_question_of_the_day();
    $context = in_array($context, array('home', 'inline'), true) ? $context : 'inline';
    $answer_url = mirrortalk_qotd_answer_url($qotd['question']);
    $label_date = wp_date('l, F j', strtotime($qotd['date'] . ' 12:00:00 UTC'));

    ob_start();
    ?>
    <aside class="mt-living-question mt-living-question--<?php echo esc_attr($context); ?>" data-mt-living-question data-mt-qotd-date="<?php echo esc_attr($qotd['date']); ?>" aria-labelledby="mt-living-question-title-<?php echo esc_attr($context); ?>">
        <div class="mt-living-question__aura" aria-hidden="true"><span></span><span></span><span></span></div>
        <div class="mt-living-question__content">
            <div class="mt-living-question__meta">
                <span><?php echo esc_html($context === 'inline' ? __('A thoughtful pause', 'astra-child') : __('The Living Question', 'astra-child')); ?></span>
                <time datetime="<?php echo esc_attr($qotd['date']); ?>" data-mt-qotd-time><?php echo esc_html($label_date); ?></time>
            </div>
            <p class="mt-living-question__theme" data-mt-qotd-theme-label><?php echo esc_html($qotd['theme']); ?></p>
            <?php if ($context === 'home') : ?>
                <h2 class="mt-living-question__question" id="mt-living-question-title-home" data-mt-qotd-question><?php echo esc_html($qotd['question']); ?></h2>
            <?php else : ?>
                <p class="mt-living-question__question" id="mt-living-question-title-inline" data-mt-qotd-question><?php echo esc_html($qotd['question']); ?></p>
            <?php endif; ?>
            <p class="mt-living-question__invitation"><?php echo esc_html($context === 'inline' ? __('If this question meets you where you are, explore a grounded response without losing your place in the conversation.', 'astra-child') : __('Pause with the question, then enter the Living Mirror for a thoughtful response grounded in the Mirror Talk archive.', 'astra-child')); ?></p>
            <div class="mt-living-question__actions">
                <a class="mt-button" href="<?php echo esc_url($answer_url); ?>" data-mt-qotd-answer data-mt-qotd-theme="<?php echo esc_attr($qotd['theme']); ?>"><?php esc_html_e('Explore the answer', 'astra-child'); ?> <span aria-hidden="true">→</span></a>
                <?php if ($context === 'home') : ?>
                    <button type="button" class="mt-living-question__reminder" data-mt-qotd-reminder><?php esc_html_e('Send me tomorrow’s question', 'astra-child'); ?></button>
                <?php endif; ?>
            </div>
            <p class="mt-living-question__status" data-mt-qotd-status role="status" aria-live="polite"></p>
        </div>
        <p class="mt-living-question__mark" aria-hidden="true">?</p>
    </aside>
    <?php
    $html = ob_get_clean();
    if ($echo) echo $html; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
    return $html;
}

function mirrortalk_qotd_content_is_eligible($post_id) {
    if (!$post_id || is_admin() || is_feed() || !is_singular(array('post', 'page')) || is_front_page()) return false;
    if (!in_the_loop() || !is_main_query()) return false;
    if (get_post_status($post_id) !== 'publish') return false;
    $slug = (string) get_post_field('post_name', $post_id);
    return !in_array($slug, array(
        'ask-mirror-talk', 'insights', 'contact', 'join-us', 'privacy-policy',
        'editorial-standards', 'corrections', 'listen', 'listen-connect',
    ), true);
}

/**
 * Find an insertion point between top-level editorial elements.
 *
 * A simple search for the first H2 can place the card inside a Composer
 * takeaway, table, quote or other semantic container. This lightweight token
 * walk preserves the original HTML byte-for-byte and accepts only boundaries
 * where no parent element remains open.
 */
function mirrortalk_qotd_word_count($content) {
    $plain_text = trim(wp_strip_all_tags(strip_shortcodes($content)));
    preg_match_all('/[\p{L}\p{N}][\p{L}\p{N}\x{2019}\x{0027}-]*/u', $plain_text, $matches);
    return count($matches[0]);
}

function mirrortalk_qotd_safe_insertion_offset($content) {
    $void_elements = array('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr');
    $stack = array();
    $top_level_heading_offsets = array();
    $top_level_paragraph_ends = array();

    $word_count = mirrortalk_qotd_word_count($content);
    if ($word_count < 250) return null;

    if (!preg_match_all('/<!--[\s\S]*?-->|<\/?[a-zA-Z][^>]*>/', $content, $tokens, PREG_OFFSET_CAPTURE)) return null;

    foreach ($tokens[0] as $token_data) {
        $token = $token_data[0];
        $offset = (int) $token_data[1];
        if (strncmp($token, '<!--', 4) === 0) continue;

        if (preg_match('/^<\/\s*([a-zA-Z0-9:-]+)/', $token, $closing)) {
            $tag = strtolower($closing[1]);
            if (!empty($stack)) {
                $opened = array_pop($stack);
                if ($opened !== $tag) {
                    $stack = array();
                    continue;
                }
            }
            if (empty($stack) && $tag === 'p') {
                $top_level_paragraph_ends[] = $offset + strlen($token);
            }
            continue;
        }

        if (!preg_match('/^<\s*([a-zA-Z0-9:-]+)/', $token, $opening)) continue;
        $tag = strtolower($opening[1]);
        $is_top_level = empty($stack);
        if ($is_top_level && $tag === 'h2') $top_level_heading_offsets[] = $offset;

        $self_closing = substr(rtrim($token), -2) === '/>' || in_array($tag, $void_elements, true);
        if (!$self_closing) $stack[] = $tag;
    }

    $progress_for = function($offset) use ($content, $word_count) {
        return mirrortalk_qotd_word_count(substr($content, 0, $offset)) / max(1, $word_count);
    };
    $within_reading_window = function($offset) use ($progress_for) {
        $progress = $progress_for($offset);
        return $progress >= .30 && $progress <= .68;
    };

    $heading_candidates = array_values(array_filter($top_level_heading_offsets, $within_reading_window));
    if (!empty($heading_candidates)) {
        foreach ($heading_candidates as $offset) {
            if ($progress_for($offset) >= .46) return $offset;
        }
        return end($heading_candidates);
    }

    $paragraph_candidates = array_values(array_filter($top_level_paragraph_ends, $within_reading_window));
    if (!empty($paragraph_candidates)) {
        usort($paragraph_candidates, function($left, $right) use ($progress_for) {
            return abs($progress_for($left) - .46) <=> abs($progress_for($right) - .46);
        });
        return $paragraph_candidates[0];
    }

    return null;
}

function mirrortalk_insert_qotd_after_editorial_opening($content) {
    $post_id = get_the_ID();
    if (!mirrortalk_qotd_content_is_eligible($post_id)) return $content;
    if (strpos($content, 'data-mt-living-question') !== false) return $content;

    $card = mirrortalk_render_question_of_the_day('inline', false);
    $offset = mirrortalk_qotd_safe_insertion_offset($content);
    if ($offset !== null) return substr($content, 0, $offset) . $card . substr($content, $offset);

    // Short or structurally ambiguous documents remain uninterrupted. The
    // persistent Ask entry point still provides access without forcing a card
    // into an unsafe or distracting position.
    return $content;
}
add_filter('the_content', 'mirrortalk_insert_qotd_after_editorial_opening', 36);

function mirrortalk_serve_push_only_worker() {
    $path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
    if ($path !== '/mirror-talk-push-sw.js') return;
    $file = get_stylesheet_directory() . '/mirror-talk-push-sw.js';
    if (!is_readable($file)) return;
    while (ob_get_level()) ob_end_clean();
    status_header(200);
    header('Content-Type: application/javascript; charset=UTF-8');
    header('Service-Worker-Allowed: /');
    header('Cache-Control: no-cache, no-store, must-revalidate');
    header('X-LiteSpeed-Cache-Control: no-cache');
    header('X-Content-Type-Options: nosniff');
    readfile($file);
    exit;
}
add_action('init', 'mirrortalk_serve_push_only_worker', 0);
