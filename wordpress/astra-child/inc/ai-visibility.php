<?php
/** Privacy-preserving, first-party AI discovery observations. */
if (!defined('ABSPATH')) exit;

function mirrortalk_ai_sources() {
    return array(
        'chatgpt' => array('hosts' => array('chatgpt.com', 'chat.openai.com'), 'agents' => array('OAI-SearchBot', 'ChatGPT-User', 'GPTBot')),
        'perplexity' => array('hosts' => array('perplexity.ai'), 'agents' => array('PerplexityBot', 'Perplexity-User')),
        'claude' => array('hosts' => array('claude.ai'), 'agents' => array('ClaudeBot', 'Claude-User', 'Claude-SearchBot')),
        // Copilot and Gemini referrals are identifiable. Their general-purpose
        // Bingbot/Googlebot crawls are intentionally not presented as AI use.
        'copilot' => array('hosts' => array('copilot.microsoft.com'), 'agents' => array()),
        'gemini' => array('hosts' => array('gemini.google.com'), 'agents' => array()),
    );
}

function mirrortalk_ai_visibility_observe() {
    if (is_admin() || wp_doing_ajax() || wp_doing_cron() || is_user_logged_in()) return;
    $agent = substr((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 300);
    $referrer = esc_url_raw((string) ($_SERVER['HTTP_REFERER'] ?? ''));
    $ref_host = strtolower((string) wp_parse_url($referrer, PHP_URL_HOST));
    $ref_host = preg_replace('/^www\./', '', $ref_host);
    $engine = ''; $kind = '';
    foreach (mirrortalk_ai_sources() as $name => $source) {
        foreach ($source['agents'] as $needle) if ($agent && stripos($agent, $needle) !== false) { $engine = $name; $kind = 'crawler'; break 2; }
        foreach ($source['hosts'] as $host) if ($ref_host === $host || substr($ref_host, -strlen('.' . $host)) === '.' . $host) { $engine = $name; $kind = 'referral'; break 2; }
    }
    if (!$engine) return;
    $day = gmdate('Y-m-d'); $data = (array) get_option('mirrortalk_ai_visibility', array());
    if (!isset($data[$day])) $data[$day] = array('crawler' => array(), 'referral' => array(), 'landing' => array());
    $data[$day][$kind][$engine] = 1 + (int) ($data[$day][$kind][$engine] ?? 0);
    if ($kind === 'referral') {
        $path = sanitize_text_field((string) wp_parse_url((string) ($_SERVER['REQUEST_URI'] ?? '/'), PHP_URL_PATH));
        $key = $engine . '|' . ($path ?: '/'); $data[$day]['landing'][$key] = 1 + (int) ($data[$day]['landing'][$key] ?? 0);
        arsort($data[$day]['landing']); $data[$day]['landing'] = array_slice($data[$day]['landing'], 0, 50, true);
    }
    update_option('mirrortalk_ai_visibility', array_slice($data, -120, null, true), false);
}
add_action('template_redirect', 'mirrortalk_ai_visibility_observe', 1);

function mirrortalk_ai_visibility_totals($days = 30) {
    $data = (array) get_option('mirrortalk_ai_visibility', array()); $cutoff = gmdate('Y-m-d', strtotime('-' . max(1, $days) . ' days'));
    $totals = array('crawler' => array(), 'referral' => array(), 'landing' => array());
    foreach ($data as $day => $rows) if ($day >= $cutoff) foreach ($totals as $kind => $unused) foreach ((array) ($rows[$kind] ?? array()) as $key => $count) $totals[$kind][$key] = (int) ($totals[$kind][$key] ?? 0) + (int) $count;
    arsort($totals['landing']); return $totals;
}

function mirrortalk_ai_readiness() {
    $posts = get_posts(array('post_type' => 'post', 'post_status' => 'publish', 'numberposts' => 100, 'fields' => 'ids')); $with_images = 0; $with_descriptions = 0;
    foreach ($posts as $id) {
        if (get_post_thumbnail_id($id)) $with_images++;
        $description = trim((string) get_post_meta($id, '_mirrortalk_meta_description', true));
        if (!$description) $description = trim((string) get_post_field('post_excerpt', $id));
        if (!$description) $description = trim(wp_trim_words(wp_strip_all_tags((string) get_post_field('post_content', $id)), 28, ''));
        if ($description) $with_descriptions++;
    }
    $checks = array(
        'Public canonical source guide' => get_option('mirrortalk_llms_owner_version') === MIRRORTALK_SEO_PLATFORM_VERSION,
        'AI discovery controls are active' => has_filter('robots_txt'),
        'Entity and podcast structured data' => function_exists('mirrortalk_schema_graph'),
        'Search Console connected' => !empty(((array) get_option('mirrortalk_google_status', array()))['connected']),
        'Bing Webmaster connected' => !empty(((array) get_option('mirrortalk_bing_status', array()))['connected']),
        'Most recent articles have source descriptions' => !$posts || $with_descriptions >= ceil(count($posts) * .8),
        'Most recent articles have distinctive images' => !$posts || $with_images >= ceil(count($posts) * .7),
    );
    return array('score' => (int) round(100 * count(array_filter($checks)) / count($checks)), 'checks' => $checks);
}

function mirrortalk_ai_visibility_admin_panel() {
    $totals = mirrortalk_ai_visibility_totals(); $readiness = mirrortalk_ai_readiness();
    echo '<hr><h2>' . esc_html__('AI visibility', 'astra-child') . '</h2><p>' . esc_html__('First-party observations from the last 30 days. AI referrals are visits arriving from a recognizable AI service. AI crawler requests are user-agent observations and can include search, user-requested retrieval or model improvement. Neither metric proves that a generated answer cited Mirror Talk, and privacy tools may remove referral data.', 'astra-child') . '</p>';
    echo '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px"><div class="card"><h3>' . esc_html__('AI readiness', 'astra-child') . '</h3><p style="font-size:28px"><strong>' . esc_html($readiness['score']) . '%</strong></p></div>';
    foreach (array('crawler' => __('AI crawler observations', 'astra-child'), 'referral' => __('AI-referred visits', 'astra-child')) as $kind => $label) { echo '<div class="card"><h3>' . esc_html($label) . '</h3>'; if (!$totals[$kind]) echo '<p>' . esc_html__('No observations yet.', 'astra-child') . '</p>'; else foreach ($totals[$kind] as $engine => $count) echo '<p>' . esc_html(ucfirst($engine)) . ': <strong>' . esc_html($count) . '</strong></p>'; echo '</div>'; } echo '</div>';
    echo '<h3>' . esc_html__('Readiness checks', 'astra-child') . '</h3><ul>'; foreach ($readiness['checks'] as $label => $passed) echo '<li>' . ($passed ? '✓ ' : '○ ') . esc_html($label) . '</li>'; echo '</ul>';
    if ($totals['landing']) { echo '<h3>' . esc_html__('Pages discovered through AI referrals', 'astra-child') . '</h3><table class="widefat striped"><thead><tr><th>Source</th><th>Landing page</th><th>Visits</th></tr></thead><tbody>'; foreach (array_slice($totals['landing'], 0, 20, true) as $key => $count) { list($engine, $path) = array_pad(explode('|', $key, 2), 2, ''); echo '<tr><td>' . esc_html(ucfirst($engine)) . '</td><td><code>' . esc_html($path) . '</code></td><td>' . esc_html($count) . '</td></tr>'; } echo '</tbody></table>'; }
    echo '<p class="description">' . esc_html__('This aggregate monitor stores no IP address, cookie, prompt or private Ask Mirror Talk content. Direct citation monitoring requires an owner-approved external answer-monitoring provider; Search Console and Bing Webmaster do not expose complete AI-answer citations.', 'astra-child') . '</p>';
}
