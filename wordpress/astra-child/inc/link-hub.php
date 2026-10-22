<?php
/** First-party Linktree and Linkfire replacement. */
if (!defined('ABSPATH')) { exit; }

define('MIRRORTALK_LINK_HUB_VERSION', '1.1.0');

function mirrortalk_link_hub_route() {
    add_rewrite_rule('^listen-connect/?$', 'index.php?mirror_links=1', 'top');
    add_rewrite_rule('^links/?$', 'index.php?mirror_links_legacy=1', 'top');
}
add_action('init', 'mirrortalk_link_hub_route');
add_filter('query_vars', function ($vars) { $vars[] = 'mirror_links'; $vars[] = 'mirror_links_legacy'; return $vars; });
add_action('template_redirect', function () {
    if (!get_query_var('mirror_links_legacy')) return;
    wp_safe_redirect(home_url('/listen-connect/'), 301, 'Mirror Talk');
    exit;
}, 1);
add_filter('body_class', function ($classes) {
    if (get_query_var('mirror_links')) $classes[] = 'mt-link-hub-page';
    return $classes;
});

add_filter('template_include', function ($template) {
    if (!get_query_var('mirror_links')) return $template;
    global $wp_query;
    $wp_query->is_404 = false;
    $wp_query->is_page = true;
    $wp_query->is_home = false;
    status_header(200);
    $owned = get_stylesheet_directory() . '/link-hub.php';
    return is_readable($owned) ? $owned : $template;
}, 96);

function mirrortalk_link_hub_refresh_route() {
    $version = function_exists('mirrortalk_release_version') ? mirrortalk_release_version() : MIRRORTALK_LINK_HUB_VERSION;
    if (get_option('mirrortalk_link_hub_route_version') === $version) return;
    flush_rewrite_rules(false);
    update_option('mirrortalk_link_hub_route_version', $version, false);
    if (function_exists('mirrortalk_indexnow_queue_url')) mirrortalk_indexnow_queue_url(home_url('/listen-connect/'));
}
add_action('after_switch_theme', 'mirrortalk_link_hub_refresh_route', 61);
add_action('admin_init', 'mirrortalk_link_hub_refresh_route', 61);

function mirrortalk_link_hub_assets() {
    if (!get_query_var('mirror_links')) return;
    wp_enqueue_style('mirror-talk-link-hub', get_stylesheet_directory_uri() . '/link-hub.css', array('mirror-talk-site'), mirrortalk_asset_version('link-hub.css'));
    wp_enqueue_script('mirror-talk-link-hub', get_stylesheet_directory_uri() . '/link-hub.js', array(), mirrortalk_asset_version('link-hub.js'), true);
    wp_script_add_data('mirror-talk-link-hub', 'strategy', 'defer');
}
add_action('wp_enqueue_scripts', 'mirrortalk_link_hub_assets', 35);

add_action('wp_head', function () {
    if (!get_query_var('mirror_links')) return;
    echo '<link rel="preload" as="image" href="' . esc_url(get_stylesheet_directory_uri() . '/assets/art/mirror-talk-cover-art.jpg') . '" fetchpriority="high">' . "\n";
}, 1);

function mirrortalk_link_hub_action_url($url, $content) {
    return function_exists('mirrortalk_campaign_url')
        ? mirrortalk_campaign_url($url, 'link_in_bio', $content)
        : $url;
}

function mirrortalk_link_hub_duration_label($value) {
    $value = trim((string) $value);
    if ($value === '') return '';
    if (preg_match('/^\d{1,2}:\d{2}(?::\d{2})?$/', $value)) return $value;
    if (!ctype_digit($value)) return sanitize_text_field($value);
    $seconds = (int) $value;
    if ($seconds < 60) return sprintf(_n('%d second', '%d seconds', $seconds, 'astra-child'), $seconds);
    $minutes = (int) floor($seconds / 60);
    if ($minutes < 60) return sprintf(__('%d min', 'astra-child'), $minutes);
    $hours = (int) floor($minutes / 60);
    $remaining = $minutes % 60;
    return $remaining ? sprintf(__('%1$d hr %2$d min', 'astra-child'), $hours, $remaining) : sprintf(_n('%d hour', '%d hours', $hours, 'astra-child'), $hours);
}

/**
 * Compact latest-video module for the first-party listen-and-connect hub.
 *
 * The global cinematic Studio is deliberately suppressed on this route. This
 * smaller renderer uses the same proven privacy, playback and Intelligence
 * engine without duplicating the large footer presentation.
 */
function mirrortalk_render_link_hub_youtube() {
    if (!function_exists('mirrortalk_latest_youtube_video')) return;
    if (!(bool) get_theme_mod('mirrortalk_youtube_enabled', true)) return;
    $video = mirrortalk_latest_youtube_video();
    if (!is_array($video) || empty($video['id']) || !preg_match('/^[A-Za-z0-9_-]{11}$/', (string) $video['id'])) return;

    wp_enqueue_script(
        'mirror-talk-youtube-studio',
        get_stylesheet_directory_uri() . '/youtube-studio.js',
        array(),
        function_exists('mirrortalk_asset_version') ? mirrortalk_asset_version('youtube-studio.js') : wp_get_theme()->get('Version'),
        true
    );
    wp_script_add_data('mirror-talk-youtube-studio', 'strategy', 'defer');

    $channel_url = 'https://www.youtube.com/channel/' . MIRRORTALK_YOUTUBE_CHANNEL_ID;
    $is_short = stripos((string) ($video['title'] ?? ''), '#short') !== false || stripos((string) ($video['url'] ?? ''), '/shorts/') !== false;
    $thumbnail = !empty($video['thumbnail']) ? esc_url($video['thumbnail']) : '';
    ?>
    <section class="mt-youtube-studio mt-youtube-studio--link-hub<?php echo $is_short ? ' is-short' : ''; ?>" data-mt-youtube-studio data-video-id="<?php echo esc_attr($video['id']); ?>" data-video-title="<?php echo esc_attr($video['title']); ?>" data-video-thumbnail="<?php echo esc_url($video['thumbnail']); ?>" aria-labelledby="mt-link-hub-youtube-title">
        <div class="mt-youtube-studio__inner">
            <div class="mt-youtube-studio__copy">
                <p class="mt-section-kicker"><?php esc_html_e('Latest from the studio', 'astra-child'); ?></p>
                <h2 id="mt-link-hub-youtube-title"><?php esc_html_e('Watch the conversation.', 'astra-child'); ?></h2>
                <h3><?php echo esc_html($video['title']); ?></h3>
                <div class="mt-youtube-studio__actions">
                    <button type="button" class="mt-button" data-mt-youtube-sound hidden><?php esc_html_e('Turn sound on', 'astra-child'); ?></button>
                    <a href="<?php echo esc_url(mirrortalk_link_hub_action_url($video['url'], 'latest-youtube-video')); ?>" target="_blank" rel="noopener" data-mt-link-hub-action="youtube-video"><?php esc_html_e('Watch on YouTube', 'astra-child'); ?> ↗</a>
                    <a href="<?php echo esc_url(mirrortalk_link_hub_action_url($channel_url, 'youtube-subscribe')); ?>" target="_blank" rel="noopener" data-mt-link-hub-action="youtube-subscribe"><?php esc_html_e('Subscribe', 'astra-child'); ?> ↗</a>
                </div>
                <p class="mt-youtube-studio__status" data-mt-youtube-status role="status" aria-live="polite"></p>
            </div>
            <div class="mt-youtube-studio__media" data-mt-youtube-media<?php echo $thumbnail ? ' style="background-image:url(&quot;' . esc_attr($thumbnail) . '&quot;)"' : ''; ?>>
                <div class="mt-youtube-studio__poster" data-mt-youtube-poster<?php echo $thumbnail ? ' style="background-image:linear-gradient(rgba(13,9,16,.58),rgba(13,9,16,.76)),url(&quot;' . esc_attr($thumbnail) . '&quot;)"' : ''; ?>>
                    <span aria-hidden="true">▶</span>
                    <strong><?php esc_html_e('Watch quietly', 'astra-child'); ?></strong>
                    <p><?php esc_html_e('The YouTube player loads only when you choose. Playback begins muted.', 'astra-child'); ?></p>
                    <button type="button" data-mt-youtube-consent><?php esc_html_e('Play latest video', 'astra-child'); ?></button>
                </div>
                <div class="mt-youtube-studio__player" data-mt-youtube-player></div>
            </div>
        </div>
    </section>
    <?php
}

/** Only destinations already published by Mirror Talk are included. */
function mirrortalk_link_hub_connections() {
    return array(
        array('id'=>'whatsapp','label'=>__('Join our WhatsApp channel','astra-child'),'detail'=>__('Conversation, updates and community','astra-child'),'url'=>'https://whatsapp.com/channel/0029VaEER5vC1Fu8V82fFm0u','mark'=>'WA'),
        array('id'=>'youtube','label'=>__('Watch on YouTube','astra-child'),'detail'=>__('Interviews, reflections and Shorts','astra-child'),'url'=>'https://www.youtube.com/channel/UCFj3nBFVYJhsEGciiu52eEw/','mark'=>'YT'),
        array('id'=>'patreon','label'=>__('Support Mirror Talk','astra-child'),'detail'=>__('Help thoughtful conversations continue','astra-child'),'url'=>'https://www.patreon.com/MirrorTalk','mark'=>'P'),
        array('id'=>'instagram','label'=>__('Follow on Instagram','astra-child'),'detail'=>__('Ideas and moments from the conversations','astra-child'),'url'=>'https://www.instagram.com/mirrortalk.podcast/','mark'=>'IG'),
        array('id'=>'facebook','label'=>__('Join our Facebook family','astra-child'),'detail'=>__('Connect with the wider community','astra-child'),'url'=>'https://www.facebook.com/MirrorTalkPodcast','mark'=>'FB'),
        array('id'=>'x','label'=>__('Follow on X','astra-child'),'detail'=>__('New conversations and concise insights','astra-child'),'url'=>'https://twitter.com/mirrortalkTO','mark'=>'X'),
    );
}

function mirrortalk_link_hub_schema($schema) {
    if (!get_query_var('mirror_links') || !is_array($schema)) return $schema;
    $url = home_url('/listen-connect/');
    $items = array(); $position = 1;
    foreach (function_exists('mirrortalk_listen_platforms') ? mirrortalk_listen_platforms(true) : array() as $platform) {
        if (($platform['id'] ?? '') === 'rss') continue;
        $items[] = array('@type'=>'ListItem','position'=>$position++,'name'=>$platform['name'],'url'=>$platform['url']);
    }
    foreach (mirrortalk_link_hub_connections() as $link) $items[] = array('@type'=>'ListItem','position'=>$position++,'name'=>$link['label'],'url'=>$link['url']);
    $schema['@graph'][] = array(
        '@type'=>'CollectionPage', '@id'=>$url . '#webpage', 'url'=>$url,
        'name'=>'Mirror Talk — Listen, Reflect & Connect',
        'description'=>mirrortalk_seo_description(),
        'isPartOf'=>array('@id'=>home_url('/') . '#website'),
        'about'=>array('@id'=>home_url('/') . '#podcast'),
        'mainEntity'=>array('@type'=>'ItemList','name'=>'Official Mirror Talk destinations','itemListElement'=>$items),
    );
    return $schema;
}
add_filter('mirrortalk_schema_graph', 'mirrortalk_link_hub_schema', 25);

