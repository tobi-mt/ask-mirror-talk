<?php
/**
 * First-party Google Search Console and Bing Webmaster connectors.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_GOOGLE_SCOPE', 'https://www.googleapis.com/auth/webmasters');
define('MIRRORTALK_GOOGLE_API', 'https://www.googleapis.com/webmasters/v3');
define('MIRRORTALK_BING_API', 'https://ssl.bing.com/webmaster/api.svc/json');

function mirrortalk_connector_encrypt($value) {
    if ($value === '' || $value === null) return '';
    if (!function_exists('openssl_encrypt')) return new WP_Error('crypto_unavailable', __('OpenSSL is required to protect search connection credentials.', 'astra-child'));
    $iv = random_bytes(12); $tag = '';
    $encrypted = openssl_encrypt(wp_json_encode($value), 'aes-256-gcm', hash('sha256', wp_salt('auth'), true), OPENSSL_RAW_DATA, $iv, $tag);
    if ($encrypted === false) return new WP_Error('encryption_failed', __('The search connection credentials could not be encrypted.', 'astra-child'));
    return base64_encode(wp_json_encode(array('v' => 1, 'iv' => base64_encode($iv), 'tag' => base64_encode($tag), 'data' => base64_encode($encrypted))));
}

function mirrortalk_connector_decrypt($stored) {
    if (!$stored || !function_exists('openssl_decrypt')) return array();
    $envelope = json_decode((string) base64_decode((string) $stored, true), true);
    if (!is_array($envelope) || empty($envelope['iv']) || empty($envelope['tag']) || empty($envelope['data'])) return array();
    $plain = openssl_decrypt(base64_decode($envelope['data']), 'aes-256-gcm', hash('sha256', wp_salt('auth'), true), OPENSSL_RAW_DATA, base64_decode($envelope['iv']), base64_decode($envelope['tag']));
    $value = $plain === false ? null : json_decode($plain, true);
    return is_array($value) ? $value : array();
}

function mirrortalk_connector_credentials($engine) {
    return mirrortalk_connector_decrypt(get_option('mirrortalk_' . $engine . '_credentials', ''));
}

function mirrortalk_connector_store($engine, $value) {
    $encrypted = mirrortalk_connector_encrypt($value);
    if (is_wp_error($encrypted)) return $encrypted;
    update_option('mirrortalk_' . $engine . '_credentials', $encrypted, false);
    return true;
}

function mirrortalk_connector_migrate_legacy_secrets() {
    if (get_option('mirrortalk_connector_secret_migration') === '1') return;
    $settings = (array) get_option('mirrortalk_seo_platform', array());
    if (!mirrortalk_connector_credentials('bing') && !empty($settings['bing_api_key'])) mirrortalk_connector_store('bing', array('api_key' => sanitize_text_field($settings['bing_api_key'])));
    unset($settings['gsc_token'], $settings['bing_api_key']);
    update_option('mirrortalk_seo_platform', $settings, false);
    update_option('mirrortalk_connector_secret_migration', '1', false);
}
add_action('admin_init', 'mirrortalk_connector_migrate_legacy_secrets', 30);

function mirrortalk_connector_notice_url($engine, $status, $message = '') {
    return add_query_arg(array('page' => 'mirror-talk-seo', 'connection' => $engine, 'connection_status' => $status, 'connection_message' => $message), admin_url('admin.php'));
}

function mirrortalk_connector_require_admin() {
    if (!current_user_can('manage_mirrortalk_seo')) wp_die(esc_html__('You are not allowed to manage search connections.', 'astra-child'));
}

function mirrortalk_connector_host($url) {
    return preg_replace('/^www\./', '', strtolower((string) wp_parse_url($url, PHP_URL_HOST)));
}

function mirrortalk_google_callback_url() {
    return admin_url('admin-post.php?action=mirrortalk_google_callback');
}

function mirrortalk_google_api($method, $path, $body = null) {
    $credentials = mirrortalk_connector_credentials('google');
    $token = (array) ($credentials['token'] ?? array());
    if (empty($token['access_token'])) return new WP_Error('google_not_connected', __('Google Search Console is not connected.', 'astra-child'));
    if ((int) ($token['expires_at'] ?? 0) <= time() + 120) {
        if (empty($token['refresh_token']) || empty($credentials['client_id']) || empty($credentials['client_secret'])) return new WP_Error('google_refresh_missing', __('Google needs to be reconnected to renew access.', 'astra-child'));
        $response = wp_remote_post('https://oauth2.googleapis.com/token', array('timeout' => 8, 'body' => array(
            'client_id' => $credentials['client_id'], 'client_secret' => $credentials['client_secret'],
            'refresh_token' => $token['refresh_token'], 'grant_type' => 'refresh_token',
        )));
        if (is_wp_error($response)) return $response;
        $fresh = json_decode(wp_remote_retrieve_body($response), true);
        if (wp_remote_retrieve_response_code($response) >= 300 || empty($fresh['access_token'])) return new WP_Error('google_refresh_failed', sanitize_text_field($fresh['error_description'] ?? $fresh['error'] ?? __('Google token renewal failed.', 'astra-child')));
        $token['access_token'] = $fresh['access_token'];
        $token['expires_at'] = time() + max(300, (int) ($fresh['expires_in'] ?? 3600));
        $credentials['token'] = $token;
        $saved = mirrortalk_connector_store('google', $credentials); if (is_wp_error($saved)) return $saved;
    }
    $args = array('method' => strtoupper($method), 'timeout' => 10, 'headers' => array('Authorization' => 'Bearer ' . $token['access_token'], 'Accept' => 'application/json'));
    if ($body !== null) { $args['headers']['Content-Type'] = 'application/json'; $args['body'] = wp_json_encode($body); }
    elseif (in_array(strtoupper($method), array('POST', 'PUT', 'PATCH'), true)) {
        // Google sitemap submission uses an empty PUT but still requires an
        // explicit zero-length entity on some HTTP/2 hosting transports.
        $args['headers']['Content-Length'] = '0';
        $args['body'] = '';
    }
    $response = wp_remote_request(MIRRORTALK_GOOGLE_API . $path, $args);
    if (is_wp_error($response)) return $response;
    $code = wp_remote_retrieve_response_code($response); $data = json_decode(wp_remote_retrieve_body($response), true);
    if ($code >= 300) return new WP_Error('google_api_error', sanitize_text_field($data['error']['message'] ?? sprintf(__('Google API returned HTTP %d.', 'astra-child'), $code)), array('status' => $code));
    return is_array($data) ? $data : array();
}

function mirrortalk_google_property($sites) {
    $home_host = mirrortalk_connector_host(home_url('/')); $best = array();
    foreach ((array) $sites as $site) {
        if (($site['permissionLevel'] ?? '') === 'siteUnverifiedUser' || empty($site['siteUrl'])) continue;
        $url = (string) $site['siteUrl'];
        $matches = strpos($url, 'sc-domain:') === 0 ? preg_replace('/^www\./', '', substr($url, 10)) === $home_host : mirrortalk_connector_host($url) === $home_host;
        if (!$matches) continue;
        if (!$best || strpos($url, 'sc-domain:') === 0) $best = $site;
    }
    return $best;
}

function mirrortalk_search_store_engine_rows($engine, $rows) {
    $existing = array_values(array_filter((array) get_option('mirrortalk_search_performance', array()), function ($row) use ($engine) { return ($row['engine'] ?? '') !== $engine; }));
    update_option('mirrortalk_search_performance', array_slice(array_merge($existing, $rows), -20000), false);
}

function mirrortalk_google_sync() {
    $sites = mirrortalk_google_api('GET', '/sites');
    if (is_wp_error($sites)) return $sites;
    $property = mirrortalk_google_property($sites['siteEntry'] ?? array());
    if (!$property) return new WP_Error('google_property_missing', __('The connected Google account does not have a verified Mirror Talk property.', 'astra-child'));
    $site_url = $property['siteUrl']; $encoded_site = rawurlencode($site_url);
    $analytics = mirrortalk_google_api('POST', '/sites/' . $encoded_site . '/searchAnalytics/query', array(
        'startDate' => gmdate('Y-m-d', strtotime('-31 days')), 'endDate' => gmdate('Y-m-d', strtotime('-3 days')),
        'dimensions' => array('date', 'query', 'page'), 'rowLimit' => 25000, 'dataState' => 'final',
    ));
    if (is_wp_error($analytics)) return $analytics;
    $rows = array();
    foreach ((array) ($analytics['rows'] ?? array()) as $row) {
        $keys = (array) ($row['keys'] ?? array());
        $rows[] = array('date' => sanitize_text_field($keys[0] ?? ''), 'engine' => 'google', 'query' => sanitize_text_field($keys[1] ?? ''), 'page' => esc_url_raw($keys[2] ?? ''), 'clicks' => max(0, (int) ($row['clicks'] ?? 0)), 'impressions' => max(0, (int) ($row['impressions'] ?? 0)), 'position' => max(0, (float) ($row['position'] ?? 0)));
    }
    mirrortalk_search_store_engine_rows('google', $rows);
    $sitemaps = array(home_url('/mirror-talk-sitemap/'), home_url('/mirror-talk-news-sitemap/'), home_url('/mirror-talk-video-sitemap/'));
    $submitted = array(); $warnings = array();
    foreach ($sitemaps as $sitemap) {
        $result = mirrortalk_google_api('PUT', '/sites/' . $encoded_site . '/sitemaps/' . rawurlencode($sitemap));
        if (!is_wp_error($result)) $submitted[] = $sitemap; else $warnings[] = $result->get_error_message();
    }
    $sitemap_status = mirrortalk_google_api('GET', '/sites/' . $encoded_site . '/sitemaps');
    if (is_wp_error($sitemap_status)) $warnings[] = $sitemap_status->get_error_message();
    $status = array('connected' => true, 'property' => $site_url, 'permission' => sanitize_text_field($property['permissionLevel'] ?? ''), 'properties_seen' => count((array) ($sites['siteEntry'] ?? array())), 'rows' => count($rows), 'sitemaps' => $submitted, 'sitemap_status' => is_wp_error($sitemap_status) ? array() : array_slice((array) ($sitemap_status['sitemap'] ?? array()), 0, 20), 'warnings' => array_values(array_unique($warnings)), 'last_sync' => time(), 'error' => '');
    update_option('mirrortalk_google_status', $status, false);
    return $status;
}

function mirrortalk_bing_api($method, $params = array(), $post = false) {
    $credentials = mirrortalk_connector_credentials('bing');
    if (empty($credentials['api_key'])) return new WP_Error('bing_not_connected', __('Bing Webmaster Tools is not connected.', 'astra-child'));
    $url = MIRRORTALK_BING_API . '/' . rawurlencode($method) . '?' . http_build_query(array_merge(array('apikey' => $credentials['api_key']), $post ? array() : $params), '', '&', PHP_QUERY_RFC3986);
    $args = array('timeout' => 25, 'headers' => array('Accept' => 'application/json'));
    if ($post) { $args['headers']['Content-Type'] = 'application/json'; $args['body'] = wp_json_encode($params); $response = wp_remote_post($url, $args); }
    else $response = wp_remote_get($url, $args);
    if (is_wp_error($response)) return $response;
    $code = wp_remote_retrieve_response_code($response); $data = json_decode(wp_remote_retrieve_body($response), true);
    if ($code >= 300 || !is_array($data)) return new WP_Error('bing_api_error', sanitize_text_field($data['Message'] ?? $data['message'] ?? sprintf(__('Bing API returned HTTP %d.', 'astra-child'), $code)), array('status' => $code));
    return isset($data['d']) ? $data['d'] : $data;
}

function mirrortalk_bing_date($value) {
    if (preg_match('/Date\((\d+)/', (string) $value, $match)) return gmdate('Y-m-d', (int) floor(((int) $match[1]) / 1000));
    $time = strtotime((string) $value); return $time ? gmdate('Y-m-d', $time) : '';
}

function mirrortalk_bing_sync() {
    $sites = mirrortalk_bing_api('GetUserSites'); if (is_wp_error($sites)) return $sites;
    $home_host = mirrortalk_connector_host(home_url('/')); $property = array();
    foreach ((array) $sites as $site) if (!empty($site['IsVerified']) && mirrortalk_connector_host($site['Url'] ?? '') === $home_host) { $property = $site; break; }
    if (!$property) return new WP_Error('bing_property_missing', __('The Bing account does not contain a verified Mirror Talk property.', 'astra-child'));
    $site_url = (string) $property['Url'];
    $stats = mirrortalk_bing_api('GetQueryStats', array('siteUrl' => $site_url)); if (is_wp_error($stats)) return $stats;
    $rows = array();
    foreach ((array) $stats as $row) $rows[] = array('date' => mirrortalk_bing_date($row['Date'] ?? ''), 'engine' => 'bing', 'query' => sanitize_text_field($row['Query'] ?? ''), 'page' => '', 'clicks' => max(0, (int) ($row['Clicks'] ?? 0)), 'impressions' => max(0, (int) ($row['Impressions'] ?? 0)), 'position' => max(0, (float) ($row['AvgImpressionPosition'] ?? 0)));
    mirrortalk_search_store_engine_rows('bing', $rows);
    $submitted = array(); $warnings = array();
    foreach (array(home_url('/mirror-talk-sitemap/'), home_url('/mirror-talk-news-sitemap/'), home_url('/mirror-talk-video-sitemap/')) as $sitemap) {
        $result = mirrortalk_bing_api('SubmitFeed', array('siteUrl' => $site_url, 'feedUrl' => $sitemap), true);
        if (!is_wp_error($result)) $submitted[] = $sitemap; else $warnings[] = $result->get_error_message();
    }
    $feeds = mirrortalk_bing_api('GetFeeds', array('siteUrl' => $site_url));
    if (is_wp_error($feeds)) $warnings[] = $feeds->get_error_message();
    $status = array('connected' => true, 'property' => $site_url, 'verified' => true, 'properties_seen' => count((array) $sites), 'rows' => count($rows), 'sitemaps' => $submitted, 'sitemap_status' => is_wp_error($feeds) ? array() : array_slice((array) $feeds, 0, 20), 'warnings' => array_values(array_unique($warnings)), 'last_sync' => time(), 'error' => '');
    update_option('mirrortalk_bing_status', $status, false);
    return $status;
}

function mirrortalk_connector_record_error($engine, $error) {
    $status = (array) get_option('mirrortalk_' . $engine . '_status', array());
    $status['connected'] = !empty(mirrortalk_connector_credentials($engine)); $status['last_attempt'] = time(); $status['error'] = $error->get_error_message();
    update_option('mirrortalk_' . $engine . '_status', $status, false);
}

function mirrortalk_search_connectors_sync() {
    if (mirrortalk_connector_credentials('google')) { $result = mirrortalk_google_sync(); if (is_wp_error($result)) mirrortalk_connector_record_error('google', $result); }
    if (mirrortalk_connector_credentials('bing')) { $result = mirrortalk_bing_sync(); if (is_wp_error($result)) mirrortalk_connector_record_error('bing', $result); }
    update_option('mirrortalk_seo_last_connector_sync', time(), false);
}

add_action('admin_post_mirrortalk_connector_settings', function () {
    mirrortalk_connector_require_admin(); check_admin_referer('mirrortalk_connector_settings');
    $engine = sanitize_key($_POST['engine'] ?? '');
    if ($engine === 'google') {
        $existing = mirrortalk_connector_credentials('google');
        $client_id = sanitize_text_field(wp_unslash($_POST['client_id'] ?? '')); $secret = trim((string) wp_unslash($_POST['client_secret'] ?? ''));
        if (!$secret) $secret = $existing['client_secret'] ?? '';
        $result = ($client_id && $secret) ? mirrortalk_connector_store('google', array('client_id' => $client_id, 'client_secret' => $secret, 'token' => $existing['token'] ?? array())) : new WP_Error('missing_fields', __('Google client ID and secret are required.', 'astra-child'));
    } elseif ($engine === 'bing') {
        $key = trim((string) wp_unslash($_POST['api_key'] ?? '')); $result = $key ? mirrortalk_connector_store('bing', array('api_key' => sanitize_text_field($key))) : new WP_Error('missing_fields', __('A Bing Webmaster API key is required.', 'astra-child'));
        if (!is_wp_error($result)) mirrortalk_runtime_queue('mirrortalk_connector_sync_manual');
    } else $result = new WP_Error('invalid_engine', __('Unknown search provider.', 'astra-child'));
    wp_safe_redirect(mirrortalk_connector_notice_url($engine ?: 'search', is_wp_error($result) ? 'error' : 'saved', is_wp_error($result) ? $result->get_error_message() : '')); exit;
});

add_action('admin_post_mirrortalk_google_connect', function () {
    mirrortalk_connector_require_admin(); check_admin_referer('mirrortalk_google_connect');
    $credentials = mirrortalk_connector_credentials('google');
    if (empty($credentials['client_id']) || empty($credentials['client_secret'])) { wp_safe_redirect(mirrortalk_connector_notice_url('google', 'error', __('Save the Google OAuth client first.', 'astra-child'))); exit; }
    $state = wp_generate_password(48, false, false); set_transient('mirrortalk_google_state_' . get_current_user_id(), hash('sha256', $state), 15 * MINUTE_IN_SECONDS);
    $url = add_query_arg(array('client_id' => $credentials['client_id'], 'redirect_uri' => mirrortalk_google_callback_url(), 'response_type' => 'code', 'scope' => MIRRORTALK_GOOGLE_SCOPE, 'access_type' => 'offline', 'include_granted_scopes' => 'true', 'prompt' => 'consent', 'state' => $state), 'https://accounts.google.com/o/oauth2/v2/auth');
    wp_redirect(esc_url_raw($url)); exit;
});

add_action('admin_post_mirrortalk_google_callback', function () {
    mirrortalk_connector_require_admin(); $state = sanitize_text_field(wp_unslash($_GET['state'] ?? '')); $expected = get_transient('mirrortalk_google_state_' . get_current_user_id()); delete_transient('mirrortalk_google_state_' . get_current_user_id());
    if (!$state || !$expected || !hash_equals($expected, hash('sha256', $state))) { wp_safe_redirect(mirrortalk_connector_notice_url('google', 'error', __('Google connection state expired or was invalid.', 'astra-child'))); exit; }
    if (!empty($_GET['error']) || empty($_GET['code'])) { wp_safe_redirect(mirrortalk_connector_notice_url('google', 'error', sanitize_text_field(wp_unslash($_GET['error_description'] ?? $_GET['error'] ?? __('Authorization was not completed.', 'astra-child'))))); exit; }
    $credentials = mirrortalk_connector_credentials('google');
    $response = wp_remote_post('https://oauth2.googleapis.com/token', array('timeout' => 8, 'body' => array('code' => sanitize_text_field(wp_unslash($_GET['code'])), 'client_id' => $credentials['client_id'], 'client_secret' => $credentials['client_secret'], 'redirect_uri' => mirrortalk_google_callback_url(), 'grant_type' => 'authorization_code')));
    $token = is_wp_error($response) ? array() : json_decode(wp_remote_retrieve_body($response), true);
    if (is_wp_error($response) || wp_remote_retrieve_response_code($response) >= 300 || empty($token['access_token'])) { $message = is_wp_error($response) ? $response->get_error_message() : sanitize_text_field($token['error_description'] ?? $token['error'] ?? __('Google token exchange failed.', 'astra-child')); wp_safe_redirect(mirrortalk_connector_notice_url('google', 'error', $message)); exit; }
    $credentials['token'] = array('access_token' => $token['access_token'], 'refresh_token' => $token['refresh_token'] ?? '', 'expires_at' => time() + max(300, (int) ($token['expires_in'] ?? 3600)), 'scope' => sanitize_text_field($token['scope'] ?? MIRRORTALK_GOOGLE_SCOPE));
    $saved = mirrortalk_connector_store('google', $credentials); $result = $saved;if(!is_wp_error($saved))mirrortalk_runtime_queue('mirrortalk_connector_sync_manual');
    wp_safe_redirect(mirrortalk_connector_notice_url('google', is_wp_error($result) ? 'error' : 'connected', is_wp_error($result) ? $result->get_error_message() : '')); exit;
});

add_action('admin_post_mirrortalk_connector_sync', function () {
    mirrortalk_connector_require_admin(); check_admin_referer('mirrortalk_connector_sync'); mirrortalk_runtime_queue('mirrortalk_connector_sync_manual');
    wp_safe_redirect(mirrortalk_connector_notice_url('search', 'queued')); exit;
});
add_action('mirrortalk_connector_sync_manual',function(){mirrortalk_runtime_run('search_sync','mirrortalk_search_connectors_sync',20*MINUTE_IN_SECONDS);});

add_action('admin_post_mirrortalk_connector_disconnect', function () {
    mirrortalk_connector_require_admin(); check_admin_referer('mirrortalk_connector_disconnect'); $engine = sanitize_key($_GET['engine'] ?? '');
    if (in_array($engine, array('google', 'bing'), true)) {
        if ($engine === 'google') {
            $credentials = mirrortalk_connector_credentials('google'); $token = $credentials['token']['refresh_token'] ?? $credentials['token']['access_token'] ?? '';
            if ($token) wp_remote_post('https://oauth2.googleapis.com/revoke', array('timeout' => 3, 'blocking' => false, 'body' => array('token' => $token)));
        }
        delete_option('mirrortalk_' . $engine . '_credentials'); delete_option('mirrortalk_' . $engine . '_status'); mirrortalk_search_store_engine_rows($engine, array());
    }
    wp_safe_redirect(mirrortalk_connector_notice_url($engine, 'disconnected')); exit;
});

function mirrortalk_connector_status_card($engine, $label) {
    $status = (array) get_option('mirrortalk_' . $engine . '_status', array()); $credentials = mirrortalk_connector_credentials($engine); $connected = !empty($status['connected']) && empty($status['error']);
    echo '<div class="card"><h3>' . esc_html($label) . '</h3><p><strong>' . esc_html($connected ? __('Connected', 'astra-child') : ($credentials ? __('Needs attention', 'astra-child') : __('Not connected', 'astra-child'))) . '</strong></p>';
    if (!empty($status['property'])) echo '<p><code>' . esc_html($status['property']) . '</code><br>' . esc_html(sprintf(__('%d search rows · last sync %s', 'astra-child'), (int) ($status['rows'] ?? 0), !empty($status['last_sync']) ? wp_date('j M Y H:i', $status['last_sync']) : __('never', 'astra-child'))) . '</p>';
    if (!empty($status['sitemaps'])) echo '<p>' . esc_html(sprintf(_n('%d sitemap submitted', '%d sitemaps submitted', count($status['sitemaps']), 'astra-child'), count($status['sitemaps']))) . '</p>';
    if (!empty($status['error'])) echo '<p style="color:#b32d2e">' . esc_html($status['error']) . '</p>';
    if (!empty($status['warnings'])) echo '<p style="color:#996800">' . esc_html(implode(' ', array_slice((array) $status['warnings'], 0, 3))) . '</p>';
    if ($credentials) echo '<p><a href="' . esc_url(wp_nonce_url(admin_url('admin-post.php?action=mirrortalk_connector_disconnect&engine=' . $engine), 'mirrortalk_connector_disconnect')) . '">' . esc_html__('Disconnect and erase credentials', 'astra-child') . '</a></p>';
    echo '</div>';
}

function mirrortalk_search_connectors_admin_panel() {
    $google = mirrortalk_connector_credentials('google');
    if (!empty($_GET['connection_status'])) {
        $ok = in_array(sanitize_key($_GET['connection_status']), array('saved', 'connected', 'synced', 'disconnected'), true); $message = !empty($_GET['connection_message']) ? sanitize_text_field(wp_unslash($_GET['connection_message'])) : ($ok ? __('Search connection updated.', 'astra-child') : __('The search connection could not be updated.', 'astra-child'));
        echo '<div class="notice ' . ($ok ? 'notice-success' : 'notice-error') . '"><p>' . esc_html($message) . '</p></div>';
    }
    echo '<h2>' . esc_html__('Search data connections', 'astra-child') . '</h2><p>' . esc_html__('Connect the verified owner accounts once. Mirror Talk then discovers the matching property, renews access, submits its sitemaps and synchronizes verified search performance twice daily.', 'astra-child') . '</p>';
    echo '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px">'; mirrortalk_connector_status_card('google', 'Google Search Console'); mirrortalk_connector_status_card('bing', 'Bing Webmaster Tools'); echo '</div>';
    echo '<h3>' . esc_html__('Google Search Console', 'astra-child') . '</h3><p>' . esc_html__('Create a Web application OAuth client with the Search Console API enabled and register this exact redirect URI:', 'astra-child') . ' <code>' . esc_html(mirrortalk_google_callback_url()) . '</code></p>';
    echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '"><input type="hidden" name="action" value="mirrortalk_connector_settings"><input type="hidden" name="engine" value="google">'; wp_nonce_field('mirrortalk_connector_settings');
    echo '<table class="form-table"><tr><th>OAuth client ID</th><td><input class="regular-text" name="client_id" value="' . esc_attr($google['client_id'] ?? '') . '" autocomplete="off" required></td></tr><tr><th>OAuth client secret</th><td><input class="regular-text" type="password" name="client_secret" value="" autocomplete="new-password" placeholder="' . esc_attr(!empty($google['client_secret']) ? __('Stored securely; leave blank to keep it', 'astra-child') : '') . '"></td></tr></table>'; submit_button(__('Save Google OAuth application', 'astra-child'), 'secondary'); echo '</form>';
    if (!empty($google['client_id']) && !empty($google['client_secret'])) echo '<p><a class="button button-primary" href="' . esc_url(wp_nonce_url(admin_url('admin-post.php?action=mirrortalk_google_connect'), 'mirrortalk_google_connect')) . '">' . esc_html__('Connect Google Search Console', 'astra-child') . '</a></p>';
    echo '<h3>' . esc_html__('Bing Webmaster Tools', 'astra-child') . '</h3><p>' . esc_html__('Generate an API key in Bing Webmaster Tools → Settings → API Access. It applies to the verified sites in that account and is encrypted before storage.', 'astra-child') . '</p><form method="post" action="' . esc_url(admin_url('admin-post.php')) . '"><input type="hidden" name="action" value="mirrortalk_connector_settings"><input type="hidden" name="engine" value="bing">'; wp_nonce_field('mirrortalk_connector_settings'); echo '<input class="regular-text" type="password" name="api_key" autocomplete="new-password" required> '; submit_button(__('Connect and test Bing', 'astra-child'), 'secondary', 'submit', false); echo '</form>';
    if (mirrortalk_connector_credentials('google') || mirrortalk_connector_credentials('bing')) { echo '<form style="margin-top:20px" method="post" action="' . esc_url(admin_url('admin-post.php')) . '"><input type="hidden" name="action" value="mirrortalk_connector_sync">'; wp_nonce_field('mirrortalk_connector_sync'); submit_button(__('Synchronize connected accounts now', 'astra-child'), 'secondary'); echo '</form>'; }
}
