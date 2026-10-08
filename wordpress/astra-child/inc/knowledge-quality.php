<?php
/**
 * Mirror Talk Knowledge & Quality Engine.
 *
 * Joins verified discovery data, consented first-party signals and explicit
 * editorial facts. It never invents a guest credential, quotation or source.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_KNOWLEDGE_VERSION', '1.0.0');

function mirrortalk_intelligence_safe_search_term($value) {
    $value = trim(preg_replace('/\s+/', ' ', sanitize_text_field((string) $value)));
    if (!$value || strlen($value) > 160) return '';
    if (is_email($value) || preg_match('#(?:https?://|www\.)#i', $value)) return '';
    $value = preg_replace('/\b[\w.%+-]+@[\w.-]+\.[A-Z]{2,}\b/i', '[email removed]', $value);
    $value = preg_replace('/(?:\+?\d[\d\s().-]{7,}\d)/', '[number removed]', $value);
    return substr($value, 0, 300);
}

function mirrortalk_knowledge_fields() {
    return array(
        'guest_name' => __('Guest name', 'astra-child'),
        'guest_bio' => __('Guest biography (verified)', 'astra-child'),
        'guest_expertise' => __('Guest expertise (comma separated)', 'astra-child'),
        'transcript_url' => __('Verified transcript URL', 'astra-child'),
        'editorial_summary' => __('Editorial summary', 'astra-child'),
        'key_moments' => __('Timestamped key ideas (one per line: 12:34 — Idea)', 'astra-child'),
        'key_questions' => __('Questions answered (one per line)', 'astra-child'),
        'quotable_insights' => __('Verified quotations (one per line)', 'astra-child'),
        'sources' => __('Sources and resources (one URL per line)', 'astra-child'),
        'reviewed_by' => __('Reviewed by', 'astra-child'),
        'last_reviewed' => __('Last reviewed (YYYY-MM-DD)', 'astra-child'),
        'correction_note' => __('Public correction note', 'astra-child'),
    );
}

function mirrortalk_knowledge_lines($value, $urls = false) {
    $lines = preg_split('/\r\n|\r|\n/', (string) $value);
    $lines = array_values(array_unique(array_filter(array_map(function ($line) use ($urls) {
        $line = trim($line);
        return $urls ? esc_url_raw($line) : sanitize_text_field($line);
    }, $lines))));
    return array_slice($lines, 0, 50);
}

function mirrortalk_knowledge_meta_box() {
    foreach (array('post', 'page') as $type) add_meta_box('mirrortalk-knowledge', __('Mirror Talk knowledge & trust', 'astra-child'), 'mirrortalk_knowledge_meta_box_html', $type, 'normal', 'high');
}
add_action('add_meta_boxes', 'mirrortalk_knowledge_meta_box');

function mirrortalk_knowledge_meta_box_html($post) {
    wp_nonce_field('mirrortalk_knowledge_save', 'mirrortalk_knowledge_nonce');
    echo '<p>' . esc_html__('Only publish facts that an editor can verify. Empty fields are omitted everywhere; the system never fills credentials or quotations by guessing.', 'astra-child') . '</p><table class="form-table">';
    foreach (mirrortalk_knowledge_fields() as $key => $label) {
        $value = get_post_meta($post->ID, '_mt_' . $key, true);
        $rows = in_array($key, array('guest_bio','editorial_summary','key_moments','key_questions','quotable_insights','sources','correction_note'), true) ? 4 : 1;
        echo '<tr><th><label for="mt-' . esc_attr($key) . '">' . esc_html($label) . '</label></th><td>';
        if ($rows > 1) echo '<textarea class="large-text" rows="' . esc_attr($rows) . '" id="mt-' . esc_attr($key) . '" name="mt_' . esc_attr($key) . '">' . esc_textarea($value) . '</textarea>';
        else echo '<input class="large-text" id="mt-' . esc_attr($key) . '" name="mt_' . esc_attr($key) . '" value="' . esc_attr($value) . '">';
        echo '</td></tr>';
    }
    echo '</table>';
}

function mirrortalk_knowledge_save($post_id) {
    if (wp_is_post_revision($post_id) || !isset($_POST['mirrortalk_knowledge_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['mirrortalk_knowledge_nonce'])), 'mirrortalk_knowledge_save') || !current_user_can('edit_post', $post_id)) return;
    foreach (mirrortalk_knowledge_fields() as $key => $label) {
        if (!array_key_exists('mt_' . $key, $_POST)) continue;
        $value = sanitize_textarea_field(wp_unslash($_POST['mt_' . $key]));
        if ($key === 'transcript_url') $value = esc_url_raw($value);
        if ($key === 'last_reviewed' && $value && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $value)) $value = '';
        $value === '' ? delete_post_meta($post_id, '_mt_' . $key) : update_post_meta($post_id, '_mt_' . $key, $value);
    }
    delete_transient('mirrortalk_command_centre');
}
add_action('save_post', 'mirrortalk_knowledge_save', 40);

function mirrortalk_knowledge_profile($post_id) {
    $post = get_post($post_id); if (!$post || $post->post_status !== 'publish') return array();
    $get = function ($key) use ($post_id) { return trim((string) get_post_meta($post_id, '_mt_' . $key, true)); };
    $summary = $get('editorial_summary');
    if (!$summary) $summary = has_excerpt($post_id) ? get_the_excerpt($post_id) : wp_trim_words(wp_strip_all_tags(strip_shortcodes($post->post_content)), 45, '…');
    $topics = wp_get_post_terms($post_id, array('category','post_tag'), array('fields' => 'names'));
    if (is_wp_error($topics)) $topics = array();
    $questions = mirrortalk_knowledge_lines($get('key_questions'));
    if (!$questions && preg_match_all('/<h[2-4][^>]*>([^<]*\?)<\/h[2-4]>/i', $post->post_content, $matches)) $questions = array_slice(array_map('sanitize_text_field', $matches[1]), 0, 10);
    $quotes = mirrortalk_knowledge_lines($get('quotable_insights'));
    if (!$quotes && preg_match_all('/<blockquote[^>]*>.*?<p[^>]*>(.*?)<\/p>.*?<\/blockquote>/is', $post->post_content, $matches)) $quotes = array_slice(array_map(function ($value) { return sanitize_text_field(wp_strip_all_tags($value)); }, $matches[1]), 0, 8);
    return array(
        'id' => (int) $post_id, 'url' => get_permalink($post_id), 'title' => get_the_title($post_id),
        'summary' => $summary, 'guest' => $get('guest_name'), 'guest_bio' => $get('guest_bio'),
        'guest_expertise' => array_values(array_filter(array_map('trim', explode(',', $get('guest_expertise'))))),
        'topics' => array_values($topics), 'questions' => $questions, 'quotes' => $quotes,
        'moments' => mirrortalk_knowledge_lines($get('key_moments')), 'sources' => mirrortalk_knowledge_lines($get('sources'), true),
        'transcript' => esc_url_raw($get('transcript_url')), 'reviewed_by' => $get('reviewed_by'),
        'last_reviewed' => $get('last_reviewed'), 'correction' => $get('correction_note'),
        'author' => get_the_author_meta('display_name', (int) $post->post_author),
        'published' => get_the_date(DATE_W3C, $post_id), 'modified' => get_the_modified_date(DATE_W3C, $post_id),
    );
}

function mirrortalk_knowledge_graph($limit = 200) {
    $ids = get_posts(array('post_type' => 'post', 'post_status' => 'publish', 'numberposts' => min(500, absint($limit)), 'fields' => 'ids', 'orderby' => 'date', 'order' => 'DESC'));
    $episodes = array_map('mirrortalk_knowledge_profile', $ids); $entities = array(); $relations = array();
    foreach ($episodes as $episode) {
        if (!empty($episode['guest'])) { $key = 'guest:' . sanitize_title($episode['guest']); $entities[$key] = array('type' => 'Person', 'name' => $episode['guest'], 'bio' => $episode['guest_bio'], 'expertise' => $episode['guest_expertise']); $relations[] = array('from' => $episode['id'], 'to' => $key, 'relation' => 'features'); }
        foreach ($episode['topics'] as $topic) { $key = 'topic:' . sanitize_title($topic); $entities[$key] = array('type' => 'Topic', 'name' => $topic); $relations[] = array('from' => $episode['id'], 'to' => $key, 'relation' => 'about'); }
        foreach ($episode['questions'] as $question) { $key = 'question:' . hash('sha256', $question); $entities[$key] = array('type' => 'Question', 'text' => $question); $relations[] = array('from' => $episode['id'], 'to' => $key, 'relation' => 'answers'); }
        foreach ($episode['quotes'] as $quote) { $key = 'insight:' . hash('sha256', $quote); $entities[$key] = array('type' => 'QuotableInsight', 'text' => $quote); $relations[] = array('from' => $episode['id'], 'to' => $key, 'relation' => 'contains'); }
        foreach ($episode['moments'] as $moment) { $key = 'moment:' . hash('sha256', $moment); $entities[$key] = array('type' => 'KeyMoment', 'text' => $moment); $relations[] = array('from' => $episode['id'], 'to' => $key, 'relation' => 'hasPart'); }
        if ($episode['transcript']) { $key = 'transcript:' . hash('sha256', $episode['transcript']); $entities[$key] = array('type' => 'Transcript', 'url' => $episode['transcript']); $relations[] = array('from' => $episode['id'], 'to' => $key, 'relation' => 'transcribedBy'); }
        foreach ($episode['sources'] as $source) { $key = 'resource:' . hash('sha256', $source); $entities[$key] = array('type' => 'Resource', 'url' => $source); $relations[] = array('from' => $episode['id'], 'to' => $key, 'relation' => 'cites'); }
    }
    return array('generated_at' => gmdate('c'), 'episodes' => $episodes, 'entities' => $entities, 'relationships' => $relations);
}

add_action('rest_api_init', function () {
    register_rest_route('mirror-talk/v1', '/knowledge-graph', array('methods' => WP_REST_Server::READABLE, 'permission_callback' => '__return_true', 'callback' => function () { return rest_ensure_response(mirrortalk_knowledge_graph()); }));
    register_rest_route('mirror-talk/v1', '/ai-citations', array(
        array('methods' => WP_REST_Server::READABLE, 'permission_callback' => function () { return current_user_can('manage_mirrortalk_seo'); }, 'callback' => function () { return rest_ensure_response((array) get_option('mirrortalk_ai_citation_checks', array())); }),
        array('methods' => WP_REST_Server::CREATABLE, 'permission_callback' => function () { return current_user_can('manage_mirrortalk_seo'); }, 'callback' => function ($request) {
            $clean=array(); foreach(array_slice((array)$request->get_json_params(),0,5000) as $row){$url=esc_url_raw($row['url']??'');if(!$url||wp_parse_url($url,PHP_URL_HOST)!==wp_parse_url(home_url('/'),PHP_URL_HOST))continue;$clean[]=array('checked_at'=>sanitize_text_field($row['checked_at']??gmdate('c')),'provider'=>sanitize_text_field($row['provider']??''),'query'=>sanitize_text_field($row['query']??''),'url'=>$url,'cited'=>!empty($row['cited']),'position'=>max(0,(int)($row['position']??0)));} update_option('mirrortalk_ai_citation_checks',$clean,false);delete_transient('mirrortalk_command_centre');return rest_ensure_response(array('stored'=>count($clean))); }),
    ));
});

add_filter('mirrortalk_schema_graph', function ($schema) {
    if (!is_singular('post')) return $schema;
    $profile = mirrortalk_knowledge_profile(get_queried_object_id()); if (!$profile) return $schema;
    foreach ($schema['@graph'] as &$node) {
        if (!in_array('PodcastEpisode', (array) ($node['@type'] ?? array()), true)) continue;
        if ($profile['guest']) $node['about'][] = array('@type' => 'Person', 'name' => $profile['guest'], 'description' => $profile['guest_bio'] ?: null, 'knowsAbout' => $profile['guest_expertise']);
        if ($profile['topics']) $node['about'] = array_merge((array) ($node['about'] ?? array()), array_map(function ($topic) { return array('@type' => 'Thing', 'name' => $topic); }, $profile['topics']));
        if ($profile['questions']) $node['abstract'] = implode(' ', $profile['questions']);
        if ($profile['transcript']) $node['subjectOf'] = array('@type' => 'CreativeWork', 'name' => 'Verified transcript', 'url' => $profile['transcript']);
        if ($profile['sources']) $node['citation'] = $profile['sources'];
        $node = array_filter($node, function ($value) { return $value !== null && $value !== array() && $value !== ''; });
    }
    unset($node); return $schema;
}, 30);

function mirrortalk_related_posts($post_id, $limit = 3) {
    $tax_query = array('relation' => 'OR');
    foreach (array('category', 'post_tag') as $taxonomy) {
        $terms = wp_get_post_terms($post_id, $taxonomy, array('fields' => 'ids'));
        if (!is_wp_error($terms) && $terms) $tax_query[] = array('taxonomy' => $taxonomy, 'field' => 'term_id', 'terms' => $terms, 'operator' => 'IN');
    }
    $args = array('post_type' => 'post', 'post_status' => 'publish', 'post__not_in' => array($post_id), 'numberposts' => $limit, 'orderby' => 'date');
    if (count($tax_query) > 1) $args['tax_query'] = $tax_query;
    return get_posts($args);
}

function mirrortalk_render_citation_brief($post_id) {
    $profile = mirrortalk_knowledge_profile($post_id); if (!$profile) return;
    $related = mirrortalk_related_posts($post_id);
    $has_brief = $profile['questions'] || $profile['moments'] || $profile['quotes'] || $profile['sources'] || $profile['guest'];
    if (!$has_brief && !$related) return;
    echo '<aside class="mt-citation-brief mt-reading__shell" aria-labelledby="mt-citation-title" data-mt-knowledge-post="' . esc_attr($post_id) . '"><p class="mt-section-kicker">' . esc_html__('Source guide', 'astra-child') . '</p><h2 id="mt-citation-title">' . esc_html__('Continue with confidence', 'astra-child') . '</h2>';
    if ($profile['summary']) echo '<p class="mt-citation-brief__summary">' . esc_html($profile['summary']) . '</p>';
    if ($profile['guest']) echo '<p><strong>' . esc_html__('Guest:', 'astra-child') . '</strong> ' . esc_html($profile['guest']) . ($profile['guest_bio'] ? ' — ' . esc_html($profile['guest_bio']) : '') . '</p>';
    foreach (array('questions' => __('Questions answered', 'astra-child'), 'moments' => __('Key moments', 'astra-child'), 'quotes' => __('Quotable insights', 'astra-child')) as $key => $label) if ($profile[$key]) { echo '<h3>' . esc_html($label) . '</h3><ul>'; foreach ($profile[$key] as $item) echo '<li>' . esc_html($item) . '</li>'; echo '</ul>'; }
    if ($profile['sources']) { echo '<h3>' . esc_html__('Sources and resources', 'astra-child') . '</h3><ul>'; foreach ($profile['sources'] as $source) echo '<li><a href="' . esc_url($source) . '" rel="noopener noreferrer">' . esc_html(wp_parse_url($source, PHP_URL_HOST) ?: $source) . '</a></li>'; echo '</ul>'; }
    if ($profile['reviewed_by'] || $profile['last_reviewed']) echo '<p class="mt-citation-brief__review">' . esc_html(sprintf(__('Editorially reviewed%s%s.', 'astra-child'), $profile['reviewed_by'] ? ' by ' . $profile['reviewed_by'] : '', $profile['last_reviewed'] ? ' on ' . $profile['last_reviewed'] : '')) . '</p>';
    if ($profile['correction']) echo '<p class="mt-citation-brief__correction"><strong>' . esc_html__('Correction:', 'astra-child') . '</strong> ' . esc_html($profile['correction']) . '</p>';
    if ($related) { echo '<h3>' . esc_html__('Related conversations', 'astra-child') . '</h3><div class="mt-citation-brief__related" data-mt-personalized-related>'; foreach ($related as $item) echo '<a href="' . esc_url(get_permalink($item)) . '" data-post-id="' . esc_attr($item->ID) . '"><span>' . esc_html(get_the_title($item)) . '</span><small>' . esc_html__('Read next', 'astra-child') . ' →</small></a>'; echo '</div><p class="mt-citation-brief__reason" data-mt-personalization-reason hidden></p>'; }
    echo '</aside>';
}

function mirrortalk_command_post_metrics($post_id, $days = 30) {
    global $wpdb; $url = get_permalink($post_id); $path = (string) wp_parse_url($url, PHP_URL_PATH); $start = gmdate('Y-m-d H:i:s', time() - $days * DAY_IN_SECONDS);
    $metrics = array('google_impressions'=>0,'google_clicks'=>0,'google_position'=>0,'bing_impressions'=>0,'bing_clicks'=>0,'views'=>0,'engaged'=>0,'plays'=>0,'completions'=>0,'conversions'=>0,'ai_referrals'=>0,'ai_citations'=>0,'search_questions'=>array());
    $positions = array('google'=>array(0,0),'bing'=>array(0,0));
    foreach ((array) get_option('mirrortalk_search_performance', array()) as $row) {
        $engine = ($row['engine'] ?? '') === 'bing' ? 'bing' : 'google';
        $page_matches = !empty($row['page']) && mirrortalk_learning_url($row['page']) === mirrortalk_learning_url($url);
        $query_matches = $engine === 'bing' && empty($row['page']) && function_exists('mirrortalk_learning_query_eligible') && mirrortalk_learning_query_eligible($row['query'] ?? '', $post_id);
        if (!$page_matches && !$query_matches) continue; $imp = (int) ($row['impressions'] ?? 0);
        $metrics[$engine . '_impressions'] += $imp; $metrics[$engine . '_clicks'] += (int) ($row['clicks'] ?? 0); $positions[$engine][0] += (float) ($row['position'] ?? 0) * $imp; $positions[$engine][1] += $imp;
    }
    foreach (array('google','bing') as $engine) $metrics[$engine . '_position'] = $positions[$engine][1] ? round($positions[$engine][0] / $positions[$engine][1], 1) : 0;
    $table = function_exists('mirrortalk_intelligence_table') ? mirrortalk_intelligence_table() : '';
    if ($table) {
        $rows = $wpdb->get_results($wpdb->prepare("SELECT event_name, COUNT(*) total FROM {$table} WHERE occurred_at >= %s AND path=%s GROUP BY event_name", $start, $path), ARRAY_A);
        foreach ($rows as $row) { $map = array('site_page_view'=>'views','site_engaged'=>'engaged','podcast_play'=>'plays','podcast_complete'=>'completions','newsletter_subscribed'=>'conversions','contact_message_sent'=>'conversions'); if (isset($map[$row['event_name']])) $metrics[$map[$row['event_name']]] += (int) $row['total']; }
        $questions = $wpdb->get_col($wpdb->prepare("SELECT search_term FROM {$table} WHERE occurred_at >= %s AND event_name='internal_search' AND search_term<>'' ORDER BY occurred_at DESC LIMIT 50", $start));
        $metrics['search_questions'] = array_values(array_filter($questions, function ($question) use ($post_id) { return function_exists('mirrortalk_learning_query_eligible') && mirrortalk_learning_query_eligible($question, $post_id); }));
        $episode_rows = $wpdb->get_row($wpdb->prepare("SELECT SUM(event_name='podcast_play') plays, SUM(event_name='podcast_complete') completions FROM {$table} WHERE occurred_at >= %s AND episode_title=%s AND event_name IN ('podcast_play','podcast_complete')", $start, get_the_title($post_id)), ARRAY_A);
        if ($episode_rows) { $metrics['plays'] = max($metrics['plays'], (int) $episode_rows['plays']); $metrics['completions'] = max($metrics['completions'], (int) $episode_rows['completions']); }
    }
    if (function_exists('mirrortalk_ai_visibility_totals')) foreach ((array) (mirrortalk_ai_visibility_totals($days)['landing'] ?? array()) as $key => $count) {
        list($engine, $landing) = array_pad(explode('|', $key, 2), 2, '');
        if (untrailingslashit($landing) === untrailingslashit($path)) $metrics['ai_referrals'] += (int) $count;
    }
    foreach((array)get_option('mirrortalk_ai_citation_checks',array()) as $check)if(!empty($check['cited'])&&mirrortalk_learning_url($check['url']??'')===mirrortalk_learning_url($url))$metrics['ai_citations']++;
    return $metrics;
}

function mirrortalk_command_recommendations($days = 30, $force = false) {
    $cached = get_transient('mirrortalk_command_centre'); if (!$force && is_array($cached)) return $cached;
    $posts = get_posts(array('post_type'=>array('post','page'),'post_status'=>'publish','numberposts'=>120,'orderby'=>'modified','order'=>'DESC')); $queue = array();
    foreach ($posts as $post) {
        $m = mirrortalk_command_post_metrics($post->ID, $days); $analysis = function_exists('mirrortalk_seo_editorial_analysis') ? mirrortalk_seo_editorial_analysis($post) : array('score'=>0,'issues'=>array());
        $impressions = $m['google_impressions'] + $m['bing_impressions']; $clicks = $m['google_clicks'] + $m['bing_clicks']; $ctr = $impressions ? $clicks / $impressions : 0; $evidence = array(); $action = ''; $impact = 'Medium'; $score = 0;
        if ($impressions >= 100 && $ctr < .02 && $m['google_position'] > 0 && $m['google_position'] <= 15) { $action = __('Review the search title and description', 'astra-child'); $evidence[] = sprintf(__('%d Google/Bing impressions, %.1f%% CTR, Google position %.1f', 'astra-child'), $impressions, $ctr*100, $m['google_position']); if($m['ai_referrals'])$evidence[]=sprintf(__('%d observed AI-referred visits','astra-child'),$m['ai_referrals']); if($m['ai_citations'])$evidence[]=sprintf(__('%d authorized citation checks found this page','astra-child'),$m['ai_citations']); $impact='High'; $score=90 + min(9,(int)($impressions/500)); }
        elseif (!empty($m['search_questions'])) { $action = __('Answer the recurring internal-search question', 'astra-child'); $evidence[] = sprintf(__('%d consented internal searches surfaced an unanswered need', 'astra-child'), count($m['search_questions'])); $impact='High'; $score=86; }
        elseif (($analysis['score'] ?? 100) < 76) { $action = __('Strengthen structure, context and internal links', 'astra-child'); $evidence = array_slice((array) ($analysis['issues'] ?? array()),0,3); $score=75; }
        elseif ($m['views'] >= 10 && $m['engaged'] / max(1,$m['views']) < .25) { $action = __('Improve the opening and next-step guidance', 'astra-child'); $evidence[] = sprintf(__('%d views but only %d engaged visits', 'astra-child'),$m['views'],$m['engaged']); $score=72; }
        elseif ($m['plays'] >= 5 && $m['completions'] / max(1,$m['plays']) < .2) { $action = __('Review episode framing and listening hand-offs', 'astra-child'); $evidence[] = sprintf(__('%d starts and %d completions', 'astra-child'),$m['plays'],$m['completions']); $score=70; }
        if (!$action) continue;
        $queue[] = array('priority'=>$score,'content'=>get_the_title($post),'action'=>$action,'evidence'=>implode('; ',$evidence),'expected_impact'=>$impact,'url'=>get_edit_post_link($post->ID,''));
    }
    global $wpdb; $table = function_exists('mirrortalk_intelligence_table') ? mirrortalk_intelligence_table() : '';
    if ($table) {
        $start = gmdate('Y-m-d H:i:s', time() - $days * DAY_IN_SECONDS);
        $needs = $wpdb->get_results($wpdb->prepare("SELECT search_term, event_name, COUNT(*) total FROM {$table} WHERE occurred_at >= %s AND event_name IN ('internal_search','safe_topic_view') AND search_term<>'' GROUP BY search_term,event_name ORDER BY total DESC LIMIT 20", $start), ARRAY_A);
        foreach ($needs as $need) {
            $matched = false; foreach ($posts as $post) if (function_exists('mirrortalk_learning_query_eligible') && mirrortalk_learning_query_eligible($need['search_term'], $post->ID)) { $matched = true; break; }
            if (!$matched && (int) $need['total'] >= 2) $queue[] = array('priority'=>82,'content'=>__('Site-wide audience need','astra-child'),'action'=>__('Create or strengthen a topic page','astra-child'),'evidence'=>sprintf(__('%d consented signals for “%s” with no strong matching page','astra-child'),$need['total'],$need['search_term']),'expected_impact'=>'High','url'=>admin_url('post-new.php?post_type=page'));
        }
    }
    usort($queue,function($a,$b){return $b['priority']<=>$a['priority'];}); $queue=array_slice($queue,0,20); set_transient('mirrortalk_command_centre',$queue,6*HOUR_IN_SECONDS); return $queue;
}

function mirrortalk_quality_scan($force = false) {
    $cached = get_option('mirrortalk_quality_guardian', array()); if (!$force && !empty($cached['time']) && $cached['time'] > time()-12*HOUR_IN_SECONDS) return $cached;
    $posts=get_posts(array('post_type'=>array('post','page'),'post_status'=>'publish','numberposts'=>300)); $issues=array(); $inbound=array();
    foreach($posts as $post) if(preg_match_all('/href=["\']([^"\']+)["\']/i',$post->post_content,$links)) foreach($links[1] as $link){$id=url_to_postid($link);if($id)$inbound[$id]=($inbound[$id]??0)+1;}
    foreach($posts as $post){$plain=trim(wp_strip_all_tags(strip_shortcodes($post->post_content))); $word_count=str_word_count($plain); $h1=preg_match_all('/<h1\b/i',$post->post_content); $images=preg_match_all('/<img\b/i',$post->post_content);
        if(!$images&&!has_post_thumbnail($post->ID))$issues[]=array('severity'=>'medium','type'=>'missing_visual','content'=>get_the_title($post),'detail'=>__('No featured or in-content image.','astra-child'),'post_id'=>$post->ID);
        if($h1)$issues[]=array('severity'=>'high','type'=>'duplicate_h1','content'=>get_the_title($post),'detail'=>__('Body contains an H1; the presentation layer safely demotes it, but the source should be repaired.','astra-child'),'post_id'=>$post->ID);
        if($word_count<250)$issues[]=array('severity'=>'medium','type'=>'thin_content','content'=>get_the_title($post),'detail'=>sprintf(__('%d words; review whether it fully serves its purpose.','astra-child'),$word_count),'post_id'=>$post->ID);
        if($post->post_type==='post'&&strtotime($post->post_modified_gmt)<time()-2*YEAR_IN_SECONDS)$issues[]=array('severity'=>'low','type'=>'freshness','content'=>get_the_title($post),'detail'=>__('Not substantively reviewed in more than two years.','astra-child'),'post_id'=>$post->ID);
        if($post->post_type==='post'&&empty($inbound[$post->ID]))$issues[]=array('severity'=>'medium','type'=>'orphan','content'=>get_the_title($post),'detail'=>__('No contextual internal link was found to this post.','astra-child'),'post_id'=>$post->ID);
        if(preg_match('/<(?:table|iframe)[^>]+(?:width=["\']?\d{4,}|style=["\'][^"\']*width:\s*\d{4,}px)/i',$post->post_content))$issues[]=array('severity'=>'high','type'=>'mobile_overflow','content'=>get_the_title($post),'detail'=>__('A fixed-width embed or table may overflow mobile.','astra-child'),'post_id'=>$post->ID);
        if(preg_match('/<img\b(?![^>]*\balt=)[^>]*>/i',$post->post_content))$issues[]=array('severity'=>'high','type'=>'accessibility','content'=>get_the_title($post),'detail'=>__('An image is missing an alt attribute.','astra-child'),'post_id'=>$post->ID);
        if(preg_match('/<iframe\b(?![^>]*\btitle=)[^>]*>/i',$post->post_content))$issues[]=array('severity'=>'high','type'=>'accessibility','content'=>get_the_title($post),'detail'=>__('An embedded frame is missing an accessible title.','astra-child'),'post_id'=>$post->ID);
        if(preg_match('/<iframe[^>]+src=["\']http:\/\//i',$post->post_content))$issues[]=array('severity'=>'high','type'=>'broken_embed','content'=>get_the_title($post),'detail'=>__('An insecure embed may be blocked by modern browsers.','astra-child'),'post_id'=>$post->ID);
        $profile=mirrortalk_knowledge_profile($post->ID); if(!$profile||!wp_json_encode($profile))$issues[]=array('severity'=>'high','type'=>'invalid_schema','content'=>get_the_title($post),'detail'=>__('The citation profile could not be encoded safely.','astra-child'),'post_id'=>$post->ID);
        if(function_exists('mirrortalk_learning_metrics')){$recent=mirrortalk_learning_metrics(get_permalink($post),gmdate('Y-m-d',strtotime('-17 days')),gmdate('Y-m-d',strtotime('-3 days')));$prior=mirrortalk_learning_metrics(get_permalink($post),gmdate('Y-m-d',strtotime('-31 days')),gmdate('Y-m-d',strtotime('-18 days')));if(($prior['impressions']??0)>=50&&($recent['impressions']??0)<$prior['impressions']*.7)$issues[]=array('severity'=>'medium','type'=>'declining_search','content'=>get_the_title($post),'detail'=>sprintf(__('Search impressions declined from %d to %d across comparable 14-day windows.','astra-child'),$prior['impressions'],$recent['impressions']),'post_id'=>$post->ID);}
    }
    foreach((array)get_option('mirrortalk_link_health',array()) as $row)if(function_exists('mirrortalk_seo_link_state')&&mirrortalk_seo_link_state($row)==='broken')$issues[]=array('severity'=>'high','type'=>'broken_link','content'=>$row['source']??'','detail'=>$row['url']??'','post_id'=>url_to_postid($row['source']??''));
    if(function_exists('mirrortalk_intelligence_table')){
        global $wpdb; $table=mirrortalk_intelligence_table(); $slow=$wpdb->get_results("SELECT path,metric,ROUND(AVG(metric_value),0) average,COUNT(*) samples FROM {$table} WHERE event_name='web_vital' AND occurred_at>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 30 DAY) GROUP BY path,metric HAVING (metric='LCP' AND average>4000) OR (metric='INP' AND average>500) OR (metric='CLS' AND average>250)",ARRAY_A);
        foreach($slow as $row)$issues[]=array('severity'=>'high','type'=>'slow_template','content'=>$row['path'],'detail'=>sprintf(__('%s averages %sms across %d consented samples.','astra-child'),$row['metric'],$row['average'],$row['samples']),'post_id'=>url_to_postid(home_url($row['path'])));
    }
    foreach(mirrortalk_quality_runtime_probe($force) as $probe)if(($probe['state']??'')==='broken')$issues[]=array('severity'=>'high','type'=>'runtime_failure','content'=>$probe['label'],'detail'=>$probe['detail'],'post_id'=>0);
    usort($issues,function($a,$b){$rank=array('high'=>3,'medium'=>2,'low'=>1);return ($rank[$b['severity']]??0)<=>($rank[$a['severity']]??0);});
    $result=array('time'=>time(),'checked'=>count($posts),'issues'=>array_slice($issues,0,500),'counts'=>array_count_values(array_column($issues,'severity'))); update_option('mirrortalk_quality_guardian',$result,false); return $result;
}

function mirrortalk_quality_runtime_probe($force = false) {
    $cached=(array)get_option('mirrortalk_quality_runtime',array()); if(!$force&&!empty($cached['time'])&&$cached['time']>time()-12*HOUR_IN_SECONDS)return (array)($cached['checks']??array());
    $targets=array(
        array('label'=>'Homepage and persistent player','url'=>home_url('/'),'marker'=>'mt-listen'),
        array('label'=>'Blog archive','url'=>home_url('/blog/'),'marker'=>'<main'),
        array('label'=>'Ask Mirror Talk','url'=>home_url('/ask-mirror-talk/'),'marker'=>'ask-mirror-talk'),
        array('label'=>'Contact form','url'=>home_url('/contact/'),'marker'=>'data-mt-contact-form'),
        array('label'=>'Release manifest','url'=>home_url('/mirror-talk-release.json'),'marker'=>'release'),
    ); $checks=array();
    foreach($targets as $target){$response=wp_remote_get($target['url'],array('timeout'=>15,'redirection'=>3,'user-agent'=>'MirrorTalkQualityGuardian/1.0'));if(is_wp_error($response)){$checks[]=array('label'=>$target['label'],'state'=>'unverified','detail'=>$response->get_error_message());continue;}$code=(int)wp_remote_retrieve_response_code($response);$body=(string)wp_remote_retrieve_body($response);$ok=$code===200&&strpos($body,$target['marker'])!==false;$checks[]=array('label'=>$target['label'],'state'=>$ok?'healthy':'broken','detail'=>$ok?__('HTTP 200 and expected marker present.','astra-child'):sprintf(__('HTTP %d or expected component marker missing.','astra-child'),$code));}
    update_option('mirrortalk_quality_runtime',array('time'=>time(),'checks'=>$checks),false);return $checks;
}
add_action('mirrortalk_quality_guardian_daily',function(){if(function_exists('mirrortalk_seo_crawl'))mirrortalk_seo_crawl();if(function_exists('mirrortalk_seo_repair_media'))mirrortalk_seo_repair_media();mirrortalk_quality_scan(true);mirrortalk_command_recommendations(30,true);});
add_action('init',function(){if(!wp_next_scheduled('mirrortalk_quality_guardian_daily'))wp_schedule_event(time()+2*HOUR_IN_SECONDS,'daily','mirrortalk_quality_guardian_daily');});
add_action('switch_theme',function(){wp_clear_scheduled_hook('mirrortalk_quality_guardian_daily');});

function mirrortalk_command_centre_panels($days) {
    $queue=mirrortalk_command_recommendations($days); $graph=mirrortalk_knowledge_graph(); $quality=mirrortalk_quality_scan();
    echo '<section id="command-centre" class="mti-panel"><header><div><p class="mti-kicker">CONTENT COMMAND CENTRE</p><h2>' . esc_html__('What deserves attention next', 'astra-child') . '</h2><p>' . esc_html__('Ranked from verified search data, consented engagement, listening, conversions and editorial quality. Recommendations are evidence—not autonomous editorial claims.', 'astra-child') . '</p></div><form method="post" action="' . esc_url(admin_url('admin-post.php')) . '"><input type="hidden" name="action" value="mirrortalk_quality_run">'; wp_nonce_field('mirrortalk_quality_run'); submit_button(__('Refresh intelligence', 'astra-child'),'secondary','submit',false); echo '</form></header>';
    mirrortalk_intelligence_table_view($queue,array('priority'=>'Score','content'=>'Content','action'=>'Recommended action','evidence'=>'Evidence','expected_impact'=>'Expected impact')); echo '</section>';
    echo '<section id="knowledge" class="mti-panel"><header><div><p class="mti-kicker">KNOWLEDGE GRAPH</p><h2>' . esc_html__('Connected podcast authority', 'astra-child') . '</h2></div></header><div class="mti-cards mti-cards--compact"><article><small>Episodes</small><strong>' . esc_html(count($graph['episodes'])) . '</strong></article><article><small>Entities</small><strong>' . esc_html(count($graph['entities'])) . '</strong></article><article><small>Relationships</small><strong>' . esc_html(count($graph['relationships'])) . '</strong></article></div><p>' . esc_html__('Guest biographies, expertise, quotations and sources appear only when explicitly verified by an editor. Categories, tags and public links create the remaining relationships automatically.', 'astra-child') . '</p></section>';
    $rows=array(); foreach(array_slice($quality['issues'],0,100) as $item)$rows[]=array('severity'=>ucfirst($item['severity']),'type'=>str_replace('_',' ',$item['type']),'content'=>$item['content'],'detail'=>$item['detail']);
    echo '<section id="quality" class="mti-panel"><header><div><p class="mti-kicker">CONTINUOUS QUALITY GUARDIAN</p><h2>' . esc_html__('Editorial and technical release gate', 'astra-child') . '</h2><p>' . esc_html(sprintf(__('%d public documents checked. Last completed %s.','astra-child'),$quality['checked']??0,wp_date('j M Y H:i',$quality['time']??time()))) . '</p></div></header>'; mirrortalk_intelligence_table_view($rows,array('severity'=>'Severity','type'=>'Check','content'=>'Content','detail'=>'Evidence')); echo '</section>';
}

add_action('admin_post_mirrortalk_quality_run',function(){if(!current_user_can('manage_mirrortalk_seo'))wp_die(esc_html__('You cannot run this audit.','astra-child'));check_admin_referer('mirrortalk_quality_run');mirrortalk_quality_scan(true);mirrortalk_command_recommendations(30,true);wp_safe_redirect(admin_url('admin.php?page=mirror-talk-intelligence#command-centre'));exit;});

function mirrortalk_create_trust_pages() {
    if(get_option('mirrortalk_trust_pages_version')===MIRRORTALK_KNOWLEDGE_VERSION)return;
    $pages=array(
        'editorial-standards'=>array('title'=>'Editorial standards','content'=>'<!-- mirror-talk:managed-trust-page --><h1>Editorial standards</h1><p>Mirror Talk publishes original conversations and editorial material intended to support reflection, learning and personal growth.</p><h2>Accuracy and attribution</h2><p>Guest statements are attributed to their speakers. Quotations, credentials and sources are published only when they can be verified. Automated tools may assist organisation and quality checks, but do not invent editorial facts.</p><h2>Independence and safety</h2><p>Editorial decisions are made for listeners and readers, not to manipulate search rankings. Reflective content is not a substitute for professional medical, legal, mental-health or emergency support.</p><h2>Corrections</h2><p>Material corrections are recorded on the affected page. Readers may report an issue through the <a href="' . esc_url(home_url('/contact/')) . '">contact page</a>.</p>'),
        'corrections'=>array('title'=>'Corrections','content'=>'<!-- mirror-talk:managed-trust-page --><h1>Corrections</h1><p>Mirror Talk welcomes specific, evidence-based correction requests. Please identify the page, the statement concerned and a reliable supporting source through our <a href="' . esc_url(home_url('/contact/')) . '">contact page</a>.</p><p>When a material correction is confirmed, the page is updated and a dated correction note is shown where readers can understand what changed.</p>'),
    );
    foreach($pages as $slug=>$data){$existing=get_page_by_path($slug);if(!$existing){$id=wp_insert_post(array('post_type'=>'page','post_status'=>'publish','post_name'=>$slug,'post_title'=>$data['title'],'post_content'=>$data['content'],'post_author'=>get_current_user_id()?:1));if($id&&!is_wp_error($id))update_post_meta($id,'_mirrortalk_managed_trust_page','1');}}
    update_option('mirrortalk_trust_pages_version',MIRRORTALK_KNOWLEDGE_VERSION,false);
}
add_action('admin_init','mirrortalk_create_trust_pages',20);

add_action('wp_enqueue_scripts',function(){if(!is_singular('post'))return;wp_enqueue_script('mirror-talk-knowledge',get_stylesheet_directory_uri().'/knowledge.js',array(),function_exists('mirrortalk_asset_version')?mirrortalk_asset_version('knowledge.js'):wp_get_theme()->get('Version'),true);$profile=mirrortalk_knowledge_profile(get_queried_object_id());$blocked='/\b(?:health|healing|faith|religion|trauma|grief|anxiety|depression|sexuality|politics)\b/i';$safe=array_values(array_filter($profile['topics']??array(),function($topic)use($blocked){return !preg_match($blocked,$topic);}));wp_localize_script('mirror-talk-knowledge','MirrorTalkKnowledge',array('postId'=>get_queried_object_id(),'title'=>get_the_title(),'url'=>get_permalink(),'safeTopics'=>$safe));},30);
