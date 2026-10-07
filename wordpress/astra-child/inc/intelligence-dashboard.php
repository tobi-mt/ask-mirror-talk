<?php
/**
 * Mirror Talk Intelligence — first-party collection and reporting.
 *
 * Stores only allow-listed, consent-approved product events. Visitor IDs are
 * irreversibly hashed; raw IP addresses, page contents and reflection text are
 * never stored.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_INTELLIGENCE_DB_VERSION', '1.1.0');

function mirrortalk_intelligence_table() {
    global $wpdb;
    return $wpdb->prefix . 'mirrortalk_intelligence_events';
}

function mirrortalk_intelligence_install() {
    if (get_option('mirrortalk_intelligence_db_version') === MIRRORTALK_INTELLIGENCE_DB_VERSION) return;
    global $wpdb;
    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    $charset = $wpdb->get_charset_collate();
    $table = mirrortalk_intelligence_table();
    dbDelta("CREATE TABLE {$table} (
        id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
        occurred_at datetime NOT NULL,
        event_date date NOT NULL,
        event_name varchar(80) NOT NULL,
        visitor_hash char(64) NOT NULL DEFAULT '',
        path varchar(500) NOT NULL DEFAULT '',
        referrer_host varchar(191) NOT NULL DEFAULT '',
        campaign_source varchar(191) NOT NULL DEFAULT '',
        campaign_medium varchar(100) NOT NULL DEFAULT '',
        campaign_name varchar(191) NOT NULL DEFAULT '',
        entry_path varchar(500) NOT NULL DEFAULT '',
        previous_path varchar(500) NOT NULL DEFAULT '',
        destination_path varchar(500) NOT NULL DEFAULT '',
        device_class varchar(20) NOT NULL DEFAULT '',
        is_returning tinyint(1) unsigned NOT NULL DEFAULT 0,
        country char(2) NOT NULL DEFAULT '',
        language varchar(20) NOT NULL DEFAULT '',
        episode_id varchar(191) NOT NULL DEFAULT '',
        episode_title varchar(500) NOT NULL DEFAULT '',
        progress_bucket smallint unsigned NOT NULL DEFAULT 0,
        metric varchar(30) NOT NULL DEFAULT '',
        metric_value decimal(14,3) NOT NULL DEFAULT 0,
        rating varchar(30) NOT NULL DEFAULT '',
        target varchar(700) NOT NULL DEFAULT '',
        status varchar(80) NOT NULL DEFAULT '',
        PRIMARY KEY  (id),
        KEY event_date (event_date),
        KEY event_name_date (event_name,event_date),
        KEY path_date (path(150),event_date),
        KEY episode_date (episode_title(150),event_date),
        KEY visitor_date (visitor_hash,event_date)
    ) {$charset};");
    if ($wpdb->get_var($wpdb->prepare('SHOW TABLES LIKE %s', $table)) === $table) update_option('mirrortalk_intelligence_db_version', MIRRORTALK_INTELLIGENCE_DB_VERSION, false);
}
add_action('after_switch_theme', 'mirrortalk_intelligence_install', 30);
add_action('admin_init', 'mirrortalk_intelligence_install', 5);

function mirrortalk_intelligence_allowed_events() {
    return array(
        'site_page_view', 'site_engaged', 'site_outbound_click', 'site_internal_journey',
        'podcast_play', 'podcast_pause', 'podcast_progress', 'podcast_complete', 'episode_discovered',
        'web_vital', 'broken_link_seen', 'newsletter_subscribed', 'contact_message_sent',
        'living_mirror_reflection_saved', 'youtube_module_viewable', 'youtube_media_allowed',
        'youtube_video_ready', 'youtube_video_start', 'youtube_video_progress', 'youtube_video_complete',
        'youtube_video_unmuted', 'youtube_video_muted', 'youtube_autoplay_blocked',
        'youtube_autoplay_fallback', 'youtube_video_error', 'youtube_api_error',
    );
}

function mirrortalk_intelligence_clean_path($value) {
    $path = (string) wp_parse_url((string) $value, PHP_URL_PATH);
    return substr(sanitize_text_field($path ?: '/'), 0, 500);
}

function mirrortalk_intelligence_country() {
    foreach (array('HTTP_CF_IPCOUNTRY', 'HTTP_CLOUDFRONT_VIEWER_COUNTRY', 'HTTP_X_COUNTRY_CODE') as $header) {
        $value = strtoupper(sanitize_text_field((string) ($_SERVER[$header] ?? '')));
        if (preg_match('/^[A-Z]{2}$/', $value) && $value !== 'XX') return $value;
    }
    return '';
}

function mirrortalk_intelligence_same_origin() {
    $site_host = strtolower((string) wp_parse_url(home_url('/'), PHP_URL_HOST));
    $origin = (string) get_http_origin();
    $referer = wp_get_referer();
    $candidate = $origin ?: $referer;
    return $candidate && strtolower((string) wp_parse_url($candidate, PHP_URL_HOST)) === $site_host;
}

function mirrortalk_intelligence_rate_limited() {
    $raw = (string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown');
    $key = 'mt_intel_rate_' . substr(hash_hmac('sha256', $raw, wp_salt('nonce')), 0, 32);
    $count = (int) get_transient($key);
    if ($count >= 120) return true;
    set_transient($key, $count + 1, MINUTE_IN_SECONDS);
    return false;
}

function mirrortalk_intelligence_collect(WP_REST_Request $request) {
    if (!mirrortalk_intelligence_same_origin()) return new WP_Error('invalid_origin', __('Analytics origin was not accepted.', 'astra-child'), array('status' => 403));
    if (mirrortalk_intelligence_rate_limited()) return new WP_Error('rate_limited', __('Analytics rate limit reached.', 'astra-child'), array('status' => 429));
    $body = (array) $request->get_json_params();
    $event = sanitize_key($body['event_name'] ?? '');
    if (!in_array($event, mirrortalk_intelligence_allowed_events(), true)) return new WP_Error('invalid_event', __('Unsupported analytics event.', 'astra-child'), array('status' => 400));
    $meta = is_array($body['metadata'] ?? null) ? $body['metadata'] : array();
    $device_id = substr(sanitize_text_field((string) ($meta['device_id'] ?? '')), 0, 100);
    $visitor = $device_id ? hash_hmac('sha256', $device_id, wp_salt('auth')) : '';
    $clean = function ($key, $limit = 191) use ($meta) { return substr(sanitize_text_field((string) ($meta[$key] ?? '')), 0, $limit); };
    global $wpdb;
    $inserted = $wpdb->insert(mirrortalk_intelligence_table(), array(
        'occurred_at' => current_time('mysql', true), 'event_date' => current_time('Y-m-d', true),
        'event_name' => $event, 'visitor_hash' => $visitor,
        'path' => mirrortalk_intelligence_clean_path($meta['path'] ?? '/'),
        'referrer_host' => strtolower($clean('referrer_host')), 'campaign_source' => strtolower($clean('campaign_source')),
        'campaign_medium' => strtolower($clean('campaign_medium', 100)), 'campaign_name' => $clean('campaign_name'),
        'entry_path' => mirrortalk_intelligence_clean_path($meta['entry_path'] ?? ''),
        'previous_path' => mirrortalk_intelligence_clean_path($meta['previous_path'] ?? ''),
        'destination_path' => mirrortalk_intelligence_clean_path($meta['destination_path'] ?? ''),
        'device_class' => in_array(($meta['device_class'] ?? ''), array('mobile', 'tablet', 'desktop'), true) ? $meta['device_class'] : '',
        'is_returning' => filter_var($meta['returning'] ?? false, FILTER_VALIDATE_BOOLEAN) ? 1 : 0,
        'country' => mirrortalk_intelligence_country(), 'language' => $clean('language', 20),
        'episode_id' => $clean('episode_id'), 'episode_title' => $clean('episode_title', 500),
        'progress_bucket' => min(100, max(0, absint($meta['progress_bucket'] ?? 0))),
        'metric' => $clean('metric', 30), 'metric_value' => (float) ($meta['value'] ?? 0),
        'rating' => $clean('rating', 30), 'target' => esc_url_raw(substr((string) ($meta['target'] ?? ''), 0, 700)),
        'status' => $clean('status', 80),
    ));
    return $inserted ? rest_ensure_response(array('status' => 'ok')) : new WP_Error('store_failed', __('The analytics event could not be stored.', 'astra-child'), array('status' => 500));
}

add_action('rest_api_init', function () {
    register_rest_route('mirror-talk/v1', '/intelligence/event', array(
        'methods' => WP_REST_Server::CREATABLE, 'permission_callback' => '__return_true',
        'callback' => 'mirrortalk_intelligence_collect',
    ));
});

function mirrortalk_intelligence_period() {
    $days = absint($_GET['period'] ?? 30);
    return in_array($days, array(7, 30, 90, 365), true) ? $days : 30;
}

function mirrortalk_intelligence_bounds($days, $previous = false) {
    $end = time() - ($previous ? $days * DAY_IN_SECONDS : 0);
    $start = $end - $days * DAY_IN_SECONDS;
    return array(gmdate('Y-m-d H:i:s', $start), gmdate('Y-m-d H:i:s', $end));
}

function mirrortalk_intelligence_event_total($events, $days, $previous = false, $distinct = false) {
    global $wpdb;
    list($start, $end) = mirrortalk_intelligence_bounds($days, $previous);
    $events = array_values(array_intersect((array) $events, mirrortalk_intelligence_allowed_events()));
    if (!$events) return 0;
    $marks = implode(',', array_fill(0, count($events), '%s'));
    $select = $distinct ? "COUNT(DISTINCT NULLIF(visitor_hash,''))" : 'COUNT(*)';
    $sql = "SELECT {$select} FROM " . mirrortalk_intelligence_table() . " WHERE occurred_at >= %s AND occurred_at < %s AND event_name IN ({$marks})";
    return (int) $wpdb->get_var($wpdb->prepare($sql, array_merge(array($start, $end), $events)));
}

function mirrortalk_intelligence_group($select, $group, $where, $days, $limit = 20, $previous = false) {
    global $wpdb;
    list($start, $end) = mirrortalk_intelligence_bounds($days, $previous);
    $limit = min(100, max(1, absint($limit)));
    $sql = "SELECT {$select} FROM " . mirrortalk_intelligence_table() . " WHERE occurred_at >= %s AND occurred_at < %s AND {$where} GROUP BY {$group} ORDER BY total DESC LIMIT {$limit}";
    return $wpdb->get_results($wpdb->prepare($sql, $start, $end), ARRAY_A);
}

function mirrortalk_intelligence_search_snapshot($days, $previous = false) {
    list($start, $end) = mirrortalk_intelligence_bounds($days, $previous);
    $start = substr($start, 0, 10); $end = substr($end, 0, 10);
    $result = array('clicks' => 0, 'impressions' => 0, 'position_sum' => 0, 'position_rows' => 0, 'queries' => array());
    foreach ((array) get_option('mirrortalk_search_performance', array()) as $row) {
        $date = (string) ($row['date'] ?? ''); if ($date < $start || $date >= $end) continue;
        $result['clicks'] += (int) ($row['clicks'] ?? 0); $result['impressions'] += (int) ($row['impressions'] ?? 0);
        if (isset($row['position'])) { $result['position_sum'] += (float) $row['position']; $result['position_rows']++; }
        $query = trim((string) ($row['query'] ?? '')); if (!$query) continue;
        if (!isset($result['queries'][$query])) $result['queries'][$query] = array('query' => $query, 'clicks' => 0, 'impressions' => 0);
        $result['queries'][$query]['clicks'] += (int) ($row['clicks'] ?? 0); $result['queries'][$query]['impressions'] += (int) ($row['impressions'] ?? 0);
    }
    usort($result['queries'], function ($a, $b) { return $b['impressions'] <=> $a['impressions']; });
    $result['queries'] = array_slice($result['queries'], 0, 20);
    $result['position'] = $result['position_rows'] ? round($result['position_sum'] / $result['position_rows'], 1) : 0;
    return $result;
}

function mirrortalk_intelligence_snapshot($days = 30) {
    global $wpdb;
    $table = mirrortalk_intelligence_table();
    list($start, $end) = mirrortalk_intelligence_bounds($days);
    $totals = array(
        'page_views' => mirrortalk_intelligence_event_total(array('site_page_view'), $days),
        'visitors' => mirrortalk_intelligence_event_total(array('site_page_view'), $days, false, true),
        'plays' => mirrortalk_intelligence_event_total(array('podcast_play'), $days),
        'completions' => mirrortalk_intelligence_event_total(array('podcast_complete'), $days),
        'conversions' => mirrortalk_intelligence_event_total(array('newsletter_subscribed', 'contact_message_sent'), $days),
        'engaged' => mirrortalk_intelligence_event_total(array('site_engaged'), $days),
    );
    $previous = array(
        'page_views' => mirrortalk_intelligence_event_total(array('site_page_view'), $days, true),
        'visitors' => mirrortalk_intelligence_event_total(array('site_page_view'), $days, true, true),
        'plays' => mirrortalk_intelligence_event_total(array('podcast_play'), $days, true),
        'completions' => mirrortalk_intelligence_event_total(array('podcast_complete'), $days, true),
        'conversions' => mirrortalk_intelligence_event_total(array('newsletter_subscribed', 'contact_message_sent'), $days, true),
        'engaged' => mirrortalk_intelligence_event_total(array('site_engaged'), $days, true),
    );
    $bucket = $days <= 31 ? 'event_date' : ($days <= 90 ? "DATE_FORMAT(event_date,'%x-W%v')" : "DATE_FORMAT(event_date,'%Y-%m')");
    $daily = $wpdb->get_results($wpdb->prepare("SELECT {$bucket} label, COUNT(*) total FROM {$table} WHERE occurred_at >= %s AND occurred_at < %s AND event_name='site_page_view' GROUP BY {$bucket} ORDER BY MIN(event_date)", $start, $end), ARRAY_A);
    $vitals = $wpdb->get_results($wpdb->prepare("SELECT metric label, ROUND(AVG(metric_value),1) average, SUM(rating='good') good, SUM(rating='needs-improvement') needs_improvement, SUM(rating='poor') poor, COUNT(*) total FROM {$table} WHERE occurred_at >= %s AND occurred_at < %s AND event_name='web_vital' AND metric <> '' GROUP BY metric ORDER BY metric", $start, $end), ARRAY_A);
    $episodes = mirrortalk_intelligence_group("CASE WHEN episode_title='' THEN 'Unknown episode' ELSE episode_title END label, SUM(event_name='podcast_play') total, SUM(event_name='podcast_complete') secondary", "CASE WHEN episode_title='' THEN 'Unknown episode' ELSE episode_title END", "event_name IN ('podcast_play','podcast_complete')", $days);
    foreach ($episodes as &$episode) $episode['rate'] = !empty($episode['total']) ? round(((int) $episode['secondary'] / (int) $episode['total']) * 100, 1) . '%' : '0%';
    unset($episode);
    $snapshot = array(
        'days' => $days, 'totals' => $totals, 'previous' => $previous, 'daily' => $daily,
        'pages' => mirrortalk_intelligence_group("path label, COUNT(*) total, COUNT(DISTINCT NULLIF(visitor_hash,'')) secondary", 'path', "event_name='site_page_view' AND path <> ''", $days),
        'referrers' => mirrortalk_intelligence_group("CASE WHEN referrer_host='' OR referrer_host='direct' THEN 'Direct / unknown' ELSE referrer_host END label, COUNT(*) total", "CASE WHEN referrer_host='' OR referrer_host='direct' THEN 'Direct / unknown' ELSE referrer_host END", "event_name='site_page_view'", $days),
        'campaigns' => mirrortalk_intelligence_group("CASE WHEN campaign_source='' THEN 'Unattributed' ELSE CONCAT(campaign_source, IF(campaign_medium='', '', CONCAT(' / ', campaign_medium)), IF(campaign_name='', '', CONCAT(' / ', campaign_name))) END label, COUNT(*) total", "CASE WHEN campaign_source='' THEN 'Unattributed' ELSE CONCAT(campaign_source, IF(campaign_medium='', '', CONCAT(' / ', campaign_medium)), IF(campaign_name='', '', CONCAT(' / ', campaign_name))) END", "event_name='site_page_view'", $days),
        'episodes' => $episodes,
        'journeys' => mirrortalk_intelligence_group("CONCAT(previous_path, ' → ', destination_path) label, COUNT(*) total", 'previous_path,destination_path', "event_name='site_internal_journey' AND destination_path <> ''", $days),
        'devices' => mirrortalk_intelligence_group("CASE WHEN device_class='' THEN 'Unknown' ELSE device_class END label, COUNT(*) total", "CASE WHEN device_class='' THEN 'Unknown' ELSE device_class END", "event_name='site_page_view'", $days),
        'audience_type' => mirrortalk_intelligence_group("IF(is_returning=1, 'Returning', 'New') label, COUNT(*) total", 'is_returning', "event_name='site_page_view'", $days),
        'geography' => mirrortalk_intelligence_group("CASE WHEN country='' THEN 'Unknown' ELSE country END label, COUNT(*) total", "CASE WHEN country='' THEN 'Unknown' ELSE country END", "event_name='site_page_view'", $days),
        'conversions' => mirrortalk_intelligence_group("event_name label, COUNT(*) total", 'event_name', "event_name IN ('newsletter_subscribed','contact_message_sent')", $days),
        'broken' => mirrortalk_intelligence_group("CASE WHEN target='' THEN path ELSE target END label, COUNT(*) total, MAX(status) detail", "CASE WHEN target='' THEN path ELSE target END", "event_name='broken_link_seen'", $days),
        'vitals' => $vitals, 'search' => mirrortalk_intelligence_search_snapshot($days),
        'search_previous' => mirrortalk_intelligence_search_snapshot($days, true),
        'ai' => function_exists('mirrortalk_ai_visibility_totals') ? mirrortalk_ai_visibility_totals($days) : array(),
        'ai_readiness' => function_exists('mirrortalk_ai_readiness') ? mirrortalk_ai_readiness() : array('score' => 0, 'checks' => array()),
        'seo' => array('broken_links' => count(array_filter((array) get_option('mirrortalk_link_health', array()), function ($row) { return function_exists('mirrortalk_seo_link_state') ? mirrortalk_seo_link_state($row) === 'broken' : empty($row['status']) || (int) $row['status'] >= 400; })), 'redirects' => count((array) get_option('mirrortalk_redirects', array())), 'last_audit' => (array) get_option('mirrortalk_last_seo_audit', array())),
    );
    return $snapshot;
}

function mirrortalk_intelligence_change($current, $previous) {
    if (!$previous) return $current ? __('New activity', 'astra-child') : __('No activity', 'astra-child');
    $change = (($current - $previous) / $previous) * 100;
    return sprintf('%+.1f%%', $change);
}

function mirrortalk_intelligence_bar_chart($rows, $label) {
    $max = 0; foreach ($rows as $row) $max = max($max, (float) ($row['total'] ?? 0));
    echo '<div class="mti-chart" role="img" aria-label="' . esc_attr($label) . '">';
    if (!$rows) echo '<p class="mti-empty">' . esc_html__('No consent-approved data in this period yet.', 'astra-child') . '</p>';
    foreach ($rows as $row) { $value = (float) ($row['total'] ?? 0); $width = $max ? max(2, round($value / $max * 100, 1)) : 0; echo '<div class="mti-bar"><span>' . esc_html($row['label'] ?? '') . '</span><i><b style="width:' . esc_attr($width) . '%"></b></i><strong>' . esc_html(number_format_i18n($value)) . '</strong></div>'; }
    echo '</div>';
}

function mirrortalk_intelligence_table_view($rows, $columns) {
    if (!$rows) { echo '<p class="mti-empty">' . esc_html__('No data in this period yet.', 'astra-child') . '</p>'; return; }
    echo '<div class="mti-table-wrap"><table class="widefat striped mti-filterable"><thead><tr>'; foreach ($columns as $key => $label) echo '<th>' . esc_html($label) . '</th>'; echo '</tr></thead><tbody>';
    foreach ($rows as $row) { echo '<tr>'; foreach ($columns as $key => $label) echo '<td>' . esc_html((string) ($row[$key] ?? '—')) . '</td>'; echo '</tr>'; }
    echo '</tbody></table></div>';
}

function mirrortalk_intelligence_admin_menu() {
    add_menu_page(__('Mirror Talk Intelligence', 'astra-child'), __('Mirror Talk Intelligence', 'astra-child'), 'manage_mirrortalk_seo', 'mirror-talk-intelligence', 'mirrortalk_intelligence_admin_page', 'dashicons-chart-line', 4);
}
add_action('admin_menu', 'mirrortalk_intelligence_admin_menu');

function mirrortalk_intelligence_admin_page() {
    if (!current_user_can('manage_mirrortalk_seo')) return;
    $days = mirrortalk_intelligence_period(); $data = mirrortalk_intelligence_snapshot($days);
    $export_url = wp_nonce_url(add_query_arg(array('action' => 'mirrortalk_intelligence_export', 'period' => $days), admin_url('admin-post.php')), 'mirrortalk_intelligence_export');
    ?>
    <div class="wrap mti-wrap">
      <div class="mti-head"><div><p class="mti-kicker">MIRROR TALK</p><h1><?php esc_html_e('Intelligence', 'astra-child'); ?></h1><p><?php esc_html_e('Website, listening, discovery and performance signals—measured privately and interpreted together.', 'astra-child'); ?></p></div><div class="mti-actions"><form method="get"><input type="hidden" name="page" value="mirror-talk-intelligence"><label><?php esc_html_e('Period', 'astra-child'); ?> <select name="period" onchange="this.form.submit()"><?php foreach (array(7,30,90,365) as $period) echo '<option value="' . esc_attr($period) . '" ' . selected($days, $period, false) . '>' . esc_html($period . ' days') . '</option>'; ?></select></label></form><a class="button button-primary" href="<?php echo esc_url($export_url); ?>"><?php esc_html_e('Export complete CSV', 'astra-child'); ?></a></div></div>
      <div class="mti-notice"><strong><?php esc_html_e('Privacy-respecting by design.', 'astra-child'); ?></strong> <?php esc_html_e('Website analytics include only visitors who allowed insights. No raw IP addresses, questions, reflection text or email addresses are stored here.', 'astra-child'); ?></div>
      <div class="mti-cards">
      <?php foreach (array('page_views' => 'Page views', 'visitors' => 'Unique visitors', 'plays' => 'Podcast plays', 'completions' => 'Completions', 'conversions' => 'Conversions') as $key => $label) : ?><article><small><?php echo esc_html($label); ?></small><strong><?php echo esc_html(number_format_i18n($data['totals'][$key])); ?></strong><span><?php echo esc_html(mirrortalk_intelligence_change($data['totals'][$key], $data['previous'][$key])); ?> <?php esc_html_e('vs previous period', 'astra-child'); ?></span></article><?php endforeach; ?>
      <article><small><?php esc_html_e('Completion rate', 'astra-child'); ?></small><strong><?php echo esc_html($data['totals']['plays'] ? round($data['totals']['completions'] / $data['totals']['plays'] * 100, 1) : 0); ?>%</strong><span><?php esc_html_e('completed plays ÷ starts', 'astra-child'); ?></span></article></div>
      <nav class="mti-tabs" aria-label="Dashboard sections"><a href="#overview">Overview</a><a href="#audience">Audience</a><a href="#podcast">Podcast</a><a href="#search">Search &amp; SEO</a><a href="#ai">AI visibility</a><a href="#performance">Performance</a><a href="#learning">SEO learning</a><a href="#reports">Reports</a><label>Filter tables <input type="search" data-mti-filter placeholder="Find a page, episode or source"></label></nav>
      <section id="overview" class="mti-panel"><header><div><p class="mti-kicker">OVERVIEW</p><h2><?php esc_html_e('Audience movement', 'astra-child'); ?></h2></div></header><?php mirrortalk_intelligence_bar_chart($data['daily'], __('Daily page views', 'astra-child')); ?><div class="mti-grid"><div><h3><?php esc_html_e('Top pages', 'astra-child'); ?></h3><?php mirrortalk_intelligence_table_view($data['pages'], array('label' => 'Page', 'total' => 'Views', 'secondary' => 'Visitors')); ?></div><div><h3><?php esc_html_e('Journeys', 'astra-child'); ?></h3><?php mirrortalk_intelligence_table_view($data['journeys'], array('label' => 'Path transition', 'total' => 'Times')); ?></div></div></section>
      <section id="audience" class="mti-panel"><header><div><p class="mti-kicker">ACQUISITION &amp; AUDIENCE</p><h2><?php esc_html_e('How people arrive', 'astra-child'); ?></h2></div></header><div class="mti-grid mti-grid--3"><div><h3>Referrers</h3><?php mirrortalk_intelligence_table_view($data['referrers'], array('label' => 'Source', 'total' => 'Visits')); ?></div><div><h3>Campaigns</h3><?php mirrortalk_intelligence_table_view($data['campaigns'], array('label' => 'Source / medium / campaign', 'total' => 'Visits')); ?></div><div><h3>Conversions</h3><?php mirrortalk_intelligence_table_view($data['conversions'], array('label' => 'Action', 'total' => 'Total')); ?></div><div><h3>Devices</h3><?php mirrortalk_intelligence_bar_chart($data['devices'], 'Device distribution'); ?></div><div><h3>New and returning</h3><?php mirrortalk_intelligence_bar_chart($data['audience_type'], 'New and returning page views'); ?></div><div><h3>Geography</h3><?php mirrortalk_intelligence_table_view($data['geography'], array('label' => 'Country', 'total' => 'Views')); ?><p class="description">Country appears only when the hosting/CDN request supplies a country code; Mirror Talk does not perform IP geolocation.</p></div></div></section>
      <section id="podcast" class="mti-panel"><header><div><p class="mti-kicker">PODCAST</p><h2><?php esc_html_e('Listening performance', 'astra-child'); ?></h2></div></header><?php mirrortalk_intelligence_table_view($data['episodes'], array('label' => 'Episode', 'total' => 'Plays', 'secondary' => 'Completions', 'rate' => 'Completion rate')); ?></section>
      <section id="search" class="mti-panel"><header><div><p class="mti-kicker">SEARCH &amp; SEO</p><h2><?php esc_html_e('Organic discovery', 'astra-child'); ?></h2></div></header><div class="mti-cards mti-cards--compact"><article><small>Search clicks</small><strong><?php echo esc_html(number_format_i18n($data['search']['clicks'])); ?></strong><span><?php echo esc_html(mirrortalk_intelligence_change($data['search']['clicks'], $data['search_previous']['clicks'])); ?> vs previous</span></article><article><small>Impressions</small><strong><?php echo esc_html(number_format_i18n($data['search']['impressions'])); ?></strong><span><?php echo esc_html(mirrortalk_intelligence_change($data['search']['impressions'], $data['search_previous']['impressions'])); ?> vs previous</span></article><article><small>Average position</small><strong><?php echo esc_html($data['search']['position'] ?: '—'); ?></strong><span>Google + Bing rows</span></article><article><small>Broken links</small><strong><?php echo esc_html($data['seo']['broken_links']); ?></strong><span>latest crawler result</span></article><article><small>Redirects</small><strong><?php echo esc_html($data['seo']['redirects']); ?></strong><span>managed rules</span></article></div><?php mirrortalk_intelligence_table_view($data['search']['queries'], array('query' => 'Query', 'clicks' => 'Clicks', 'impressions' => 'Impressions')); ?></section>
      <section id="ai" class="mti-panel"><header><div><p class="mti-kicker">AI VISIBILITY</p><h2><?php esc_html_e('Discovery evidence', 'astra-child'); ?></h2></div></header><div class="mti-cards mti-cards--compact"><article><small>AI readiness</small><strong><?php echo esc_html($data['ai_readiness']['score']); ?>%</strong><span>technical and editorial checks</span></article><article><small>AI referrals</small><strong><?php echo esc_html(array_sum((array) ($data['ai']['referral'] ?? array()))); ?></strong><span>recognizable referrers</span></article><article><small>AI crawler observations</small><strong><?php echo esc_html(array_sum((array) ($data['ai']['crawler'] ?? array()))); ?></strong><span>recognized user agents</span></article></div><p class="description">These are discovery signals, not proof that an AI answer cited Mirror Talk.</p></section>
      <section id="performance" class="mti-panel"><header><div><p class="mti-kicker">PERFORMANCE &amp; QUALITY</p><h2><?php esc_html_e('Real visitor experience', 'astra-child'); ?></h2></div></header><?php mirrortalk_intelligence_table_view($data['vitals'], array('label' => 'Metric', 'average' => 'Average', 'good' => 'Good', 'needs_improvement' => 'Needs improvement', 'poor' => 'Poor', 'total' => 'Samples')); ?><h3>Broken-resource observations</h3><?php mirrortalk_intelligence_table_view($data['broken'], array('label' => 'Resource', 'detail' => 'Status', 'total' => 'Observations')); ?></section>
      <?php if (function_exists('mirrortalk_seo_learning_panel')) mirrortalk_seo_learning_panel(); ?>
      <section id="reports" class="mti-panel"><header><div><p class="mti-kicker">WEEKLY REPORTS</p><h2><?php esc_html_e('What changed and what needs attention', 'astra-child'); ?></h2></div><form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><input type="hidden" name="action" value="mirrortalk_intelligence_report_now"><?php wp_nonce_field('mirrortalk_intelligence_report_now'); ?><?php submit_button(__('Generate report now', 'astra-child'), 'secondary', 'submit', false); ?></form></header><?php $reports = array_reverse((array) get_option('mirrortalk_intelligence_weekly_reports', array())); if (!$reports) echo '<p class="mti-empty">The first report is generated by the existing weekly schedule. Current data is available above now.</p>'; foreach ($reports as $report) { echo '<details><summary><strong>' . esc_html(wp_date('j M Y', (int) ($report['time'] ?? time()))) . '</strong> — ' . esc_html(($report['page_views'] ?? 0) . ' views · ' . ($report['plays'] ?? 0) . ' plays · ' . ($report['issues'] ?? 0) . ' SEO issues') . '</summary><p>' . esc_html($report['summary'] ?? '') . '</p></details>'; } ?></section>
    </div>
    <?php
}

function mirrortalk_intelligence_export() {
    if (!current_user_can('manage_mirrortalk_seo')) wp_die(esc_html__('You cannot export this report.', 'astra-child'));
    check_admin_referer('mirrortalk_intelligence_export');
    $days = mirrortalk_intelligence_period(); $data = mirrortalk_intelligence_snapshot($days);
    nocache_headers(); header('Content-Type: text/csv; charset=UTF-8'); header('Content-Disposition: attachment; filename="mirror-talk-intelligence-' . gmdate('Y-m-d') . '.csv"');
    $out = fopen('php://output', 'w'); fputcsv($out, array('Mirror Talk Intelligence', $days . ' days')); fputcsv($out, array());
    foreach ($data['totals'] as $key => $value) fputcsv($out, array('summary', $key, $value, $data['previous'][$key] ?? 0));
    foreach (array('pages','referrers','campaigns','episodes','journeys','devices','audience_type','geography','conversions','vitals','broken') as $section) {
        fputcsv($out, array()); fputcsv($out, array(strtoupper($section)));
        if (!empty($data[$section])) { fputcsv($out, array_keys($data[$section][0])); foreach ($data[$section] as $row) fputcsv($out, $row); }
    }
    fputcsv($out, array()); fputcsv($out, array('SEARCH QUERIES')); fputcsv($out, array('query','clicks','impressions')); foreach ($data['search']['queries'] as $row) fputcsv($out, $row);
    fclose($out); exit;
}
add_action('admin_post_mirrortalk_intelligence_export', 'mirrortalk_intelligence_export');

function mirrortalk_intelligence_weekly_snapshot() {
    $data = mirrortalk_intelligence_snapshot(7);
    $report = array('time' => time(), 'page_views' => $data['totals']['page_views'], 'visitors' => $data['totals']['visitors'], 'plays' => $data['totals']['plays'], 'completions' => $data['totals']['completions'], 'conversions' => $data['totals']['conversions'], 'issues' => $data['seo']['broken_links'], 'summary' => sprintf(__('This week: %1$d page views from %2$d consented visitors, %3$d podcast plays, %4$d completions and %5$d measured conversions.', 'astra-child'), $data['totals']['page_views'], $data['totals']['visitors'], $data['totals']['plays'], $data['totals']['completions'], $data['totals']['conversions']));
    $reports = (array) get_option('mirrortalk_intelligence_weekly_reports', array()); $reports[] = $report;
    update_option('mirrortalk_intelligence_weekly_reports', array_slice($reports, -52), false);
    return $report;
}
add_action('mirrortalk_weekly_seo_report', 'mirrortalk_intelligence_weekly_snapshot', 5);

add_action('admin_post_mirrortalk_intelligence_report_now', function () {
    if (!current_user_can('manage_mirrortalk_seo')) wp_die(esc_html__('You cannot generate this report.', 'astra-child'));
    check_admin_referer('mirrortalk_intelligence_report_now');
    mirrortalk_intelligence_weekly_snapshot();
    wp_safe_redirect(admin_url('admin.php?page=mirror-talk-intelligence&period=7#reports')); exit;
});

function mirrortalk_intelligence_cleanup() {
    global $wpdb;
    $wpdb->query($wpdb->prepare('DELETE FROM ' . mirrortalk_intelligence_table() . ' WHERE occurred_at < %s', gmdate('Y-m-d H:i:s', time() - 400 * DAY_IN_SECONDS)));
}
add_action('mirrortalk_intelligence_cleanup', 'mirrortalk_intelligence_cleanup');
add_action('init', function () { if (!wp_next_scheduled('mirrortalk_intelligence_cleanup')) wp_schedule_event(time() + DAY_IN_SECONDS, 'daily', 'mirrortalk_intelligence_cleanup'); });
add_action('switch_theme', function () { wp_clear_scheduled_hook('mirrortalk_intelligence_cleanup'); });

add_action('admin_enqueue_scripts', function ($hook) {
    if ($hook !== 'toplevel_page_mirror-talk-intelligence') return;
    wp_enqueue_style('mirror-talk-intelligence-admin', get_stylesheet_directory_uri() . '/intelligence-admin.css', array(), wp_get_theme()->get('Version'));
    wp_enqueue_script('mirror-talk-intelligence-admin', get_stylesheet_directory_uri() . '/intelligence-admin.js', array(), wp_get_theme()->get('Version'), true);
});
