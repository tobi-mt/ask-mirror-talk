<?php
/**
 * Astra Child Theme - Mirror Talk Edition
 * 
 * This child theme adds the Ask Mirror Talk widget to the Astra theme.
 * Child themes are upgrade-safe: parent theme updates won't affect this file.
 */

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}

function mirrortalk_is_staging_host() {
    $host = isset($_SERVER['HTTP_HOST']) ? strtolower((string) $_SERVER['HTTP_HOST']) : '';
    return preg_replace('/:\\d+$/', '', $host) === 'calm.mirrortalkpodcast.com';
}

/** Authenticated previews bypass caches and must stay off background work. */
function mirrortalk_is_editor_preview_request() {
    return isset($_GET['preview']) && filter_var(wp_unslash($_GET['preview']), FILTER_VALIDATE_BOOLEAN);
}

/** Trust documents are factual service pages, not articles to be recomposed. */
function mirrortalk_is_trust_page($post_id = 0) {
    $post_id = $post_id ? absint($post_id) : get_queried_object_id();
    if (!$post_id || get_post_type($post_id) !== 'page') return false;
    return in_array(get_post_field('post_name', $post_id), array('corrections', 'editorial-standards'), true);
}

function mirrortalk_trust_page_details($post_id) {
    $slug = (string) get_post_field('post_name', $post_id);
    if ($slug === 'corrections') {
        return array(
            'eyebrow' => __('Accountability', 'astra-child'),
            'summary' => __('How Mirror Talk reviews evidence, corrects material errors and clearly records what changed.', 'astra-child'),
            'aside_title' => __('Request a correction', 'astra-child'),
            'aside_copy' => __('Please identify the page, the statement concerned and a reliable supporting source. Every specific request is reviewed with care.', 'astra-child'),
            'aside_label' => __('Contact the editorial team', 'astra-child'),
            'aside_url' => home_url('/contact/'),
        );
    }
    return array(
        'eyebrow' => __('Trust & transparency', 'astra-child'),
        'summary' => __('The principles that guide Mirror Talk’s original conversations, editorial decisions, attribution and reader care.', 'astra-child'),
        'aside_title' => __('Our editorial promise', 'astra-child'),
        'aside_copy' => __('We value accuracy, clear attribution, independence and transparent corrections. Automated tools may support quality checks but never invent editorial facts.', 'astra-child'),
        'aside_label' => __('Read our corrections policy', 'astra-child'),
        'aside_url' => home_url('/corrections/'),
    );
}

if (mirrortalk_is_editor_preview_request()) remove_action('init', 'wp_cron');
add_action('send_headers', function () { if (mirrortalk_is_editor_preview_request()) header('X-Mirror-Talk-Preview-Mode: fast'); }, 1000);

// Staging must be a reliable review surface, not a three-day collection of
// browser-specific page-cache variants.
if (mirrortalk_is_staging_host() && !defined('DONOTCACHEPAGE')) {
    define('DONOTCACHEPAGE', true);
}

function mirrortalk_staging_cache_headers($headers) {
    if (!mirrortalk_is_staging_host()) return $headers;
    $headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0';
    $headers['Pragma'] = 'no-cache';
    $headers['Expires'] = 'Wed, 11 Jan 1984 05:00:00 GMT';
    $headers['X-LiteSpeed-Cache-Control'] = 'no-cache';
    $headers['CDN-Cache-Control'] = 'no-store';
    $headers['Surrogate-Control'] = 'no-store';
    return $headers;
}
add_filter('wp_headers', 'mirrortalk_staging_cache_headers', 999);

function mirrortalk_disable_staging_page_cache() {
    if (mirrortalk_is_staging_host()) do_action('litespeed_control_set_nocache', 'Mirror Talk staging review');
}
add_action('template_redirect', 'mirrortalk_disable_staging_page_cache', 0);

function mirrortalk_purge_release_caches() {
    $version = (string) wp_get_theme()->get('Version');
    if (get_option('mirrortalk_delivered_theme_version') === $version) return;
    do_action('litespeed_purge_all');
    do_action('litespeed_purge_url', home_url('/'));
    if (function_exists('wp_cache_flush')) wp_cache_flush();
    update_option('mirrortalk_delivered_theme_version', $version, false);
}
add_action('init', 'mirrortalk_purge_release_caches', 1);
add_action('admin_init', 'mirrortalk_purge_release_caches', 1);

function mirrortalk_asset_version($relative_path) {
    $path = get_stylesheet_directory() . '/' . ltrim($relative_path, '/');
    $modified = file_exists($path) ? (string) filemtime($path) : '0';
    return (string) wp_get_theme()->get('Version') . '.' . $modified;
}

/**
 * Enqueue parent theme stylesheet
 * This loads the parent Astra theme's CSS before the child theme's CSS
 */
// Astra already enqueues its generated `astra-theme-css`. Loading the parent
// style.css again adds another request without providing the dynamic design CSS.

/**
 * Mirror Talk theme foundations.
 *
 * The child theme deliberately keeps Astra as its compatibility layer while
 * owning the visual system, editor defaults and public-facing templates.
 */
function mirrortalk_theme_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('responsive-embeds');
    add_theme_support('editor-styles');
    add_theme_support('wp-block-styles');
    add_theme_support('align-wide');
    add_theme_support(
        'html5',
        array('search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script')
    );

    add_editor_style('mirror-talk-site.css');
}
add_action('after_setup_theme', 'mirrortalk_theme_setup');

/**
 * Load Ask Mirror Talk widget
 * This file contains the shortcode, AJAX handlers, and PWA setup
 */
require_once get_stylesheet_directory() . '/ask-mirror-talk.php';
require_once get_stylesheet_directory() . '/inc/runtime-resilience.php';
require_once get_stylesheet_directory() . '/inc/production-hardening.php';
require_once get_stylesheet_directory() . '/inc/journey.php';
require_once get_stylesheet_directory() . '/inc/listen-and-connect.php';
require_once get_stylesheet_directory() . '/inc/listen-everywhere.php';
require_once get_stylesheet_directory() . '/inc/link-hub.php';
require_once get_stylesheet_directory() . '/inc/youtube-studio.php';
require_once get_stylesheet_directory() . '/inc/intelligence-seo.php';
require_once get_stylesheet_directory() . '/inc/seo-platform.php';
require_once get_stylesheet_directory() . '/inc/search-connectors.php';
require_once get_stylesheet_directory() . '/inc/ai-visibility.php';
require_once get_stylesheet_directory() . '/inc/intelligence-dashboard.php';
require_once get_stylesheet_directory() . '/inc/seo-learning.php';
require_once get_stylesheet_directory() . '/inc/knowledge-quality.php';
require_once get_stylesheet_directory() . '/inc/page-one-growth.php';
require_once get_stylesheet_directory() . '/inc/intelligence-pipeline.php';
require_once get_stylesheet_directory() . '/inc/editorial-composer.php';
require_once get_stylesheet_directory() . '/inc/editorial-composer-v2.php';
require_once get_stylesheet_directory() . '/inc/guarded-taxonomy.php';
require_once get_stylesheet_directory() . '/inc/editorial-story-studio.php';
require_once get_stylesheet_directory() . '/inc/rss-editorial-ingestion.php';
require_once get_stylesheet_directory() . '/inc/editorial-presentations.php';
require_once get_stylesheet_directory() . '/inc/content-normalizer.php';
require_once get_stylesheet_directory() . '/inc/elementor-migration.php';
require_once get_stylesheet_directory() . '/inc/navigation.php';
require_once get_stylesheet_directory() . '/inc/contact-forms.php';

/**
 * Consistency mode: full-site service workers created several independent HTML
 * generations across Safari, Chromium and installed PWAs. The podcast site is
 * network-first, so release consistency is more valuable than offline pages.
 */
remove_action('wp_footer', 'ask_mirror_talk_pwa_footer', 99);

function mirrortalk_release_version() {
    return (string) wp_get_theme()->get('Version');
}

function mirrortalk_release_headers($headers) {
    $headers['X-Mirror-Talk-Release'] = mirrortalk_release_version();
    return $headers;
}
add_filter('wp_headers', 'mirrortalk_release_headers', 1000);

function mirrortalk_release_marker() {
    $version = mirrortalk_release_version();
    echo '<meta name="mirror-talk-release" content="' . esc_attr($version) . '">';
    ?>
    <script id="mirror-talk-release-consistency">
    (function () {
      var release = <?php echo wp_json_encode($version); ?>;
      try {
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.getRegistrations().then(function (registrations) {
            return Promise.all(registrations.map(function (registration) { return registration.unregister(); }));
          }).then(function () {
            if (!navigator.serviceWorker.controller) return;
            var key = 'mt_release_reloaded_' + release;
            if (!sessionStorage.getItem(key)) {
              sessionStorage.setItem(key, '1');
              window.location.reload();
            }
          }).catch(function () {});
        }
        if ('caches' in window) {
          caches.keys().then(function (keys) {
            return Promise.all(keys.filter(function (key) { return key.indexOf('amt-') === 0 || key.indexOf('amt_') === 0; }).map(function (key) { return caches.delete(key); }));
          }).catch(function () {});
        }
        localStorage.setItem('mt_active_release', release);
      } catch (e) {}
    }());
    </script>
    <?php
}
add_action('wp_head', 'mirrortalk_release_marker', 0);

function mirrortalk_preload_home_art() {
    if (!is_front_page()) return;
    $art = get_stylesheet_directory_uri() . '/assets/art/mirror-talk-hero-atmosphere-1600.avif';
    echo '<link rel="preload" as="image" type="image/avif" fetchpriority="high" href="' . esc_url($art) . '">';
}
add_action('wp_head', 'mirrortalk_preload_home_art', 2);

function mirrortalk_serve_release_manifest() {
    $path = parse_url(isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '', PHP_URL_PATH);
    if ($path !== '/mirror-talk-release.json') return;
    while (ob_get_level()) ob_end_clean();
    nocache_headers();
    header('Content-Type: application/json; charset=UTF-8');
    header('X-Mirror-Talk-Release: ' . mirrortalk_release_version());
    echo wp_json_encode(array(
        'release' => mirrortalk_release_version(),
        'theme' => 'astra-child',
        'generated_at' => gmdate('c'),
        'consistency_mode' => true,
    ));
    exit;
}
add_action('init', 'mirrortalk_serve_release_manifest', -1);

add_action('wp_enqueue_scripts', 'mirrortalk_child_enqueue_styles', 20);
function mirrortalk_child_enqueue_styles() {
    wp_enqueue_style(
        'astra-child-style',
        get_stylesheet_uri(),
        array('astra-theme-css'),
        mirrortalk_asset_version('style.css')
    );

    wp_enqueue_style(
        'mirror-talk-site',
        get_stylesheet_directory_uri() . '/mirror-talk-site.css',
        array('astra-child-style'),
        mirrortalk_asset_version('mirror-talk-site.css')
    );

    wp_enqueue_script(
        'mirror-talk-site',
        get_stylesheet_directory_uri() . '/mirror-talk-site.js',
        array(),
        mirrortalk_asset_version('mirror-talk-site.js'),
        true
    );

    wp_script_add_data('mirror-talk-site', 'strategy', 'defer');
    wp_localize_script('mirror-talk-site', 'MirrorTalkSite', array(
        'apiBase' => 'https://ask-mirror-talk-production.up.railway.app',
    ));

    wp_enqueue_script(
        'mirror-talk-listen-connect',
        get_stylesheet_directory_uri() . '/listen-connect.js',
        array(),
        mirrortalk_asset_version('listen-connect.js'),
        true
    );
    wp_script_add_data('mirror-talk-listen-connect', 'strategy', 'defer');
    wp_enqueue_script(
        'mirror-talk-listen-everywhere',
        get_stylesheet_directory_uri() . '/listen-everywhere.js',
        array(),
        mirrortalk_asset_version('listen-everywhere.js'),
        true
    );
    wp_script_add_data('mirror-talk-listen-everywhere', 'strategy', 'defer');
    $newsletter_issued_at = time();
    wp_localize_script('mirror-talk-listen-connect', 'MirrorTalkNewsletter', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('mirrortalk_newsletter_signup'),
        'issuedAt' => $newsletter_issued_at,
        'proof' => hash_hmac('sha256', (string) $newsletter_issued_at, wp_salt('nonce')),
    ));
    wp_localize_script('mirror-talk-listen-connect', 'MirrorTalkLiving', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('ask_mirror_talk_nonce'),
    ));
}

function mirrortalk_streamline_owned_home_assets() {
    $owned_surface = is_front_page()
        || (bool) get_query_var('mirror_listen')
        || (bool) get_query_var('mirror_blog')
        || (bool) get_query_var('mirror_topic');
    if (!$owned_surface || (is_front_page() && !empty($_GET['legacy_home']))) return;
    $styles = array(
        'jetpack-forms-layout', 'hostinger-reach-subscription-block', 'mediaelement',
        'wp-mediaelement', 'contact-form-7', 'astra-contact-form-7',
        'uagb-block-positioning-css', 'uagb-slick-css', 'uagb-aos-css',
        'uag-style-296', 'aioseo/css/src/vue/standalone/blocks/table-of-contents/global.scss',
        'wp-block-library', 'wp-block-library-theme',
    );
    $scripts = array(
        'jquery-migrate', 'jp-tracks', 'jp-tracks-functions', 'swv', 'contact-form-7',
        'starter-templates-zip-preview', 'hostinger-reach-embed', 'uagb-block-positioning-js',
        'uagb-counter-js', 'uagb-countUp-js', 'uagb-button-child-js', 'uagb-testimonial-js',
        'uagb-imagesloaded', 'uagb-slick-js', 'uagb-aos-js', 'uagb-animation-js',
        'uag-script-296', 'mediaelement-core', 'mediaelement-migrate',
        'jetpack-block-podcast-player',
    );
    foreach ($styles as $handle) wp_dequeue_style($handle);
    foreach ($scripts as $handle) wp_dequeue_script($handle);

    // Spectra may register per-post generated handles whose names cannot be
    // known in advance. Archive queries can enqueue dozens of those files even
    // though the owned templates render their own cards instead of block HTML.
    foreach (array(wp_styles(), wp_scripts()) as $registry) {
        foreach ((array) $registry->queue as $handle) {
            $registered = $registry->registered[$handle] ?? null;
            $source = $registered ? (string) $registered->src : '';
            if (strpos($source, '/uploads/uag-plugin/assets/') === false) continue;
            $registry instanceof WP_Styles ? wp_dequeue_style($handle) : wp_dequeue_script($handle);
        }
    }
}
add_action('wp_enqueue_scripts', 'mirrortalk_streamline_owned_home_assets', PHP_INT_MAX);

/**
 * Remove front-end assets that have no matching component in the document.
 * This runs after plugin enqueues and never affects wp-admin or logged-in tools.
 */
function mirrortalk_frontend_performance_assets() {
    if (is_admin()) return;
    if (!is_admin_bar_showing()) {
        wp_dequeue_style('admin-bar');
        wp_dequeue_style('dashicons');
    }
    $content = is_singular() ? (string) get_post_field('post_content', get_queried_object_id()) : '';
    $uses_paypal = strpos($content, 'wp:jetpack/paypal') !== false || has_shortcode($content, 'jetpack-paypal');
    if (!$uses_paypal) {
        $styles = wp_styles();
        foreach ((array) $styles->queue as $handle) {
            $registered = $styles->registered[$handle] ?? null;
            if ($registered && strpos((string) $registered->src, 'jetpack-paypal-payments') !== false) wp_dequeue_style($handle);
        }
    }
}
add_action('wp_enqueue_scripts', 'mirrortalk_frontend_performance_assets', PHP_INT_MAX);

/**
 * Form plugins enqueue their full front-end stacks site-wide. Preserve those
 * assets wherever the document actually contains a supported form, but remove
 * them from ordinary articles and pages. This also prevents the anti-spam
 * challenge runtime from blocking the main thread on content-only visits.
 */
function mirrortalk_streamline_singular_form_assets() {
    if (!is_singular(array('post', 'page'))) return;
    $content = (string) get_post_field('post_content', get_queried_object_id());
    $uses = array(
        'cf7' => (bool) preg_match('/(?:\[contact-form-7\b|wp:contact-form-7\b|class=["\'][^"\']*wpcf7)/i', $content),
        'wpforms' => (bool) preg_match('/(?:\[wpforms\b|wp:wpforms\b|class=["\'][^"\']*wpforms)/i', $content),
        'mc4wp' => (bool) preg_match('/(?:\[mc4wp_form\b|class=["\'][^"\']*mc4wp)/i', $content),
        'sureforms' => (bool) preg_match('/(?:\[sureforms\b|wp:sureforms\b|class=["\'][^"\']*sureforms)/i', $content),
        'jetpack' => strpos($content, 'wp:jetpack/contact-form') !== false,
        'hostinger' => (bool) preg_match('/(?:wp:hostinger-reach\b|class=["\'][^"\']*hostinger-reach)/i', $content),
    );

    // These editor/preview runtimes are never required by a public document.
    wp_dequeue_script('starter-templates-zip-preview');
    if (!$uses['cf7']) {
        foreach (array('contact-form-7', 'astra-contact-form-7') as $handle) wp_dequeue_style($handle);
        foreach (array('swv', 'contact-form-7') as $handle) wp_dequeue_script($handle);
    }
    if (!$uses['jetpack']) wp_dequeue_style('jetpack-forms-layout');
    if (!$uses['hostinger']) {
        wp_dequeue_style('hostinger-reach-subscription-block');
        wp_dequeue_script('hostinger-reach-embed');
    }
    // Prosopo may protect Mailchimp, WPForms or SureForms; retain it only when
    // one of those form families is genuinely rendered by this document.
    if (!$uses['mc4wp'] && !$uses['wpforms'] && !$uses['sureforms']) wp_dequeue_script('prosopo-procaptcha');
}
add_action('wp_enqueue_scripts', 'mirrortalk_streamline_singular_form_assets', PHP_INT_MAX);

/**
 * Stop legacy Elementor YouTube widgets from loading/autoplaying before the
 * visitor asks. The guard replaces only YouTube widgets, leaving stored content
 * and editor output untouched, and upgrades them to youtube-nocookie on click.
 */
function mirrortalk_enqueue_legacy_video_guard() {
    if (!is_singular(array('post', 'page'))) return;
    $post_id = get_queried_object_id();
    $content = (string) get_post_field('post_content', $post_id);
    $elementor_data = (string) get_post_meta($post_id, '_elementor_data', true);
    $has_rendered_widget = stripos($content, 'elementor-widget-video') !== false && stripos($content, 'youtu') !== false;
    $has_elementor_widget = stripos($elementor_data, '"widgetType":"video"') !== false && stripos($elementor_data, 'youtu') !== false;
    if (!$has_rendered_widget && !$has_elementor_widget) return;
    wp_enqueue_script(
        'mirror-talk-legacy-video-guard',
        get_stylesheet_directory_uri() . '/legacy-video-guard.js',
        array(),
        mirrortalk_asset_version('legacy-video-guard.js'),
        false
    );
}
add_action('wp_enqueue_scripts', 'mirrortalk_enqueue_legacy_video_guard', 1);

function mirrortalk_enqueue_owned_widgets() {
    if (!is_singular(array('post','page'))) return;
    $content=(string)get_post_field('post_content',get_queried_object_id());
    if (strpos($content,'data-mt-owned-slider')===false) return;
    wp_enqueue_script('mirror-talk-owned-widgets',get_stylesheet_directory_uri().'/owned-widgets.js',array(),mirrortalk_asset_version('owned-widgets.js'),true);
    wp_script_add_data('mirror-talk-owned-widgets','strategy','defer');
}
add_action('wp_enqueue_scripts','mirrortalk_enqueue_owned_widgets',25);

add_filter('astra_the_title_enabled', function ($enabled) {
    return is_home() ? false : $enabled;
});
