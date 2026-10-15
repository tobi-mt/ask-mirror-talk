<?php
/**
 * From the Mirror Talk Studio.
 *
 * A privacy-aware, server-cached latest YouTube upload module. The initial
 * document contains no YouTube iframe or thumbnail request. Visitors explicitly
 * allow external media once; muted in-view autoplay can then continue on later
 * pages without weakening the site's first-party analytics promise.
 */
if (!defined('ABSPATH')) { exit; }

define('MIRRORTALK_YOUTUBE_CHANNEL_ID', 'UCFj3nBFVYJhsEGciiu52eEw');
define('MIRRORTALK_YOUTUBE_CACHE_KEY', 'mirrortalk_latest_youtube_v1');
define('MIRRORTALK_YOUTUBE_LAST_GOOD_KEY', 'mirrortalk_latest_youtube_last_good_v1');

function mirrortalk_youtube_fallback_video() {
    $saved = get_option(MIRRORTALK_YOUTUBE_LAST_GOOD_KEY, array());
    if (is_array($saved) && !empty($saved['id']) && preg_match('/^[A-Za-z0-9_-]{11}$/', $saved['id'])) return $saved;
    // A bundled, known-good channel upload keeps the experience useful during
    // the very first request if YouTube's public feed is temporarily unavailable.
    return array(
        'checked' => true,
        'id' => 'EMq-NadNUGw',
        'title' => __('Why you need to talk to yourself #selflove #mirror #shorts', 'astra-child'),
        'url' => 'https://www.youtube.com/shorts/EMq-NadNUGw',
        'published' => '',
        'thumbnail' => 'https://i.ytimg.com/vi/EMq-NadNUGw/hqdefault.jpg',
    );
}

function mirrortalk_youtube_video_id($url) {
    $url = trim((string) $url);
    if (preg_match('~(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/))([A-Za-z0-9_-]{11})~i', $url, $matches)) {
        return $matches[1];
    }
    return preg_match('/^[A-Za-z0-9_-]{11}$/', $url) ? $url : '';
}

function mirrortalk_youtube_feed_video($force_refresh = false) {
    $cached = get_transient(MIRRORTALK_YOUTUBE_CACHE_KEY);
    if (!$force_refresh && is_array($cached) && isset($cached['checked'])) return !empty($cached['id']) ? $cached : mirrortalk_youtube_fallback_video();
    $last_good = get_option(MIRRORTALK_YOUTUBE_LAST_GOOD_KEY, array());
    if (!$force_refresh && is_array($last_good) && !empty($last_good['id'])) {
        if (!wp_next_scheduled('mirrortalk_refresh_youtube_feed')) wp_schedule_single_event(time() + 15, 'mirrortalk_refresh_youtube_feed');
        return $last_good;
    }
    if (!$force_refresh) {
        if (!wp_next_scheduled('mirrortalk_refresh_youtube_feed')) wp_schedule_single_event(time()+5, 'mirrortalk_refresh_youtube_feed');
        return mirrortalk_youtube_fallback_video();
    }

    $channel_id = sanitize_text_field((string) get_theme_mod('mirrortalk_youtube_channel_id', MIRRORTALK_YOUTUBE_CHANNEL_ID));
    if (!preg_match('/^UC[A-Za-z0-9_-]{20,30}$/', $channel_id)) $channel_id = MIRRORTALK_YOUTUBE_CHANNEL_ID;
    $feed_url = add_query_arg('channel_id', rawurlencode($channel_id), 'https://www.youtube.com/feeds/videos.xml');
    $response = wp_safe_remote_get($feed_url, array(
        'timeout' => 7,
        'redirection' => 2,
        'user-agent' => 'Mirror Talk WordPress/' . wp_get_theme()->get('Version'),
    ));
    if (is_wp_error($response) || wp_remote_retrieve_response_code($response) !== 200) {
        $fallback = mirrortalk_youtube_fallback_video();
        set_transient(MIRRORTALK_YOUTUBE_CACHE_KEY, $fallback, 15 * MINUTE_IN_SECONDS);
        return $fallback;
    }

    $body = wp_remote_retrieve_body($response);
    $video = array();
    if (function_exists('simplexml_load_string')) {
        $previous = libxml_use_internal_errors(true);
        $xml = simplexml_load_string($body, 'SimpleXMLElement', LIBXML_NONET | LIBXML_NOCDATA);
        libxml_clear_errors();
        libxml_use_internal_errors($previous);
        if ($xml && isset($xml->entry[0])) {
            $entry = $xml->entry[0];
            $youtube = $entry->children('http://www.youtube.com/xml/schemas/2015');
            $media = $entry->children('http://search.yahoo.com/mrss/');
            $id = sanitize_text_field((string) $youtube->videoId);
            $thumbnail = '';
            if (isset($media->group->thumbnail)) {
                $attributes = $media->group->thumbnail->attributes();
                $thumbnail = esc_url_raw((string) $attributes['url']);
            }
            if (preg_match('/^[A-Za-z0-9_-]{11}$/', $id)) {
                $link = isset($entry->link) ? esc_url_raw((string) $entry->link['href']) : '';
                $video = array(
                    'checked' => true,
                    'id' => $id,
                    'title' => sanitize_text_field(wp_strip_all_tags((string) $entry->title)),
                    'url' => $link ?: 'https://www.youtube.com/watch?v=' . $id,
                    'published' => sanitize_text_field((string) $entry->published),
                    'thumbnail' => $thumbnail ?: 'https://i.ytimg.com/vi/' . $id . '/hqdefault.jpg',
                );
            }
        }
    }
    if ($video) {
        set_transient(MIRRORTALK_YOUTUBE_CACHE_KEY, $video, 3 * HOUR_IN_SECONDS);
        update_option(MIRRORTALK_YOUTUBE_LAST_GOOD_KEY, $video, false);
        return $video;
    }
    $fallback = mirrortalk_youtube_fallback_video();
    set_transient(MIRRORTALK_YOUTUBE_CACHE_KEY, $fallback, 15 * MINUTE_IN_SECONDS);
    return $fallback;
}

add_action('mirrortalk_refresh_youtube_feed', function () {
    mirrortalk_runtime_run('youtube_feed',function(){return mirrortalk_youtube_feed_video(true);},10*MINUTE_IN_SECONDS);
});

function mirrortalk_latest_youtube_video() {
    $override = esc_url_raw((string) get_theme_mod('mirrortalk_youtube_pinned_url', ''));
    $override_id = mirrortalk_youtube_video_id($override);
    if ($override_id) {
        return array(
            'id' => $override_id,
            'title' => __('A recent conversation from Mirror Talk', 'astra-child'),
            'url' => 'https://www.youtube.com/watch?v=' . $override_id,
            'published' => '',
            'thumbnail' => 'https://i.ytimg.com/vi/' . $override_id . '/hqdefault.jpg',
        );
    }
    return mirrortalk_youtube_feed_video();
}

function mirrortalk_youtube_surface() {
    if (is_admin() || is_404() || is_search() || isset($_GET['mirror_player']) || (function_exists('mirrortalk_is_editor_preview_request') && mirrortalk_is_editor_preview_request())) return '';
    if (function_exists('mirrortalk_is_trust_page') && mirrortalk_is_trust_page()) return '';
    if (!(bool) get_theme_mod('mirrortalk_youtube_enabled', true)) return '';
    if (is_page(array('ask-mirror-talk', 'insights')) || is_page_template('answer-archive-template.php')) return '';
    if (is_singular(array('post','page')) && function_exists('mirrortalk_story_studio_settings')) {
        $story_settings = mirrortalk_story_studio_settings(get_queried_object_id());
        $story_decisions = function_exists('mirrortalk_composer_v2_decisions') ? mirrortalk_composer_v2_decisions(get_queried_object_id()) : array();
        if (!empty($story_settings['enabled']) && ($story_settings['youtube_mode']??'latest') !== 'none' && !empty($story_decisions['youtube_player']['enabled'])) return '';
    }
    if (is_front_page()) return 'cinematic';
    if (is_singular('post')) return 'article';
    if (is_home() || is_archive() || get_query_var('mirror_topic')) return 'compact';
    return is_page() ? 'compact' : '';
}

function mirrortalk_render_youtube_studio() {
    $surface = mirrortalk_youtube_surface();
    if (!$surface) return;
    $video = mirrortalk_latest_youtube_video();
    $channel_url = 'https://www.youtube.com/channel/' . MIRRORTALK_YOUTUBE_CHANNEL_ID;
    if (empty($video['id'])) {
        ?>
        <section class="mt-youtube-studio mt-youtube-studio--invitation" aria-labelledby="mt-youtube-title">
            <div class="mt-youtube-studio__inner">
                <div class="mt-youtube-studio__copy">
                    <p class="mt-section-kicker"><?php esc_html_e('From the Mirror Talk Studio', 'astra-child'); ?></p>
                    <h2 id="mt-youtube-title"><?php esc_html_e('Watch. Reflect. Continue.', 'astra-child'); ?></h2>
                    <p><?php esc_html_e('Discover our latest films, conversations and short reflections on YouTube.', 'astra-child'); ?></p>
                    <a class="mt-button" href="<?php echo esc_url($channel_url); ?>" target="_blank" rel="noopener"><?php esc_html_e('Visit Mirror Talk on YouTube', 'astra-child'); ?> ↗</a>
                </div>
            </div>
        </section>
        <?php
        return;
    }

    wp_enqueue_script(
        'mirror-talk-youtube-studio',
        get_stylesheet_directory_uri() . '/youtube-studio.js',
        array(),
        function_exists('mirrortalk_asset_version') ? mirrortalk_asset_version('youtube-studio.js') : wp_get_theme()->get('Version'),
        true
    );
    wp_script_add_data('mirror-talk-youtube-studio', 'strategy', 'defer');
    $is_short = stripos($video['title'], '#short') !== false || stripos($video['url'], '/shorts/') !== false;
    ?>
    <section class="mt-youtube-studio mt-youtube-studio--<?php echo esc_attr($surface); ?><?php echo $is_short ? ' is-short' : ''; ?>" data-mt-youtube-studio data-video-id="<?php echo esc_attr($video['id']); ?>" data-video-title="<?php echo esc_attr($video['title']); ?>" data-video-thumbnail="<?php echo esc_url($video['thumbnail']); ?>" aria-labelledby="mt-youtube-title">
        <div class="mt-youtube-studio__inner">
            <div class="mt-youtube-studio__copy">
                <p class="mt-section-kicker"><?php esc_html_e('From the Mirror Talk Studio', 'astra-child'); ?></p>
                <h2 id="mt-youtube-title"><?php echo esc_html($surface === 'cinematic' ? __('Watch what moves you.', 'astra-child') : __('Watch. Reflect. Continue.', 'astra-child')); ?></h2>
                <p class="mt-youtube-studio__latest"><?php esc_html_e('Latest on YouTube', 'astra-child'); ?></p>
                <h3><?php echo esc_html($video['title']); ?></h3>
                <p><?php esc_html_e('A visual moment for clarity, curiosity and meaningful growth. Sound remains off until you choose otherwise.', 'astra-child'); ?></p>
                <div class="mt-youtube-studio__actions">
                    <button type="button" class="mt-button" data-mt-youtube-sound hidden><?php esc_html_e('Turn sound on', 'astra-child'); ?></button>
                    <a href="<?php echo esc_url($video['url']); ?>" target="_blank" rel="noopener"><?php esc_html_e('Watch on YouTube', 'astra-child'); ?> ↗</a>
                    <a href="<?php echo esc_url($channel_url); ?>" target="_blank" rel="noopener"><?php esc_html_e('Subscribe', 'astra-child'); ?> ↗</a>
                </div>
                <p class="mt-youtube-studio__status" data-mt-youtube-status role="status" aria-live="polite"></p>
            </div>
            <div class="mt-youtube-studio__media" data-mt-youtube-media>
                <div class="mt-youtube-studio__poster" data-mt-youtube-poster>
                    <span aria-hidden="true">▶</span>
                    <strong><?php esc_html_e('Your privacy comes first', 'astra-child'); ?></strong>
                    <p><?php esc_html_e('YouTube is external media. Allow it once on this device to play this and future videos automatically when they enter view—always muted first.', 'astra-child'); ?></p>
                    <button type="button" data-mt-youtube-consent><?php esc_html_e('Allow and play video', 'astra-child'); ?></button>
                </div>
                <div class="mt-youtube-studio__player" data-mt-youtube-player></div>
            </div>
        </div>
    </section>
    <?php
}

function mirrortalk_youtube_customize($customizer) {
    $customizer->add_section('mirrortalk_youtube_studio', array(
        'title' => __('Mirror Talk YouTube Studio', 'astra-child'),
        'priority' => 42,
        'description' => __('Automatically presents the newest channel upload. A pinned URL temporarily overrides the feed.', 'astra-child'),
    ));
    $customizer->add_setting('mirrortalk_youtube_enabled', array('default' => true, 'sanitize_callback' => 'rest_sanitize_boolean'));
    $customizer->add_control('mirrortalk_youtube_enabled', array('section' => 'mirrortalk_youtube_studio', 'label' => __('Show the YouTube Studio module', 'astra-child'), 'type' => 'checkbox'));
    $customizer->add_setting('mirrortalk_youtube_channel_id', array('default' => MIRRORTALK_YOUTUBE_CHANNEL_ID, 'sanitize_callback' => 'sanitize_text_field'));
    $customizer->add_control('mirrortalk_youtube_channel_id', array('section' => 'mirrortalk_youtube_studio', 'label' => __('YouTube channel ID', 'astra-child'), 'type' => 'text'));
    $customizer->add_setting('mirrortalk_youtube_pinned_url', array('default' => '', 'sanitize_callback' => 'esc_url_raw'));
    $customizer->add_control('mirrortalk_youtube_pinned_url', array('section' => 'mirrortalk_youtube_studio', 'label' => __('Pinned YouTube video URL (optional)', 'astra-child'), 'type' => 'url'));
}
add_action('customize_register', 'mirrortalk_youtube_customize');
add_action('customize_save_after', function () { delete_transient(MIRRORTALK_YOUTUBE_CACHE_KEY); });
