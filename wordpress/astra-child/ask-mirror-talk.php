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

function ask_mirror_talk_theme_version() {
    return '5.5.6';
}

function ask_mirror_talk_shortcode() {
    ob_start();
    ?>
    <div class="ask-mirror-talk">
        <div class="amt-heading-row">
            <div class="amt-heading-copy">
                <p class="amt-heading-kicker">Premium reflection, grounded in real episodes</p>
                <h2>Ask Mirror Talk</h2>
                <p class="amt-heading-subtitle">Bring a question. Get a calm, thoughtful answer shaped by the Mirror Talk library and anchored with trusted references.</p>
                <div class="amt-heading-trust-strip" aria-label="Why people trust Ask Mirror Talk">
                    <span class="amt-heading-trust-pill">Private by default</span>
                    <span class="amt-heading-trust-pill">Real episode references</span>
                </div>
            </div>
            <div class="amt-heading-controls">
                <button type="button" id="amt-text-size-btn" class="amt-text-size-btn" title="Change text size" aria-label="Change text size">Aa</button>
                <button type="button" id="amt-journal-btn" class="amt-journal-btn" title="My reflection notes" aria-label="My reflection notes">📓</button>
                <button type="button" id="amt-about-btn" class="amt-about-btn" title="About this app" aria-label="About Mirror Talk">ⓘ</button>
                <div class="amt-heading-controls-note">Saved notes live in <strong>📓</strong></div>
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
            <button type="button" class="amt-insights-btn" id="amt-insights-btn" title="My saved insights" aria-label="My saved insights"><span aria-hidden="true">🔖</span><span class="screen-reader-text"> Saved insights</span></button>                <button type="button" class="amt-notif-manage-btn" id="amt-notif-manage-btn" title="Notification settings" style="display:none;" aria-expanded="false"><span aria-hidden="true">🔔</span><span class="screen-reader-text"> Notification settings</span></button>
        </div>
        <div id="amt-insights-panel" class="amt-insights-panel" style="display:none;" role="region" aria-label="My saved insights"></div>
        <div id="amt-streak-protect-banner" class="amt-streak-protect-banner" style="display:none;" role="status"></div>
        <div id="amt-streak-revival-card" class="amt-streak-revival-card" style="display:none;" role="region" aria-label="Streak recovery"></div>
        <div id="amt-notif-manage-panel" class="amt-notif-manage-panel" style="display:none;" aria-label="Notification settings"></div>
        <div id="amt-badge-shelf" class="amt-badge-shelf" style="display:none;"></div>
        <div id="amt-milestone-toast" class="amt-milestone-toast" style="display:none;"></div>
        <div id="amt-journey-card" class="amt-journey-card" style="display:none;" role="region" aria-label="Continue your reflection"></div>
        <div id="amt-weekly-recap" class="amt-weekly-recap" style="display:none;" role="region" aria-label="Weekly reflection recap"></div>
        <!-- About modal -->
        <div id="amt-about-modal" class="amt-about-modal" style="display:none;" role="dialog" aria-modal="true" aria-label="About Mirror Talk"></div>
        <!-- Journal modal -->
        <div id="amt-journal-modal" class="amt-journal-modal" style="display:none;" role="dialog" aria-modal="true" aria-label="My reflection notes"></div>
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
            <div class="amt-form-intro">
                <div>
                    <p class="amt-form-kicker">Start your reflection</p>
                    <label for="ask-mirror-talk-input">What’s on your heart?</label>
                </div>
                <p class="amt-form-note">Best for personal, honest questions. We’ll surface the strongest episode moments we can find and show you where the answer came from.</p>
            </div>
            <textarea id="ask-mirror-talk-input" rows="3" placeholder="Ask what you are carrying, questioning, or trying to understand..." autocomplete="off" autocapitalize="sentences" maxlength="500"></textarea>
            <div id="amt-question-coach" class="amt-question-coach" style="display:none;" aria-live="polite"></div>
            <div class="amt-form-footer">
                <div id="amt-char-counter" class="amt-char-counter" aria-live="polite">0 / 500</div>
                <button type="submit" id="ask-mirror-talk-submit">Ask Mirror Talk</button>
            </div>
        </form>
        <div class="ask-mirror-talk-response">
            <div class="amt-response-progress" id="amt-response-progress" aria-hidden="true"><div class="amt-response-progress-bar" id="amt-response-progress-bar"></div></div>
            <div class="amt-response-header">
                <h3>Your Reflection</h3>
                <button type="button" id="amt-copy-answer-btn" class="amt-copy-answer-btn" style="display:none;" title="Copy answer" aria-label="Copy answer">⎘ Copy</button>
            </div>
            <div id="amt-answer-context" class="amt-answer-context" style="display:none;"></div>
            <div id="ask-mirror-talk-output"></div>
            <div id="amt-continuation-strip" class="amt-continuation-strip" style="display:none;" aria-label="Next steps"></div>
            <div id="amt-answer-utilities" class="amt-answer-utilities"></div>
            <div id="amt-mood-reactions" class="amt-mood-reactions" style="display:none;" aria-label="How did this land?"></div>
            <div id="amt-reflect-section" class="amt-reflect-section" style="display:none;"></div>
        </div>
        <div class="ask-mirror-talk-citations">
            <h3>Verify The Answer</h3>
            <div id="amt-citation-trust-note" class="amt-citation-trust-note" style="display:none;"></div>
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
    $version = ask_mirror_talk_theme_version(); // v5.5.6: validates source-grounded reflection card text before sharing
    
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
    
    // Keep the optional enhanced JS layer disabled for now while we stabilize
    // the core widget runtime.

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

    <!-- Explicit viewport keeps iOS standalone/PWA rendering pinned to device width -->
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">

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
 * PWA: Serve the SW-init script from /sw-init (no .js extension) with strict no-cache headers.
 *
 * Root problem: Old service workers treat any .js URL as a static asset
 * (cacheFirstWithUpdate), which means /sw-init.js was intercepted and potentially
 * served from cache even with a versioned query string.
 *
 * Fix v5.1.7: rename endpoint to /sw-init (no extension). Old SWs only call
 * event.respondWith() for static assets (.js/.css/etc), API calls, and HTML.
 * /sw-init matches none of those patterns, so the fetch handler returns without
 * intercepting — the browser fetches it directly from the network every time.
 * This is guaranteed to work for ALL old SW versions, even pre-5.0.8.
 */
function ask_mirror_talk_serve_sw_init() {
    $request_path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
    if ($request_path !== '/sw-init') {
        return;
    }

    // Must match CACHE_VERSION in sw.js.
    $sw_ver = ask_mirror_talk_theme_version();
    $sw_url = '/sw.js?v=' . $sw_ver;

    while (ob_get_level()) {
        ob_end_clean();
    }

    http_response_code(200);
    header('Content-Type: application/javascript; charset=UTF-8');
    header('Cache-Control: no-cache, no-store, must-revalidate');
    header('Pragma: no-cache');
    header('Expires: 0');
    header('X-LiteSpeed-Cache-Control: no-cache'); // Prevent LiteSpeed from caching this ever
    header('X-Content-Type-Options: nosniff');

    echo "(function() {
  if (!('serviceWorker' in navigator)) return;

  var SW_VER = '{$sw_ver}';
  var SW_URL = '{$sw_url}';
  var isStandalone = false;

  try {
    isStandalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) ||
      window.navigator.standalone === true;
  } catch (e) {}

  // Clean up stale RESET_KEY flags written by the 5.0.4 strategy
  try {
    Object.keys(localStorage).forEach(function(k) {
      if (k.indexOf('amt_sw_reset_') === 0) localStorage.removeItem(k);
    });
  } catch (e) {}

  async function enforceSW() {
    async function canLoadScript(url) {
      try {
        var res = await fetch(url, {
          method: 'GET',
          cache: 'no-store',
          credentials: 'same-origin'
        });
        return res.ok;
      } catch (e) {
        return false;
      }
    }

    var allRegs = await navigator.serviceWorker.getRegistrations();
    var hasActiveRegistration = allRegs.some(function(r) {
      return !!(r && (r.active || r.waiting || r.installing));
    });

    var targetUrl = SW_URL;
    if (!(await canLoadScript(targetUrl))) {
      targetUrl = '/sw.js';
      if (!(await canLoadScript(targetUrl))) {
        if (hasActiveRegistration || navigator.serviceWorker.controller) {
          console.info('[PWA] Keeping existing service worker; latest script is not reachable yet');
          return;
        }
        throw new TypeError('Service worker script unavailable');
      }
      console.info('[PWA] Falling back to unversioned service worker URL');
    }

    // Unregister any SW at a different script URL (old version or old URL format)
    var unregisteredAny = false;
    await Promise.all(allRegs.map(function(r) {
      var sw = r.active || r.installing || r.waiting;
      var url = sw ? sw.scriptURL : '';
      var matchesVersioned = url.indexOf('v=' + SW_VER) !== -1;
      var matchesFallback = targetUrl === '/sw.js' && /\/sw\.js(?:\?|$)/.test(url);
      if (!matchesVersioned && !matchesFallback) {
        console.log('[PWA] Unregistering stale SW:', url || '(unknown)');
        unregisteredAny = true;
        return r.unregister();
      }
      return Promise.resolve();
    }));

    // Register at versioned URL — LiteSpeed cache miss guaranteed
    var reg = await navigator.serviceWorker.register(targetUrl, {
      scope: '/',
      updateViaCache: 'none'
    });

    // Reload when new SW activates. Works on iOS Safari PWA where client.navigate() is unreliable.
    // Uses two hooks to cover all timing scenarios:
    //  1. reg.installing/waiting — already set when register() resolves (first install or update)
    //  2. updatefound — fires when update() finds a newer SW and starts installing it
    function watchWorker(worker) {
      if (!worker) return;
      worker.addEventListener('statechange', function() {
        if (worker.state === 'activated') {
          console.log('[PWA] New SW activated — reloading page');
          try {
            if (!sessionStorage.getItem('amt_sw_reloaded')) {
              sessionStorage.setItem('amt_sw_reloaded', '1');
              window.location.reload();
            }
          } catch(e) { window.location.reload(); }
        }
      });
    }

    // Hook 1: already-installing worker (covers first registration after unregister)
    watchWorker(reg.installing || reg.waiting);

    // Hook 2: future updatefound (covers update() detecting a newer script)
    reg.addEventListener('updatefound', function() { watchWorker(reg.installing); });

    // Belt-and-suspenders update check (bypasses SW fetch handler per spec)
    await reg.update();

    console.log('[PWA] SW enforce complete. State:',
      reg.installing ? 'installing' :
      reg.waiting    ? 'waiting'    :
      reg.active     ? 'active'     : 'unknown');
  }

  async function passiveUpdate() {
    try {
      var regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map(function(reg) { return reg.update(); }));
      console.log('[PWA] Passive SW update check complete');
    } catch (err) {
      console.info('[PWA] Passive SW update skipped:', err && err.message ? err.message : err);
    }
  }

  var lastEnforceAt = 0;
  function enforceSWSafely() {
    var now = Date.now();
    if (now - lastEnforceAt < 30000) return;
    lastEnforceAt = now;

    if (!isStandalone && navigator.serviceWorker.controller) {
      passiveUpdate();
      return;
    }

    enforceSW().catch(function(err) {
      if (navigator.serviceWorker.controller) {
        console.info('[PWA] SW enforce skipped; existing worker remains active');
        return;
      }
      console.warn('[PWA] SW enforce error:', err);
    });
  }

  window.addEventListener('load', enforceSWSafely);
  window.addEventListener('pageshow', enforceSWSafely);
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
      enforceSWSafely();
    }
  });
})();";
    exit;
}
add_action('init', 'ask_mirror_talk_serve_sw_init', 0);

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
    header('Cache-Control: no-cache, must-revalidate');
    header('X-Content-Type-Options: nosniff');
    echo json_encode( $manifest, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT );
    exit;
}
add_action('init', 'ask_mirror_talk_serve_manifest', 0);

/**
 * PWA: Load SW-init script from the dedicated no-cache PHP endpoint.
 *
 * IMPORTANT: the ?v= query string MUST be bumped with every release.
 *
 * Why: /sw-init has no .js extension, so old SWs (all versions) pass the request
 * straight through to the network — never intercepted, never cached by any SW.
 * The ?v= query string additionally bypasses LiteSpeed's HTTP cache.
 * The combination guarantees every visit fetches a fresh PHP response.
 */
function ask_mirror_talk_pwa_footer() {
    $sw_init_ver = ask_mirror_talk_theme_version();
    ?>
    <script src="/sw-init?v=<?php echo esc_attr($sw_init_ver); ?>" defer></script>
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
