<?php
/**
 * Evidence-led SEO learning loop.
 *
 * Learns from verified query/page data and first-party engagement. Experiments
 * affect only the search/social title, never the visible editorial headline.
 */
if (!defined('ABSPATH')) exit;

function mirrortalk_learning_enabled() {
    return get_option('mirrortalk_seo_learning_enabled', '1') === '1';
}

function mirrortalk_learning_rows() {
    return array_values(array_filter((array) get_option('mirrortalk_search_performance', array()), function ($row) {
        return ($row['engine'] ?? '') === 'google' && !empty($row['page']) && !empty($row['query']) && !empty($row['date']);
    }));
}

function mirrortalk_learning_url($url) {
    $parts = wp_parse_url((string) $url);
    if (empty($parts['host'])) return '';
    return strtolower($parts['host']) . untrailingslashit($parts['path'] ?? '/');
}

function mirrortalk_learning_metrics($url, $start, $end) {
    $key = mirrortalk_learning_url($url); $result = array('clicks' => 0, 'impressions' => 0, 'ctr' => 0);
    foreach (mirrortalk_learning_rows() as $row) {
        $date = (string) $row['date'];
        if ($date < $start || $date > $end || mirrortalk_learning_url($row['page']) !== $key) continue;
        $result['clicks'] += max(0, (int) ($row['clicks'] ?? 0));
        $result['impressions'] += max(0, (int) ($row['impressions'] ?? 0));
    }
    $result['ctr'] = $result['impressions'] ? $result['clicks'] / $result['impressions'] : 0;
    return $result;
}

/**
 * Keep automated learning away from navigational, operator-led, unsafe and
 * contextually unrelated queries. Raw Search Console rows remain visible in
 * reporting; this gate applies only to automatic focus keywords/experiments.
 */
function mirrortalk_learning_query_eligible($query, $post_id = 0) {
    $query = strtolower(trim(preg_replace('/\s+/', ' ', sanitize_text_field((string) $query))));
    if (!$query || strlen($query) > 100 || count(preg_split('/\s+/', $query)) > 8) return false;
    if (preg_match('/(?:^|\s)(?:site|inurl|intitle|allinurl|allintitle|cache|filetype):/i', $query)) return false;
    if (preg_match('#(?:https?://|www\.|\.(?:com|org|net|co|io)(?:/|\s|$))#i', $query)) return false;

    $compact = preg_replace('/[^a-z0-9]+/', '', remove_accents($query));
    $brand_queries = array('mirrortalk', 'mirrortalkpodcast', 'themirrortalk', 'mirrortalksoulfulconversations');
    if (in_array($compact, $brand_queries, true)) return false;

    // Protect editorial metadata from adult/spam traffic that can appear in GSC.
    if (preg_match('/\b(?:porn|pornhub|xxx|sexcam|casino|viagra|cialis)\b/i', $query)) return false;
    if (!$post_id || !get_post_status($post_id)) return false;

    $post = get_post($post_id);
    if (!$post) return false;
    $haystack = strtolower(remove_accents(wp_strip_all_tags(
        get_the_title($post_id) . ' ' . (string) $post->post_excerpt . ' ' . (string) $post->post_content
    )));
    $tokens = preg_split('/[^a-z0-9]+/', remove_accents($query), -1, PREG_SPLIT_NO_EMPTY);
    $stopwords = array('a', 'an', 'and', 'are', 'at', 'by', 'for', 'from', 'how', 'in', 'is', 'of', 'on', 'or', 'the', 'to', 'with');
    $tokens = array_values(array_unique(array_filter($tokens, function ($token) use ($stopwords) {
        return strlen($token) >= 3 && !in_array($token, $stopwords, true);
    })));
    if (!$tokens) return false;
    $matches = 0;
    foreach ($tokens as $token) if (preg_match('/\b' . preg_quote($token, '/') . '\b/i', $haystack)) $matches++;
    $required = count($tokens) <= 2 ? 1 : (int) ceil(count($tokens) / 2);
    return (bool) apply_filters('mirrortalk_learning_query_eligible', $matches >= $required, $query, $post_id, $matches, $required);
}

function mirrortalk_learning_page_queries($post_id, $days = 28) {
    $url = mirrortalk_learning_url(get_permalink($post_id));
    $cutoff = gmdate('Y-m-d', time() - max(7, $days) * DAY_IN_SECONDS); $queries = array();
    foreach (mirrortalk_learning_rows() as $row) {
        if ((string) $row['date'] < $cutoff || mirrortalk_learning_url($row['page']) !== $url) continue;
        $query = strtolower(trim(preg_replace('/\s+/', ' ', sanitize_text_field((string) $row['query']))));
        if (!mirrortalk_learning_query_eligible($query, $post_id)) continue;
        if (!isset($queries[$query])) $queries[$query] = array('query' => $query, 'clicks' => 0, 'impressions' => 0, 'position_sum' => 0, 'position_weight' => 0);
        $impressions = max(0, (int) ($row['impressions'] ?? 0));
        $queries[$query]['clicks'] += max(0, (int) ($row['clicks'] ?? 0));
        $queries[$query]['impressions'] += $impressions;
        $queries[$query]['position_sum'] += max(0, (float) ($row['position'] ?? 0)) * $impressions;
        $queries[$query]['position_weight'] += $impressions;
    }
    foreach ($queries as &$item) {
        $item['ctr'] = $item['impressions'] ? $item['clicks'] / $item['impressions'] : 0;
        $item['position'] = $item['position_weight'] ? $item['position_sum'] / $item['position_weight'] : 0;
        $position_factor = $item['position'] >= 4 && $item['position'] <= 20 ? 1.35 : 1;
        $item['opportunity'] = round($item['impressions'] * max(.05, 1 - $item['ctr']) * $position_factor, 2);
    }
    unset($item); usort($queries, function ($a, $b) { return $b['opportunity'] <=> $a['opportunity']; });
    return array_values($queries);
}

function mirrortalk_learning_focus_keyword($post_id) {
    $queries = mirrortalk_learning_page_queries($post_id);
    foreach ($queries as $query) if ($query['impressions'] >= 5) return $query;
    return array();
}

function mirrortalk_learning_trim_title($value, $limit) {
    $value = trim(wp_strip_all_tags((string) $value));
    $length = function_exists('mb_strlen') ? mb_strlen($value) : strlen($value);
    if ($length <= $limit) return $value;
    $cut = function_exists('mb_substr') ? mb_substr($value, 0, $limit + 1) : substr($value, 0, $limit + 1);
    $cut = preg_replace('/\s+\S*$/u', '', $cut);
    return rtrim($cut, " \t\n\r\0\x0B:;,.—-");
}

function mirrortalk_learning_title_candidate($post_id, $keyword) {
    $base = trim((string) get_the_title($post_id)); $keyword = trim((string) $keyword);
    if (!$base || !$keyword || stripos($base, $keyword) !== false) return '';
    $keyword_title = implode(' ', array_map(function ($word) { return strlen($word) > 3 ? ucfirst($word) : $word; }, preg_split('/\s+/', $keyword)));
    $available = max(18, 60 - strlen($keyword_title) - strlen(' —  | Mirror Talk'));
    $candidate = $keyword_title . ' — ' . mirrortalk_learning_trim_title($base, $available) . ' | Mirror Talk';
    return mirrortalk_learning_trim_title($candidate, 60);
}

function mirrortalk_learning_log($entry) {
    $log = (array) get_option('mirrortalk_seo_learning_log', array());
    $log[] = array_merge(array('time' => time()), $entry);
    update_option('mirrortalk_seo_learning_log', array_slice($log, -200), false);
}

function mirrortalk_learning_significant_ctr_gain($baseline, $variant) {
    $n1 = (int) ($baseline['impressions'] ?? 0); $n2 = (int) ($variant['impressions'] ?? 0);
    if ($n1 < 100 || $n2 < 100) return false;
    $c1 = (int) ($baseline['clicks'] ?? 0); $c2 = (int) ($variant['clicks'] ?? 0);
    $p1 = $c1 / $n1; $p2 = $c2 / $n2; $pooled = ($c1 + $c2) / ($n1 + $n2);
    $error = sqrt(max(.0000001, $pooled * (1 - $pooled) * ((1 / $n1) + (1 / $n2))));
    $z = ($p2 - $p1) / $error;
    return $p2 >= $p1 + .005 && $p2 >= $p1 * 1.08 && $z >= 1.64;
}

function mirrortalk_learning_finish_experiments() {
    $experiments = (array) get_option('mirrortalk_seo_experiments', array()); $changed = false;
    foreach ($experiments as $post_id => &$experiment) {
        if (($experiment['status'] ?? '') !== 'running') continue;
        if (!get_post_status($post_id)) { $experiment['status'] = 'content_removed'; $experiment['finished_at'] = time(); $changed = true; continue; }
        $current_title = (string) get_post_meta($post_id, '_mirrortalk_meta_title', true);
        if ($current_title !== (string) ($experiment['candidate_title'] ?? '')) {
            $experiment['status'] = 'editor_override'; $experiment['finished_at'] = time(); $changed = true;
            mirrortalk_learning_log(array('post_id' => (int) $post_id, 'action' => 'editor_override', 'keyword' => $experiment['focus_keyword'] ?? '', 'title' => $current_title));
            continue;
        }
        $age = time() - (int) ($experiment['started_at'] ?? 0); if ($age < 21 * DAY_IN_SECONDS) continue;
        $after = mirrortalk_learning_metrics(get_permalink($post_id), gmdate('Y-m-d', (int) $experiment['started_at']), gmdate('Y-m-d', time() - 3 * DAY_IN_SECONDS));
        if ($after['impressions'] < 50 && $age < 35 * DAY_IN_SECONDS) continue;
        $baseline = (array) ($experiment['baseline_metrics'] ?? array()); $baseline_ctr = (float) ($baseline['ctr'] ?? 0); $decision = 'rolled_back';
        if (mirrortalk_learning_significant_ctr_gain($baseline, $after)) {
            $decision = 'kept';
        } else {
            $baseline_title = (string) ($experiment['baseline_title'] ?? '');
            if ($baseline_title) update_post_meta($post_id, '_mirrortalk_meta_title', $baseline_title); else delete_post_meta($post_id, '_mirrortalk_meta_title');
        }
        $experiment['status'] = $decision; $experiment['finished_at'] = time(); $experiment['variant_metrics'] = $after; $changed = true;
        mirrortalk_seo_snapshot($post_id);
        mirrortalk_indexnow_queue_url(get_permalink($post_id));
        mirrortalk_learning_log(array('post_id' => (int) $post_id, 'action' => $decision, 'keyword' => $experiment['focus_keyword'] ?? '', 'title' => $experiment['candidate_title'] ?? '', 'baseline_ctr' => $baseline_ctr, 'variant_ctr' => $after['ctr']));
    }
    unset($experiment); if ($changed) update_option('mirrortalk_seo_experiments', $experiments, false);
}

function mirrortalk_learning_start_experiments() {
    $experiments = (array) get_option('mirrortalk_seo_experiments', array());
    $running = count(array_filter($experiments, function ($item) { return ($item['status'] ?? '') === 'running'; }));
    if ($running >= 2) return;
    $posts = get_posts(array('post_type' => 'post', 'post_status' => 'publish', 'numberposts' => 100, 'orderby' => 'modified', 'order' => 'DESC'));
    foreach ($posts as $post) {
        if ($running >= 2 || get_post_meta($post->ID, '_mirrortalk_seo_auto_lock', true) || (($experiments[$post->ID]['status'] ?? '') === 'running')) continue;
        $focus = mirrortalk_learning_focus_keyword($post->ID); if (!$focus || $focus['impressions'] < 100) continue;
        if (!empty($experiments[$post->ID]) && ($experiments[$post->ID]['focus_keyword'] ?? '') === $focus['query']) continue;
        update_post_meta($post->ID, '_mirrortalk_focus_keyword', $focus['query']);
        update_post_meta($post->ID, '_mirrortalk_focus_keyword_evidence', array('updated' => time(), 'impressions' => $focus['impressions'], 'clicks' => $focus['clicks'], 'position' => round($focus['position'], 1)));
        $candidate = mirrortalk_learning_title_candidate($post->ID, $focus['query']); if (!$candidate) continue;
        $end = gmdate('Y-m-d', time() - 3 * DAY_IN_SECONDS); $start = gmdate('Y-m-d', strtotime($end . ' -14 days'));
        $baseline = mirrortalk_learning_metrics(get_permalink($post->ID), $start, $end); if ($baseline['impressions'] < 100) continue;
        $baseline_title = (string) get_post_meta($post->ID, '_mirrortalk_meta_title', true);
        $prior = (array) ($experiments[$post->ID] ?? array());
        if ($baseline_title && (!$prior || (($prior['status'] ?? '') === 'kept' && $baseline_title !== ($prior['candidate_title'] ?? '')) || ($prior['status'] ?? '') !== 'kept')) continue;
        mirrortalk_seo_snapshot($post->ID); update_post_meta($post->ID, '_mirrortalk_meta_title', $candidate); mirrortalk_seo_snapshot($post->ID);
        $experiments[$post->ID] = array('status' => 'running', 'started_at' => time(), 'baseline_title' => $baseline_title, 'candidate_title' => $candidate, 'focus_keyword' => $focus['query'], 'baseline_metrics' => $baseline);
        mirrortalk_learning_log(array('post_id' => $post->ID, 'action' => 'started', 'keyword' => $focus['query'], 'title' => $candidate, 'baseline_ctr' => $baseline['ctr']));
        mirrortalk_indexnow_queue_url(get_permalink($post)); $running++;
    }
    update_option('mirrortalk_seo_experiments', $experiments, false);
}

function mirrortalk_learning_refresh_keywords() {
    foreach (get_posts(array('post_type' => mirrortalk_seo_public_post_types(), 'post_status' => 'publish', 'numberposts' => 300)) as $post) {
        if (get_post_meta($post->ID, '_mirrortalk_seo_auto_lock', true)) continue;
        $focus = mirrortalk_learning_focus_keyword($post->ID); if (!$focus) continue;
        update_post_meta($post->ID, '_mirrortalk_focus_keyword', $focus['query']);
        update_post_meta($post->ID, '_mirrortalk_focus_keyword_evidence', array('updated' => time(), 'impressions' => $focus['impressions'], 'clicks' => $focus['clicks'], 'position' => round($focus['position'], 1)));
    }
}

function mirrortalk_seo_learning_cycle() {
    if (!mirrortalk_learning_enabled()) return;
    mirrortalk_learning_finish_experiments();
    mirrortalk_learning_refresh_keywords();
    mirrortalk_learning_start_experiments();
    update_option('mirrortalk_seo_learning_last_run', time(), false);
}
add_action('mirrortalk_weekly_seo_report', function(){mirrortalk_runtime_queue('mirrortalk_learning_cycle_manual',array(),20);}, 20);

function mirrortalk_learning_pause_and_restore() {
    $experiments = (array) get_option('mirrortalk_seo_experiments', array()); $changed = false;
    foreach ($experiments as $post_id => &$experiment) if (($experiment['status'] ?? '') === 'running') {
        $current_title = (string) get_post_meta($post_id, '_mirrortalk_meta_title', true);
        if ($current_title !== (string) ($experiment['candidate_title'] ?? '')) { $experiment['status'] = 'editor_override'; $experiment['finished_at'] = time(); $changed = true; continue; }
        $baseline = (string) ($experiment['baseline_title'] ?? '');
        if ($baseline) update_post_meta($post_id, '_mirrortalk_meta_title', $baseline); else delete_post_meta($post_id, '_mirrortalk_meta_title');
        $experiment['status'] = 'paused_rolled_back'; $experiment['finished_at'] = time(); $changed = true;
        mirrortalk_seo_snapshot($post_id); mirrortalk_indexnow_queue_url(get_permalink($post_id));
        mirrortalk_learning_log(array('post_id' => (int) $post_id, 'action' => 'paused_rolled_back', 'keyword' => $experiment['focus_keyword'] ?? '', 'title' => $experiment['candidate_title'] ?? ''));
    }
    unset($experiment); if ($changed) update_option('mirrortalk_seo_experiments', $experiments, false);
}

function mirrortalk_learning_internal_link_suggestion($post_id, $query) {
    $tokens = array_values(array_filter(preg_split('/[^a-z0-9]+/', strtolower(remove_accents((string) $query))), function ($token) { return strlen($token) >= 4; }));
    if (!$tokens) return '';
    $source = get_post($post_id); if (!$source) return '';
    $best = array('score' => 0, 'title' => '', 'url' => '');
    foreach (get_posts(array('post_type' => mirrortalk_seo_public_post_types(), 'post_status' => 'publish', 'numberposts' => 100, 'exclude' => array($post_id))) as $candidate) {
        $url = get_permalink($candidate); if (!$url || strpos($source->post_content, $url) !== false) continue;
        $title = strtolower(remove_accents(get_the_title($candidate))); $score = 0;
        foreach ($tokens as $token) if (preg_match('/\b' . preg_quote($token, '/') . '\b/i', $title)) $score++;
        if ($score > $best['score']) $best = array('score' => $score, 'title' => get_the_title($candidate), 'url' => $url);
    }
    return $best['score'] ? $best['title'] . ' — ' . $best['url'] : '';
}

function mirrortalk_learning_opportunities() {
    $items = array();
    foreach (get_posts(array('post_type' => mirrortalk_seo_public_post_types(), 'post_status' => 'publish', 'numberposts' => 200)) as $post) {
        $focus = mirrortalk_learning_focus_keyword($post->ID); if (!$focus) continue;
        if ($focus['position'] >= 4 && $focus['position'] <= 20) $recommendation = __('Expand the answer and strengthen relevant internal links.', 'astra-child');
        elseif ($focus['position'] <= 3 && $focus['ctr'] < .03) $recommendation = __('Test a clearer search title aligned with intent.', 'astra-child');
        elseif ($focus['position'] > 20) $recommendation = __('Strengthen the supporting topic hub before changing the title.', 'astra-child');
        else $recommendation = __('Monitor; there is not enough evidence for an automatic change.', 'astra-child');
        $items[] = array('post' => get_the_title($post), 'query' => $focus['query'], 'impressions' => $focus['impressions'], 'clicks' => $focus['clicks'], 'ctr' => round($focus['ctr'] * 100, 1) . '%', 'position' => round($focus['position'], 1), 'recommendation' => $recommendation, 'suggested_link' => mirrortalk_learning_internal_link_suggestion($post->ID, $focus['query']), 'score' => $focus['opportunity']);
    }
    usort($items, function ($a, $b) { return $b['score'] <=> $a['score']; }); return array_slice($items, 0, 20);
}

add_filter('mirrortalk_schema_graph', function ($schema) {
    if (!is_singular('post')) return $schema;
    $keyword = trim((string) get_post_meta(get_queried_object_id(), '_mirrortalk_focus_keyword', true)); if (!$keyword) return $schema;
    foreach ($schema['@graph'] as &$node) if (in_array('Article', (array) ($node['@type'] ?? ''), true)) {
        $keywords = array_filter(array_map('trim', explode(',', (string) ($node['keywords'] ?? '')))); $keywords[] = $keyword;
        $node['keywords'] = implode(', ', array_values(array_unique($keywords)));
    }
    unset($node); return $schema;
}, 30);

add_action('add_meta_boxes', function () {
    add_meta_box('mirrortalk-seo-learning', __('Mirror Talk SEO Learning', 'astra-child'), 'mirrortalk_learning_meta_box', 'post', 'side', 'default');
});
function mirrortalk_learning_meta_box($post) {
    $keyword = get_post_meta($post->ID, '_mirrortalk_focus_keyword', true); $evidence = (array) get_post_meta($post->ID, '_mirrortalk_focus_keyword_evidence', true);
    $experiment = ((array) get_option('mirrortalk_seo_experiments', array()))[$post->ID] ?? array(); wp_nonce_field('mirrortalk_learning_post', 'mirrortalk_learning_nonce');
    echo '<p><strong>' . esc_html__('Evidence-led focus keyword', 'astra-child') . '</strong><br>' . esc_html($keyword ?: __('Waiting for verified query data', 'astra-child')) . '</p>';
    if ($evidence) echo '<p><small>' . esc_html(sprintf(__('%1$d impressions · %2$d clicks · position %3$s', 'astra-child'), $evidence['impressions'] ?? 0, $evidence['clicks'] ?? 0, $evidence['position'] ?? '—')) . '</small></p>';
    if ($experiment) echo '<p><strong>' . esc_html__('Title experiment:', 'astra-child') . '</strong> ' . esc_html($experiment['status'] ?? '') . '<br><small>' . esc_html($experiment['candidate_title'] ?? '') . '</small></p>';
    echo '<label><input type="checkbox" name="mirrortalk_seo_auto_lock" value="1" ' . checked((bool) get_post_meta($post->ID, '_mirrortalk_seo_auto_lock', true), true, false) . '> ' . esc_html__('Keep this post under manual SEO control', 'astra-child') . '</label>';
}
add_action('save_post_post', function ($post_id) {
    if (!isset($_POST['mirrortalk_learning_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['mirrortalk_learning_nonce'])), 'mirrortalk_learning_post') || !current_user_can('edit_post', $post_id)) return;
    if (!empty($_POST['mirrortalk_seo_auto_lock'])) update_post_meta($post_id, '_mirrortalk_seo_auto_lock', '1'); else delete_post_meta($post_id, '_mirrortalk_seo_auto_lock');
});

add_action('save_post_post', function ($post_id) {
    if (wp_is_post_revision($post_id) || wp_is_post_autosave($post_id)) return;
    $experiments = (array) get_option('mirrortalk_seo_experiments', array());
    if (($experiments[$post_id]['status'] ?? '') !== 'running') return;
    $current = (string) get_post_meta($post_id, '_mirrortalk_meta_title', true);
    if ($current === (string) ($experiments[$post_id]['candidate_title'] ?? '')) return;
    $experiments[$post_id]['status'] = 'editor_override'; $experiments[$post_id]['finished_at'] = time();
    update_option('mirrortalk_seo_experiments', $experiments, false);
    mirrortalk_learning_log(array('post_id' => $post_id, 'action' => 'editor_override', 'keyword' => $experiments[$post_id]['focus_keyword'] ?? '', 'title' => $current));
}, 120);

function mirrortalk_seo_learning_panel() {
    $experiments = (array) get_option('mirrortalk_seo_experiments', array()); $log = array_reverse((array) get_option('mirrortalk_seo_learning_log', array()));
    echo '<section id="learning" class="mti-panel"><header><div><p class="mti-kicker">SEO LEARNING</p><h2>' . esc_html__('Evidence-led optimisation', 'astra-child') . '</h2><p>' . esc_html__('Focus keywords come from verified queries. Search-title experiments require at least 100 baseline impressions, run one variant for at least 21 days, preserve the visible headline and automatically keep or roll back the result.', 'astra-child') . '</p></div><form method="post" action="' . esc_url(admin_url('admin-post.php')) . '"><input type="hidden" name="action" value="mirrortalk_learning_settings">';
    wp_nonce_field('mirrortalk_learning_settings'); echo '<label><input type="checkbox" name="enabled" value="1" ' . checked(mirrortalk_learning_enabled(), true, false) . '> ' . esc_html__('Automatic guarded learning', 'astra-child') . '</label> '; submit_button(__('Save', 'astra-child'), 'secondary', 'submit', false); echo '</form></header>';
    echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '"><input type="hidden" name="action" value="mirrortalk_learning_run">'; wp_nonce_field('mirrortalk_learning_run'); submit_button(__('Run learning cycle now', 'astra-child'), 'secondary', 'submit', false); echo '</form>';
    echo '<h3>' . esc_html__('Highest-confidence opportunities', 'astra-child') . '</h3>'; mirrortalk_intelligence_table_view(mirrortalk_learning_opportunities(), array('post' => 'Post or page', 'query' => 'Observed query', 'impressions' => 'Impressions', 'clicks' => 'Clicks', 'ctr' => 'CTR', 'position' => 'Position', 'recommendation' => 'Recommended response', 'suggested_link' => 'Relevant internal link'));
    $rows = array(); foreach ($experiments as $post_id => $item) $rows[] = array('post' => get_the_title($post_id), 'keyword' => $item['focus_keyword'] ?? '', 'candidate' => $item['candidate_title'] ?? '', 'status' => $item['status'] ?? '', 'started' => !empty($item['started_at']) ? wp_date('j M Y', $item['started_at']) : '—');
    echo '<h3>' . esc_html__('Title experiments', 'astra-child') . '</h3>'; mirrortalk_intelligence_table_view($rows, array('post' => 'Post', 'keyword' => 'Focus keyword', 'candidate' => 'Search title variant', 'status' => 'Decision', 'started' => 'Started'));
    $log_rows = array(); foreach (array_slice($log, 0, 30) as $item) $log_rows[] = array('date' => wp_date('j M Y H:i', $item['time'] ?? time()), 'post' => get_the_title($item['post_id'] ?? 0), 'action' => $item['action'] ?? '', 'keyword' => $item['keyword'] ?? '', 'title' => $item['title'] ?? '');
    echo '<h3>' . esc_html__('Decision history', 'astra-child') . '</h3>'; mirrortalk_intelligence_table_view($log_rows, array('date' => 'Date', 'post' => 'Post', 'action' => 'Action', 'keyword' => 'Keyword', 'title' => 'Title')); echo '</section>';
}

add_action('admin_post_mirrortalk_learning_settings', function () {
    if (!current_user_can('manage_mirrortalk_seo')) wp_die(esc_html__('You cannot change learning settings.', 'astra-child')); check_admin_referer('mirrortalk_learning_settings');
    $enabled = !empty($_POST['enabled']); update_option('mirrortalk_seo_learning_enabled', $enabled ? '1' : '0', false);
    if (!$enabled) mirrortalk_learning_pause_and_restore();
    wp_safe_redirect(admin_url('admin.php?page=mirror-talk-intelligence#learning')); exit;
});
add_action('admin_post_mirrortalk_learning_run', function () {
    if (!current_user_can('manage_mirrortalk_seo')) wp_die(esc_html__('You cannot run SEO learning.', 'astra-child')); check_admin_referer('mirrortalk_learning_run');
    mirrortalk_runtime_queue('mirrortalk_learning_cycle_manual'); wp_safe_redirect(admin_url('admin.php?page=mirror-talk-intelligence&mt_job=queued#learning')); exit;
});
add_action('mirrortalk_learning_cycle_manual',function(){mirrortalk_runtime_run('seo_learning','mirrortalk_seo_learning_cycle',20*MINUTE_IN_SECONDS);});
