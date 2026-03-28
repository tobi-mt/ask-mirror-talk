<?php
/**
 * Ask Mirror Talk Shortcode + AJAX handler for Astra theme.
 *
 * Usage: [ask_mirror_talk]
 * Requires WPGetAPI to be configured with:
 *   api_id = mirror_talk_ask
 *   endpoint_id = mirror_talk_ask
 */

if (!defined('ABSPATH')) {
    exit;
}

function ask_mirror_talk_shortcode() {
    ob_start();
    ?>
    <div class="ask-mirror-talk">
        <div class="amt-heading-row">
            <h2>Ask Mirror Talk</h2>
            <div class="amt-heading-controls">
                <button type="button" id="amt-text-size-btn" class="amt-text-size-btn" title="Change text size" aria-label="Change text size">Aa</button>
                <button type="button" id="amt-about-btn" class="amt-about-btn" title="About this app" aria-label="About Mirror Talk">ⓘ</button>
            </div>
        </div>
        <div id="amt-stats-bar" class="amt-stats-bar" style="display:none;">
            <div class="amt-stat amt-stat-streak">
                <span class="amt-stat-icon" aria-hidden="true">🔥</span>
                <span class="amt-stat-value" id="amt-streak-value">0</span>
                <span class="amt-stat-label">day streak</span>
            </div>
            <div class="amt-stat amt-stat-questions">
                <span class="amt-stat-icon" aria-hidden="true">💬</span>
                <span class="amt-stat-value" id="amt-questions-value">0</span>
                <span class="amt-stat-label">questions</span>
            </div>
            <div class="amt-stat amt-stat-themes">
                <span class="amt-stat-icon" aria-hidden="true">🗺️</span>
                <span class="amt-stat-value" id="amt-themes-value">0</span>
                <span class="amt-stat-label">/ 20 topics</span>
            </div>
            <button type="button" class="amt-badges-btn" id="amt-badges-btn" title="Your badges"><span aria-hidden="true">🏆</span> <span id="amt-badge-count">0</span><span class="screen-reader-text"> badges earned</span></button>
            <button type="button" class="amt-insights-btn" id="amt-insights-btn" title="My saved insights" aria-label="My saved insights"><span aria-hidden="true">🔖</span><span class="screen-reader-text"> Saved insights</span></button>
            <button type="button" class="amt-notif-manage-btn" id="amt-notif-manage-btn" title="Notification settings" style="display:none;" aria-expanded="false"><span aria-hidden="true">🔔</span><span class="screen-reader-text"> Notification settings</span></button>
        </div>
        <div id="amt-insights-panel" class="amt-insights-panel" style="display:none;" role="region" aria-label="My saved insights"></div>
        <div id="amt-streak-protect-banner" class="amt-streak-protect-banner" style="display:none;" role="status"></div>
        <div id="amt-notif-manage-panel" class="amt-notif-manage-panel" style="display:none;" aria-label="Notification settings"></div>
        <div id="amt-badge-shelf" class="amt-badge-shelf" style="display:none;"></div>
        <div id="amt-milestone-toast" class="amt-milestone-toast" style="display:none;"></div>
        <!-- About modal -->
        <div id="amt-about-modal" class="amt-about-modal" style="display:none;" role="dialog" aria-modal="true" aria-label="About Mirror Talk"></div>
        <div id="ask-mirror-talk-qotd" class="amt-qotd" style="display:none;"></div>
        <div id="amt-explore-expander" class="amt-explore-expander" style="display:none;">
            <button type="button" id="amt-explore-toggle" class="amt-explore-toggle" aria-expanded="false" aria-controls="amt-explore-panel">
                <span class="amt-explore-icons" id="amt-explore-icons" aria-hidden="true"></span>
                <span class="amt-explore-label">Explore topics &amp; questions</span>
                <span class="amt-explore-chevron" aria-hidden="true">&rsaquo;</span>
            </button>
            <div id="amt-explore-panel" class="amt-explore-panel" role="region" aria-label="Topics and suggested questions">
                <div id="ask-mirror-talk-topics" class="amt-topics" style="display:none;">
                    <p class="amt-topics-label">Browse by topic:</p>
                    <div class="amt-topics-list"></div>
                </div>
                <div id="ask-mirror-talk-suggestions" class="amt-suggestions" style="display:none;">
                    <p class="amt-suggestions-label">Try asking about:</p>
                    <div class="amt-suggestions-list"></div>
                </div>
            </div>
        </div>
        <form id="ask-mirror-talk-form">
            <label for="ask-mirror-talk-input">What’s on your heart?</label>
            <textarea id="ask-mirror-talk-input" rows="3" placeholder="Ask a question..." autocomplete="off" autocapitalize="sentences" maxlength="500"></textarea>
            <div id="amt-char-counter" class="amt-char-counter" aria-live="polite">0 / 500</div>
            <button type="submit" id="ask-mirror-talk-submit">Ask</button>
        </form>
        <div class="ask-mirror-talk-response">
            <div class="amt-response-progress" id="amt-response-progress" aria-hidden="true"><div class="amt-response-progress-bar" id="amt-response-progress-bar"></div></div>
            <div class="amt-response-header">
                <h3>Response</h3>
                <button type="button" id="amt-copy-answer-btn" class="amt-copy-answer-btn" style="display:none;" title="Copy answer" aria-label="Copy answer">⎘ Copy</button>
            </div>
            <div id="ask-mirror-talk-output"></div>
            <div id="amt-mood-reactions" class="amt-mood-reactions" style="display:none;" aria-label="How did this land?"></div>
            <div id="amt-reflect-section" class="amt-reflect-section" style="display:none;"></div>
        </div>
        <div class="ask-mirror-talk-citations">
            <h3>Referenced Episodes</h3>
            <ul id="ask-mirror-talk-citations"></ul>
        </div>
        <div id="ask-mirror-talk-followups" class="amt-followups" style="display:none;">
            <p class="amt-followups-label">You might also want to ask:</p>
            <div class="amt-followups-list"></div>
        </div>
    </div>
    <!-- Onboarding overlay (rendered by JS on first visit) -->
    <div id="amt-onboarding-overlay" style="display:none;"></div>
    <?php
    return ob_get_clean();
}
add_shortcode('ask_mirror_talk', 'ask_mirror_talk_shortcode');

function ask_mirror_talk_enqueue_assets() {
    // Always enqueue on singular pages to handle page builders and dynamic content
    if (!is_singular()) {
        return;
    }

    $theme_uri = get_stylesheet_directory_uri();
    $version = '5.0.5'; // v5.0.5: cookie backup for gamification state (streak/XP survives iOS PWA reinstall)
    
    // Core styles
    wp_enqueue_style(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.css',
        array(),
        $version
    );
    
    // Enhanced UX styles
    wp_enqueue_style(
        'ask-mirror-talk-enhanced',
        $theme_uri . '/ask-mirror-talk-enhanced.css',
        array('ask-mirror-talk'),
        $version
    );
    
    // Core scripts
    wp_enqueue_script(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.js',
        array('jquery'),
        $version,
        true
    );
    
    // Enhanced UX scripts
    wp_enqueue_script(
        'ask-mirror-talk-enhanced',
        $theme_uri . '/ask-mirror-talk-enhanced.js',
        array('ask-mirror-talk'),
        $version,
        true
    );

    // Analytics add-on: citation click tracking + feedback buttons
    wp_enqueue_script(
        'ask-mirror-talk-analytics',
        $theme_uri . '/analytics-addon.js',
        array('ask-mirror-talk'),
        $version,
        true
    );

    wp_localize_script('ask-mirror-talk', 'AskMirrorTalk', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('ask_mirror_talk_nonce'),
        'apiUrl' => 'https://ask-mirror-talk-production.up.railway.app'
    ));
}
add_action('wp_enqueue_scripts', 'ask_mirror_talk_enqueue_assets');

/**
 * Remove WordPress core's wp_site_icon() output from wp_head.
 * WordPress injects its own apple-touch-icon and shortcut-icon tags based on
 * Settings → General → Site Icon, which would conflict with our custom PWA icons.
 */
add_action( 'init', function() {
    remove_action( 'wp_head', 'wp_site_icon', 99 );
} );

/**
 * PWA Support: manifest, meta tags, service worker registration, and Apple touch icons.
 *
 * iOS/Safari ignores the Web App Manifest entirely for home-screen icons.
 * It only reads <link rel="apple-touch-icon"> tags in <head>.
 * We provide device-specific sizes so every iPhone and iPad gets a pixel-perfect icon:
 *   180×180 — all modern iPhones (6 through 16)
 *   167×167 — iPad Pro (9.7", 10.5", 11", 12.9")
 *   152×152 — iPad / iPad mini
 * These PNGs are full-bleed squares (no pre-baked rounded corners) so iOS can apply
 * its own squircle clipping cleanly, identical to how Android uses the manifest icons.
 *
 * Android/Chrome/Edge/Samsung Internet read the manifest.json instead (served dynamically)
 * and use the 192/512 PNG icons which have our custom rounded corners baked in.
 */
function ask_mirror_talk_pwa_head() {
    $theme_uri = get_stylesheet_directory_uri();
    ?>
    <!-- PWA Manifest — served dynamically from /manifest.json with correct icon URLs -->
    <link rel="manifest" href="/manifest.json">

    <!-- Standard PWA meta tag (Android / Chrome) -->
    <meta name="theme-color" content="#943e08">
    <meta name="mobile-web-app-capable" content="yes">

    <!-- Apple PWA meta tags — makes "Add to Home Screen" launch as a standalone app -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Mirror Talk">
    <meta name="apple-touch-fullscreen" content="yes">

    <!--
        Apple Touch Icons — full-bleed squares, iOS clips to its own squircle shape.
        Largest first; iOS picks the best match for the current device.
        Using rel="apple-touch-icon" (not "precomposed") because iOS 7+ no longer
        adds gloss, and the default behaviour gives the best result on all devices.
    -->
    <link rel="apple-touch-icon" sizes="180x180" href="<?php echo esc_url($theme_uri . '/pwa-icon-180.png'); ?>">
    <link rel="apple-touch-icon" sizes="167x167" href="<?php echo esc_url($theme_uri . '/pwa-icon-167.png'); ?>">
    <link rel="apple-touch-icon" sizes="152x152" href="<?php echo esc_url($theme_uri . '/pwa-icon-152.png'); ?>">
    <!-- Fallback for very old iOS devices (<= iOS 6) -->
    <link rel="apple-touch-icon"                href="<?php echo esc_url($theme_uri . '/pwa-icon-180.png'); ?>">
    <?php
}
add_action('wp_head', 'ask_mirror_talk_pwa_head', 1);

/**
 * PWA: Serve service worker from root URL (/sw.js) with proper scope header.
 *
 * Browsers restrict SW scope to the directory the file is served from.
 * Since our SW lives in /wp-content/themes/astra/sw.js but needs scope "/",
 * we intercept the request very early (before WordPress routing) and serve
 * the file with the required Service-Worker-Allowed header.
 *
 * This approach does NOT rely on add_rewrite_rule (which requires flushing
 * permalinks and can conflict with LiteSpeed/LSCWP caching on Hostinger).
 * Instead, it hooks into 'init' and checks the raw REQUEST_URI.
 *
 * Alternative: place a physical sw.js file in the WordPress document root.
 */
function ask_mirror_talk_serve_sw() {
    // Parse the request URI and check if it's /sw.js (ignore query strings)
    $request_path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
    if ($request_path !== '/sw.js') {
        return;
    }

    $sw_file = get_stylesheet_directory() . '/sw.js';
    if (file_exists($sw_file)) {
        // Prevent any output buffering or caching from interfering
        while (ob_get_level()) {
            ob_end_clean();
        }

        http_response_code(200);
        header('Content-Type: application/javascript; charset=UTF-8');
        header('Service-Worker-Allowed: /');
        header('Cache-Control: no-cache, no-store, must-revalidate');
        header('Pragma: no-cache');
        header('Expires: 0');
        header('X-LiteSpeed-Cache-Control: no-cache'); // Bypass LiteSpeed/LSCWP server cache (Hostinger)
        header('X-Content-Type-Options: nosniff');
        readfile($sw_file);
        exit;
    }
}
add_action('init', 'ask_mirror_talk_serve_sw', 0); // Priority 0 = run first

/**
 * PWA: Serve manifest.json from root URL (/manifest.json).
 * Icons are injected dynamically so they always point to the correct child-theme URL,
 * regardless of what directory WordPress installs the theme in.
 */
function ask_mirror_talk_serve_manifest() {
    $request_path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
    if ($request_path !== '/manifest.json') {
        return;
    }

    $manifest_file = get_stylesheet_directory() . '/manifest.json';
    if ( ! file_exists($manifest_file) ) {
        return;
    }

    $theme_uri = rtrim( get_stylesheet_directory_uri(), '/' );

    $manifest = json_decode( file_get_contents($manifest_file), true );
    if ( ! $manifest ) {
        return;
    }

    // Always use the live child-theme URI for icons so paths survive theme renames
    $manifest['icons'] = [
        [
            'src'     => $theme_uri . '/pwa-icon-192.png',
            'sizes'   => '192x192',
            'type'    => 'image/png',
            'purpose' => 'any',
        ],
        [
            'src'     => $theme_uri . '/pwa-icon-192.png',
            'sizes'   => '192x192',
            'type'    => 'image/png',
            'purpose' => 'maskable',
        ],
        [
            'src'     => $theme_uri . '/pwa-icon-512.png',
            'sizes'   => '512x512',
            'type'    => 'image/png',
            'purpose' => 'any',
        ],
        [
            'src'     => $theme_uri . '/pwa-icon-512.png',
            'sizes'   => '512x512',
            'type'    => 'image/png',
            'purpose' => 'maskable',
        ],
        [
            'src'     => $theme_uri . '/pwa-icon.svg',
            'sizes'   => 'any',
            'type'    => 'image/svg+xml',
            'purpose' => 'any',
        ],
    ];

    while ( ob_get_level() ) {
        ob_end_clean();
    }

    http_response_code(200);
    header('Content-Type: application/manifest+json; charset=UTF-8');
    header('Cache-Control: public, max-age=86400');
    header('X-Content-Type-Options: nosniff');
    echo json_encode( $manifest, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT );
    exit;
}
add_action('init', 'ask_mirror_talk_serve_manifest', 0);

/**
 * PWA: Register service worker + enforce version on every page load.
 *
 * Strategy:
 * 1. Register with updateViaCache:'none' so the browser bypasses HTTP cache on update checks.
 * 2. Call reg.update() which bypasses the SW's own fetch handler (per SW spec).
 * 3. If no update was found (reg.installing/waiting are null) but the active SW
 *    still reports an old version via a message-channel query, we are in a
 *    hard server-side caching deadlock. Break it with a one-time hard reset:
 *    unregister all SWs, delete all caches, re-register, hard-reload.
 *    A localStorage flag (per target version) prevents infinite reload loops.
 */
function ask_mirror_talk_pwa_footer() {
    ?>
    <script>
    (function() {
        if (!('serviceWorker' in navigator) || !('caches' in window)) return;

        var SW_URL    = '/sw.js';
        var SW_TARGET = 'amt-v5.0.5';           // must match CACHE_VERSION in sw.js
        var RESET_KEY = 'amt_sw_reset_' + SW_TARGET;

        // Ask the active SW what version it is via a MessageChannel.
        // Resolves null if the SW has no handler (i.e. old version).
        function querySwVersion(active) {
            return new Promise(function(resolve) {
                var timer = setTimeout(function() { resolve(null); }, 1500);
                try {
                    var mc = new MessageChannel();
                    mc.port1.onmessage = function(e) {
                        clearTimeout(timer);
                        resolve(e.data && e.data.version ? e.data.version : null);
                    };
                    active.postMessage('GET_VERSION', [mc.port2]);
                } catch (e) { clearTimeout(timer); resolve(null); }
            });
        }

        async function enforceSW() {
            // Register (or update opts on existing registration)
            var reg = await navigator.serviceWorker.register(SW_URL, {
                scope: '/',
                updateViaCache: 'none'
            });

            // Trigger an update check that bypasses both the SW fetch handler
            // and (with updateViaCache:'none') the HTTP cache.
            await reg.update();

            // If an update was found it is now installing/waiting and skipWaiting()
            // will activate it. Nothing more needed.
            if (reg.installing || reg.waiting) {
                console.log('[PWA] SW update found — installing.');
                return;
            }

            // No update found via normal path. Check if the active SW is the
            // right version or if we are stuck in a server-caching deadlock.
            if (!reg.active) return;
            var version = await querySwVersion(reg.active);
            if (version === SW_TARGET) {
                console.log('[PWA] SW up-to-date:', version);
                return;
            }

            // Active SW is stale AND update check found nothing = deadlock.
            // Guard against reload loops with a per-version localStorage flag.
            var already;
            try { already = localStorage.getItem(RESET_KEY); } catch (e) {}
            if (already) {
                console.warn('[PWA] Hard reset already attempted for', SW_TARGET, '— giving up.');
                return;
            }
            try { localStorage.setItem(RESET_KEY, '1'); } catch (e) {}

            console.log('[PWA] Stale SW (', version, ') — hard reset to', SW_TARGET);

            // Unregister every SW registration on this origin.
            var regs = await navigator.serviceWorker.getRegistrations();
            await Promise.all(regs.map(function(r) { return r.unregister(); }));

            // Wipe all caches so nothing stale remains.
            var keys = await caches.keys();
            await Promise.all(keys.map(function(k) { return caches.delete(k); }));

            // Register fresh (no prior SW will interfere with the fetch).
            await navigator.serviceWorker.register(SW_URL, {
                scope: '/',
                updateViaCache: 'none'
            });

            // Hard-reload: forces the browser to fetch the HTML and all assets
            // fresh from the server with zero SW or cache involvement.
            window.location.reload(true);
        }

        window.addEventListener('load', function() {
            enforceSW().catch(function(err) {
                console.warn('[PWA] SW enforce error:', err);
            });
        });
    })();
    </script>
    <?php
}
add_action('wp_footer', 'ask_mirror_talk_pwa_footer', 99);

/**
 * AJAX endpoint to refresh expired nonces without a full page reload.
 * Called by the JS widget when it detects a 403 (stale nonce).
 */
function ask_mirror_talk_refresh_nonce() {
    wp_send_json_success(array(
        'nonce' => wp_create_nonce('ask_mirror_talk_nonce')
    ));
}
add_action('wp_ajax_ask_mirror_talk_refresh_nonce', 'ask_mirror_talk_refresh_nonce');
add_action('wp_ajax_nopriv_ask_mirror_talk_refresh_nonce', 'ask_mirror_talk_refresh_nonce');

function ask_mirror_talk_ajax_handler() {
    // Verify nonce — but return a clear error so the JS can auto-refresh
    if (!wp_verify_nonce($_POST['nonce'] ?? '', 'ask_mirror_talk_nonce')) {
        wp_send_json_error(array(
            'message' => 'Session expired. Retrying…',
            'code'    => 'nonce_expired'
        ), 403);
    }

    $question = isset($_POST['question']) ? sanitize_textarea_field($_POST['question']) : '';
    if (!$question) {
        wp_send_json_error(array('message' => 'Question cannot be empty.'), 400);
    }

    // Direct API call to Railway (no WPGetAPI dependency)
    $api_url = 'https://ask-mirror-talk-production.up.railway.app/ask';

    $response = wp_remote_post($api_url, array(
        'timeout' => 30,
        'headers' => array(
            'Content-Type' => 'application/json',
        ),
        'body' => json_encode(array(
            'question' => $question
        ))
    ));

    // Check for WordPress HTTP errors
    if (is_wp_error($response)) {
        error_log('Ask Mirror Talk API Error: ' . $response->get_error_message());
        wp_send_json_error(array(
            'message' => 'Could not connect to API server. Please try again later.'
        ), 500);
    }

    // Get response details
    $response_code = wp_remote_retrieve_response_code($response);
    $response_body = wp_remote_retrieve_body($response);

    // Check for HTTP errors
    if ($response_code !== 200) {
        error_log("Ask Mirror Talk API returned {$response_code}: {$response_body}");
        wp_send_json_error(array(
            'message' => 'API returned an error. Please try again later.'
        ), $response_code);
    }

    // Parse JSON response
    $data = json_decode($response_body, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log('Ask Mirror Talk JSON decode error: ' . json_last_error_msg());
        wp_send_json_error(array(
            'message' => 'Invalid response from API server.'
        ), 500);
    }

    // Return successful response
    wp_send_json_success($data);
}
add_action('wp_ajax_ask_mirror_talk', 'ask_mirror_talk_ajax_handler');
add_action('wp_ajax_nopriv_ask_mirror_talk', 'ask_mirror_talk_ajax_handler');
