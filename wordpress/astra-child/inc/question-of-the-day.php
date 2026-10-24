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
                <span><?php esc_html_e('The Living Question', 'astra-child'); ?></span>
                <time datetime="<?php echo esc_attr($qotd['date']); ?>" data-mt-qotd-time><?php echo esc_html($label_date); ?></time>
            </div>
            <p class="mt-living-question__theme" data-mt-qotd-theme-label><?php echo esc_html($qotd['theme']); ?></p>
            <h2 id="mt-living-question-title-<?php echo esc_attr($context); ?>" data-mt-qotd-question><?php echo esc_html($qotd['question']); ?></h2>
            <p class="mt-living-question__invitation"><?php esc_html_e('Pause with the question, then enter the Living Mirror for a thoughtful response grounded in the Mirror Talk archive.', 'astra-child'); ?></p>
            <div class="mt-living-question__actions">
                <a class="mt-button" href="<?php echo esc_url($answer_url); ?>" data-mt-qotd-answer data-mt-qotd-theme="<?php echo esc_attr($qotd['theme']); ?>"><?php esc_html_e('Explore the answer', 'astra-child'); ?> <span aria-hidden="true">→</span></a>
                <button type="button" class="mt-living-question__reminder" data-mt-qotd-reminder><?php esc_html_e('Send me tomorrow’s question', 'astra-child'); ?></button>
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

function mirrortalk_insert_qotd_after_editorial_opening($content) {
    $post_id = get_the_ID();
    if (!mirrortalk_qotd_content_is_eligible($post_id)) return $content;
    if (strpos($content, 'data-mt-living-question') !== false) return $content;

    $card = mirrortalk_render_question_of_the_day('inline', false);
    $heading_offset = null;
    if (preg_match('/<h2\b/i', $content, $heading_match, PREG_OFFSET_CAPTURE)) {
        $heading_offset = (int) $heading_match[0][1];
    }
    if ($heading_offset !== null && $heading_offset >= 450) {
        return substr($content, 0, $heading_offset) . $card . substr($content, $heading_offset);
    }

    if (preg_match_all('/<\/p\s*>/i', $content, $paragraphs, PREG_OFFSET_CAPTURE) && count($paragraphs[0]) >= 3) {
        $third = $paragraphs[0][2];
        $offset = (int) $third[1] + strlen($third[0]);
        return substr($content, 0, $offset) . $card . substr($content, $offset);
    }

    return $content . $card;
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
