<?php
/** Production recovery, attribution and low-risk content hygiene. */
if (!defined('ABSPATH')) { exit; }

function mirrortalk_campaign_url($url, $surface = 'website', $content = '') {
    $url = esc_url_raw((string) $url);
    if (!$url || !in_array(wp_parse_url($url, PHP_URL_SCHEME), array('http', 'https'), true)) return $url;
    return add_query_arg(array_filter(array(
        'utm_source' => 'mirrortalk',
        'utm_medium' => 'website',
        'utm_campaign' => sanitize_key($surface),
        'utm_content' => sanitize_key($content),
    )), $url);
}

/* Debug output must never leak into public responses. WP_DEBUG_LOG itself is a
 * wp-config concern; the admin notice below gives the exact remaining action. */
add_action('init', function () {
    if (!is_admin()) @ini_set('display_errors', '0');
}, PHP_INT_MAX);

function mirrortalk_recover_cron_runner() {
    if (get_transient('mirrortalk_cron_recovery_lock')) return;
    $next = wp_next_scheduled('action_scheduler_run_queue');
    $elementor = get_option('mirrortalk_elementor_auto_migration') && !wp_next_scheduled('mirrortalk_elementor_auto_batch');
    if ((!$next || $next > time() - 10 * MINUTE_IN_SECONDS) && !$elementor) return;
    set_transient('mirrortalk_cron_recovery_lock', 1, 5 * MINUTE_IN_SECONDS);
    if ($elementor) wp_schedule_single_event(time() + 30, 'mirrortalk_elementor_auto_batch');
    wp_remote_post(site_url('wp-cron.php?doing_wp_cron=' . rawurlencode(sprintf('%.22F', microtime(true)))), array(
        'timeout' => 0.01, 'blocking' => false, 'sslverify' => apply_filters('https_local_ssl_verify', false),
    ));
}
add_action('shutdown', 'mirrortalk_recover_cron_runner', 999);

function mirrortalk_disable_blanket_404_plugin() {
    if (!is_admin() || !current_user_can('activate_plugins')) return;
    if (!function_exists('deactivate_plugins')) require_once ABSPATH . 'wp-admin/includes/plugin.php';
    foreach ((array) get_option('active_plugins', array()) as $plugin) {
        if (!preg_match('#^all-404-redirect-to-homepage/#i', (string) $plugin)) continue;
        deactivate_plugins($plugin, false, false);
        update_option('mirrortalk_404_plugin_disabled', array('plugin' => $plugin, 'time' => time()), false);
    }
}

function mirrortalk_source_hygiene_batch() {
    if (get_transient('mirrortalk_source_hygiene_lock')) return;
    set_transient('mirrortalk_source_hygiene_lock', 1, 5 * MINUTE_IN_SECONDS);
    $ids = get_posts(array(
        'post_type' => array('post', 'page'), 'post_status' => array('publish', 'draft', 'future'),
        'posts_per_page' => 5, 'fields' => 'ids', 'orderby' => 'modified', 'order' => 'DESC',
        'meta_query' => array('relation' => 'AND',
            array('key' => '_mirrortalk_source_hygiene_v1', 'compare' => 'NOT EXISTS'),
            array('key' => '_elementor_data', 'compare' => 'NOT EXISTS'),
        ),
    ));
    foreach ($ids as $post_id) {
        $post = get_post($post_id); $original = (string) $post->post_content; $content = $original;
        $content = preg_replace('/<h1(\s[^>]*)?>/i', '<h2$1>', $content);
        $content = preg_replace('/<\/h1>/i', '</h2>', $content);
        $content = preg_replace_callback('/<iframe\b([^>]*)>/i', function ($match) {
            if (preg_match('/\btitle\s*=/i', $match[1])) return $match[0];
            $label = stripos($match[1], 'youtube') !== false ? __('Mirror Talk video player', 'astra-child') : __('Embedded media', 'astra-child');
            return '<iframe title="' . esc_attr($label) . '"' . $match[1] . '>';
        }, $content);
        if ($content !== $original) {
            update_post_meta($post_id, '_mirrortalk_source_hygiene_snapshot_v1', $original);
            wp_update_post(wp_slash(array('ID' => $post_id, 'post_content' => $content)));
        }
        update_post_meta($post_id, '_mirrortalk_source_hygiene_v1', $content !== $original ? 'repaired' : 'clean');
    }
    delete_transient('mirrortalk_source_hygiene_lock');
    if (count($ids) === 5) wp_schedule_single_event(time() + 5 * MINUTE_IN_SECONDS, 'mirrortalk_source_hygiene_batch');
}
add_action('mirrortalk_source_hygiene_batch', 'mirrortalk_source_hygiene_batch');

function mirrortalk_hardening_release_bootstrap() {
    $version = function_exists('mirrortalk_release_version') ? mirrortalk_release_version() : '1';
    if (get_option('mirrortalk_hardening_bootstrap') === $version) return;
    mirrortalk_disable_blanket_404_plugin();
    update_option('mirrortalk_elementor_auto_migration', 1, false);
    if (!wp_next_scheduled('mirrortalk_elementor_auto_batch')) wp_schedule_single_event(time() + 2 * MINUTE_IN_SECONDS, 'mirrortalk_elementor_auto_batch');
    if (!wp_next_scheduled('mirrortalk_source_hygiene_batch')) wp_schedule_single_event(time() + 3 * MINUTE_IN_SECONDS, 'mirrortalk_source_hygiene_batch');
    if (!wp_next_scheduled('mirrortalk_seo_crawl_continue')) wp_schedule_single_event(time() + 4 * MINUTE_IN_SECONDS, 'mirrortalk_seo_crawl_continue');
    if (function_exists('mirrortalk_pipeline_request')) {
        mirrortalk_pipeline_request('release');
        if (function_exists('mirrortalk_runtime_request_dispatch')) mirrortalk_runtime_request_dispatch();
    } elseif (!wp_next_scheduled('mirrortalk_intelligence_artifacts_refresh')) wp_schedule_single_event(time() + 8 * MINUTE_IN_SECONDS, 'mirrortalk_intelligence_artifacts_refresh');
    update_option('mirrortalk_hardening_bootstrap', $version, false);
}
add_action('admin_init', 'mirrortalk_hardening_release_bootstrap', 90);

