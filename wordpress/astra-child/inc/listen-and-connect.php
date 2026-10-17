<?php
/** Persistent listening companion and intentional CTA dialogs. */
if (!defined('ABSPATH')) { exit; }

function mirrortalk_feed_tag_url($item, $tag_name) {
    $namespaces = array('https://podcastindex.org/namespace/1.0', 'https://podcastindex.org/namespace/1.0/');
    foreach ($namespaces as $namespace) {
        $tags = $item->get_item_tags($namespace, $tag_name);
        if (empty($tags[0]['attribs']['']['url'])) continue;
        return esc_url_raw($tags[0]['attribs']['']['url']);
    }
    return '';
}

function mirrortalk_get_feed_episodes($limit = 8, $force_refresh = false) {
    $cached = get_transient('mirrortalk_feed_episodes_v2');
    if (!$force_refresh && is_array($cached) && !empty($cached)) {
        return array_slice($cached, 0, $limit);
    }

    $last_good = get_option('mirrortalk_feed_episodes_last_good_v2', array());
    if (!$force_refresh && is_array($last_good) && !empty($last_good)) {
        if (!wp_next_scheduled('mirrortalk_refresh_podcast_feed')) {
            wp_schedule_single_event(time() + 10, 'mirrortalk_refresh_podcast_feed');
        }
        return array_slice($last_good, 0, $limit);
    }

    // Public and editor requests never wait on the remote RSS host. The first
    // refresh is queued and the UI uses its graceful empty/fallback state.
    if (!$force_refresh) {
        if (!wp_next_scheduled('mirrortalk_refresh_podcast_feed')) wp_schedule_single_event(time()+5, 'mirrortalk_refresh_podcast_feed');
        return array();
    }

    include_once ABSPATH . WPINC . '/feed.php';
    $feed_url = apply_filters(
        'mirrortalk_podcast_feed_url',
        get_theme_mod('mirrortalk_podcast_feed_url', 'https://anchor.fm/s/261b1464/podcast/rss')
    );
    $feed = fetch_feed($feed_url);
    if (is_wp_error($feed)) {
        return is_array($last_good) ? array_slice($last_good, 0, $limit) : array();
    }

    $episodes = array();
    foreach ($feed->get_items(0, $limit) as $item) {
        $enclosure = $item->get_enclosure();
        if (!$enclosure || !$enclosure->get_link()) {
            continue;
        }
        $episodes[] = array(
            'title' => wp_strip_all_tags($item->get_title()),
            'audio' => esc_url_raw($enclosure->get_link()),
            'permalink' => esc_url_raw($item->get_permalink()),
            'date' => $item->get_date('M j'),
            'duration' => method_exists($enclosure, 'get_duration') ? (string) $enclosure->get_duration() : '',
            'transcript' => mirrortalk_feed_tag_url($item, 'transcript'),
            'chapters' => mirrortalk_feed_tag_url($item, 'chapters'),
        );
    }

    if (!empty($episodes)) {
        set_transient('mirrortalk_feed_episodes_v2', $episodes, 6 * HOUR_IN_SECONDS);
        update_option('mirrortalk_feed_episodes_last_good_v2', $episodes, false);
    }
    return $episodes;
}

add_action('mirrortalk_refresh_podcast_feed', function () {mirrortalk_runtime_run('podcast_feed',function(){return mirrortalk_get_feed_episodes(8,true);},10*MINUTE_IN_SECONDS);});

function mirrortalk_render_listen_companion() {
    if (is_admin() || is_404() || isset($_GET['mirror_player']) || (function_exists('mirrortalk_is_editor_preview_request') && mirrortalk_is_editor_preview_request())) { return; }
    $episodes = mirrortalk_get_feed_episodes();
    if (empty($episodes)) { return; }
    $latest = $episodes[0];
    ?>
    <aside class="mt-listen" data-mt-listen data-ask-url="<?php echo esc_url(home_url('/ask-mirror-talk/')); ?>" aria-label="<?php esc_attr_e('Mirror Talk podcast player', 'astra-child'); ?>">
        <button class="mt-listen__launcher" type="button" data-mt-listen-toggle aria-expanded="false" aria-controls="mt-listen-panel">
            <span class="mt-listen__pulse" aria-hidden="true"><span>▶</span></span>
            <span><small><?php esc_html_e('Listen now', 'astra-child'); ?></small><strong><?php esc_html_e('Latest episode', 'astra-child'); ?></strong></span>
        </button>
        <section id="mt-listen-panel" class="mt-listen__panel" hidden>
            <header class="mt-listen__header">
                <div><p class="mt-section-kicker"><?php esc_html_e('The Living Mirror', 'astra-child'); ?></p><h2><?php esc_html_e('Carry the conversation with you.', 'astra-child'); ?></h2></div>
                <button type="button" class="mt-listen__close" data-mt-listen-close aria-label="<?php esc_attr_e('Close player', 'astra-child'); ?>">×</button>
            </header>
            <div class="mt-listen__now">
                <span class="mt-listen__art" aria-hidden="true"></span>
                <div><small data-mt-player-chapter><?php esc_html_e('Now selected', 'astra-child'); ?></small><strong data-mt-player-title><?php echo esc_html($latest['title']); ?></strong></div>
            </div>
            <audio data-mt-audio controls preload="metadata" src="<?php echo esc_url($latest['audio']); ?>"></audio>
            <div class="mt-listen__moment-actions" aria-label="<?php esc_attr_e('Living Mirror actions', 'astra-child'); ?>">
                <button type="button" data-mt-save-moment><?php esc_html_e('Save this moment', 'astra-child'); ?></button>
                <button type="button" data-mt-reflect-moment><?php esc_html_e('Reflect on this moment', 'astra-child'); ?></button>
            </div>
            <p class="mt-listen__moment-status" data-mt-moment-status role="status" aria-live="polite"></p>
            <section class="mt-living-transcript" data-mt-transcript-panel hidden aria-label="<?php esc_attr_e('Synchronized episode transcript', 'astra-child'); ?>">
                <div class="mt-living-transcript__heading"><strong><?php esc_html_e('Living transcript', 'astra-child'); ?></strong><small><?php esc_html_e('Follows the audio', 'astra-child'); ?></small></div>
                <div class="mt-living-transcript__cues" data-mt-transcript-cues tabindex="0"></div>
            </section>
            <button class="mt-listen__expand" type="button" data-mt-queue-toggle aria-expanded="false" aria-controls="mt-listen-queue">
                <span><?php esc_html_e('Choose another episode', 'astra-child'); ?></span><span aria-hidden="true">⌄</span>
            </button>
            <div id="mt-listen-queue" class="mt-listen__queue" hidden>
                <?php foreach ($episodes as $index => $episode) : ?>
                    <button type="button" class="mt-listen__episode<?php echo $index === 0 ? ' is-current' : ''; ?>" data-mt-episode data-audio="<?php echo esc_url($episode['audio']); ?>" data-title="<?php echo esc_attr($episode['title']); ?>" data-permalink="<?php echo esc_url($episode['permalink']); ?>" data-transcript="<?php echo esc_url(isset($episode['transcript']) ? $episode['transcript'] : ''); ?>" data-chapters="<?php echo esc_url(isset($episode['chapters']) ? $episode['chapters'] : ''); ?>">
                        <span class="mt-listen__episode-index"><?php echo esc_html(str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT)); ?></span>
                        <span><strong><?php echo esc_html($episode['title']); ?></strong><small><?php echo esc_html(trim($episode['date'] . ($episode['duration'] ? ' · ' . $episode['duration'] : ''))); ?></small></span>
                        <span aria-hidden="true">▶</span>
                    </button>
                <?php endforeach; ?>
            </div>
            <footer class="mt-listen__footer">
                <button class="mt-listen__continue" type="button" data-mt-popout data-player-url="<?php echo esc_url(home_url('/?mirror_player=1')); ?>"><?php esc_html_e('Keep playing while I browse', 'astra-child'); ?> ↗</button>
                <button type="button" data-mt-open-dialog="mt-follow-invite"><?php esc_html_e('Follow the podcast', 'astra-child'); ?></button>
                <button type="button" data-mt-open-dialog="mt-newsletter-invite"><?php esc_html_e('Join the newsletter', 'astra-child'); ?></button>
            </footer>
            <section class="mt-living-reflection" data-mt-reflection-workspace hidden aria-labelledby="mt-living-reflection-title">
                <header class="mt-living-reflection__header">
                    <div><p class="mt-section-kicker"><?php esc_html_e('The Living Mirror', 'astra-child'); ?></p><h2 id="mt-living-reflection-title"><?php esc_html_e('A reflection from this moment', 'astra-child'); ?></h2></div>
                    <button type="button" data-mt-reflection-back aria-label="<?php esc_attr_e('Return to the podcast player', 'astra-child'); ?>">←</button>
                </header>
                <div class="mt-living-reflection__context" data-mt-reflection-context></div>
                <div class="mt-living-reflection__answer" data-mt-reflection-answer role="status" aria-live="polite"></div>
                <div class="mt-living-reflection__followups" data-mt-reflection-followups hidden></div>
                <form class="mt-living-reflection__form" data-mt-reflection-form hidden>
                    <label for="mt-living-followup"><?php esc_html_e('Ask a follow-up', 'astra-child'); ?></label>
                    <textarea id="mt-living-followup" data-mt-reflection-input rows="2" maxlength="500" placeholder="<?php esc_attr_e('What would you like to understand more deeply?', 'astra-child'); ?>"></textarea>
                    <button type="submit"><?php esc_html_e('Continue reflecting', 'astra-child'); ?></button>
                </form>
                <div class="mt-living-reflection__actions">
                    <button type="button" data-mt-reflection-save hidden><?php esc_html_e('Save reflection', 'astra-child'); ?></button>
                    <button type="button" data-mt-reflection-back><?php esc_html_e('Return to listening', 'astra-child'); ?></button>
                </div>
                <p class="mt-living-reflection__privacy"><?php esc_html_e('Saved reflections remain privately on this device. This is reflective guidance, not therapy or emergency support.', 'astra-child'); ?></p>
            </section>
        </section>
    </aside>
    <?php
}
add_action('wp_footer', 'mirrortalk_render_listen_companion', 18);

function mirrortalk_render_invitation_dialogs() {
    if (is_admin() || is_404() || isset($_GET['mirror_player']) || (function_exists('mirrortalk_is_editor_preview_request') && mirrortalk_is_editor_preview_request())) { return; }
    $ask_url = home_url('/ask-mirror-talk/');
    $quick_paths = array(
        __('I need clarity', 'astra-child') => __('I need clarity. What might help me see my situation and next meaningful step more clearly?', 'astra-child'),
        __('I feel stuck', 'astra-child') => __('I feel stuck. What perspective from the Mirror Talk archive could help me move forward gently?', 'astra-child'),
        __('I need courage', 'astra-child') => __('I need courage for what comes next. What can I learn from the Mirror Talk conversations?', 'astra-child'),
        __('I am navigating change', 'astra-child') => __('I am navigating change. How can I meet this season with honesty, resilience and hope?', 'astra-child'),
        __('I am seeking purpose', 'astra-child') => __('I am questioning my purpose. What should I notice about the direction of my life?', 'astra-child'),
        __('Surprise me thoughtfully', 'astra-child') => __('Offer me a thoughtful question and a meaningful podcast moment for where I am today.', 'astra-child'),
    );
    ?>
    <dialog id="mt-ask-invite" class="mt-dialog" aria-labelledby="mt-ask-dialog-title">
        <button class="mt-dialog__close" type="button" data-mt-dialog-close aria-label="<?php esc_attr_e('Close', 'astra-child'); ?>">×</button>
        <p class="mt-section-kicker"><?php esc_html_e('A private reflection space', 'astra-child'); ?></p>
        <h2 id="mt-ask-dialog-title"><?php esc_html_e('What is on your heart?', 'astra-child'); ?></h2>
        <p><?php esc_html_e('Bring a real question. Ask Mirror Talk will help you explore it through relevant moments from the podcast archive.', 'astra-child'); ?></p>
        <div class="mt-living-paths" aria-label="<?php esc_attr_e('Quick reflection paths', 'astra-child'); ?>">
            <p><?php esc_html_e('What would help you today?', 'astra-child'); ?></p>
            <div><?php foreach ($quick_paths as $label => $prompt) : ?><a href="<?php echo esc_url(add_query_arg(array('intent' => 'living_mirror', 'prefill' => $prompt), $ask_url)); ?>"><?php echo esc_html($label); ?></a><?php endforeach; ?></div>
            <details><summary><?php esc_html_e('Why am I seeing these?', 'astra-child'); ?></summary><small><?php esc_html_e('These are gentle starting points, not assumptions about you. Nothing is selected until you choose it, and your saved journey stays on this device.', 'astra-child'); ?></small></details>
        </div>
        <a class="mt-button" href="<?php echo esc_url($ask_url); ?>"><?php esc_html_e('Begin a reflection', 'astra-child'); ?></a>
        <small><?php esc_html_e('Not therapy, medical advice or emergency support. You choose what to share.', 'astra-child'); ?></small>
    </dialog>
    <dialog id="mt-newsletter-invite" class="mt-dialog" aria-labelledby="mt-newsletter-dialog-title" data-mt-newsletter-dialog>
        <button class="mt-dialog__close" type="button" data-mt-dialog-close aria-label="<?php esc_attr_e('Close', 'astra-child'); ?>">×</button>
        <p class="mt-section-kicker"><?php esc_html_e('A thoughtful note, not more noise', 'astra-child'); ?></p>
        <h2 id="mt-newsletter-dialog-title"><?php esc_html_e('Keep a little wisdom close.', 'astra-child'); ?></h2>
        <p><?php esc_html_e('Receive new conversations, reflective prompts and carefully chosen ideas for living with greater clarity and intention.', 'astra-child'); ?></p>
        <form class="mt-newsletter-form" data-mt-newsletter-form novalidate>
            <div class="mt-newsletter-form__fields">
                <label><span><?php esc_html_e('First name', 'astra-child'); ?></span><input type="text" name="name" autocomplete="given-name" maxlength="80" required></label>
                <label><span><?php esc_html_e('Email address', 'astra-child'); ?></span><input type="email" name="email" autocomplete="email" maxlength="190" required></label>
            </div>
            <label class="mt-newsletter-form__consent"><input type="checkbox" name="consent" value="1" required> <span><?php esc_html_e('I would like to receive the Mirror Talk newsletter and can unsubscribe at any time.', 'astra-child'); ?></span></label>
            <input type="text" name="website" tabindex="-1" autocomplete="off" class="mt-newsletter-form__trap" aria-hidden="true">
            <p class="mt-newsletter-form__status" data-mt-newsletter-status role="status" aria-live="polite"></p>
            <div class="mt-newsletter-form__actions"><button class="mt-button" type="submit"><?php esc_html_e('Join the newsletter', 'astra-child'); ?></button><button class="mt-dialog__quiet" type="button" data-mt-dialog-close><?php esc_html_e('Not now', 'astra-child'); ?></button></div>
        </form>
    </dialog>
    <dialog id="mt-follow-invite" class="mt-dialog mt-dialog--wide" aria-labelledby="mt-follow-dialog-title">
        <button class="mt-dialog__close" type="button" data-mt-dialog-close aria-label="<?php esc_attr_e('Close', 'astra-child'); ?>">×</button>
        <p class="mt-section-kicker"><?php esc_html_e('Choose your way to stay connected', 'astra-child'); ?></p>
        <h2 id="mt-follow-dialog-title"><?php esc_html_e('Never miss a meaningful conversation.', 'astra-child'); ?></h2>
        <?php if (function_exists('mirrortalk_render_platform_cards')) mirrortalk_render_platform_cards('dialog'); ?>
        <div class="mt-follow-community" aria-label="<?php esc_attr_e('Community and supporter channels', 'astra-child'); ?>">
            <a href="<?php echo esc_url(mirrortalk_campaign_url('https://whatsapp.com/channel/0029VaEER5vC1Fu8V82fFm0u', 'community_cta', 'whatsapp')); ?>" target="_blank" rel="noopener"><?php esc_html_e('Join the WhatsApp channel', 'astra-child'); ?> <span aria-hidden="true">↗</span></a>
            <a href="<?php echo esc_url(mirrortalk_campaign_url('https://www.patreon.com/MirrorTalk', 'community_cta', 'patreon')); ?>" target="_blank" rel="noopener"><?php esc_html_e('Support Mirror Talk on Patreon', 'astra-child'); ?> <span aria-hidden="true">↗</span></a>
        </div>
        <p><a href="<?php echo esc_url(home_url('/listen/')); ?>"><?php esc_html_e('View every verified listening option', 'astra-child'); ?> →</a></p>
    </dialog>
    <?php
}
add_action('wp_footer', 'mirrortalk_render_invitation_dialogs', 19);

function mirrortalk_connection_customizer($customizer) {
    $customizer->add_section('mirrortalk_connections', array(
        'title' => __('Mirror Talk listening & connections', 'astra-child'),
        'priority' => 35,
    ));
    $customizer->add_setting('mirrortalk_podcast_feed_url', array(
        'default' => 'https://anchor.fm/s/261b1464/podcast/rss',
        'sanitize_callback' => 'esc_url_raw',
    ));
    $customizer->add_control('mirrortalk_podcast_feed_url', array(
        'section' => 'mirrortalk_connections',
        'label' => __('Podcast RSS feed URL', 'astra-child'),
        'type' => 'url',
    ));
}
add_action('customize_register', 'mirrortalk_connection_customizer');

function mirrortalk_register_newsletter_subscriber_type() {
    register_post_type('mt_subscriber', array(
        'labels' => array('name' => __('Newsletter subscribers', 'astra-child'), 'singular_name' => __('Newsletter subscriber', 'astra-child')),
        'public' => false,
        'show_ui' => current_user_can('manage_options'),
        'show_in_menu' => 'tools.php',
        'supports' => array('title'),
        'map_meta_cap' => true,
    ));
}
add_action('init', 'mirrortalk_register_newsletter_subscriber_type');

function mirrortalk_newsletter_client_ip() {
    $candidates = array('HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR');
    foreach ($candidates as $key) {
        if (empty($_SERVER[$key])) continue;
        $raw = sanitize_text_field(wp_unslash($_SERVER[$key]));
        $candidate = trim(explode(',', $raw)[0]);
        if (filter_var($candidate, FILTER_VALIDATE_IP)) return $candidate;
    }
    return 'unknown';
}

function mirrortalk_newsletter_rate_limit() {
    $network_key = hash_hmac('sha256', mirrortalk_newsletter_client_ip(), wp_salt('auth'));
    $windows = array(
        array('key' => 'mt_nl_min_' . $network_key, 'limit' => 3, 'ttl' => MINUTE_IN_SECONDS),
        array('key' => 'mt_nl_day_' . $network_key, 'limit' => 10, 'ttl' => DAY_IN_SECONDS),
    );
    foreach ($windows as $window) {
        $count = (int) get_transient($window['key']);
        if ($count >= $window['limit']) return false;
        set_transient($window['key'], $count + 1, $window['ttl']);
    }
    return true;
}

function mirrortalk_newsletter_generic_success() {
    wp_send_json_success(array('message' => __('Thank you. Please check your inbox to confirm your subscription.', 'astra-child')));
}

function mirrortalk_newsletter_signup() {
    check_ajax_referer('mirrortalk_newsletter_signup', 'nonce');
    $name = isset($_POST['name']) ? sanitize_text_field(wp_unslash($_POST['name'])) : '';
    $email = isset($_POST['email']) ? sanitize_email(wp_unslash($_POST['email'])) : '';
    $consent = isset($_POST['consent']) && sanitize_text_field(wp_unslash($_POST['consent'])) === '1';
    $trap = isset($_POST['website']) ? sanitize_text_field(wp_unslash($_POST['website'])) : '';
    $issued_at = isset($_POST['issued_at']) ? absint($_POST['issued_at']) : 0;
    $proof = isset($_POST['proof']) ? sanitize_text_field(wp_unslash($_POST['proof'])) : '';
    $expected_proof = hash_hmac('sha256', (string) $issued_at, wp_salt('nonce'));
    $form_age = time() - $issued_at;
    if ($trap) mirrortalk_newsletter_generic_success();
    if (!mirrortalk_newsletter_rate_limit()) wp_send_json_error(array('message' => __('Too many attempts. Please wait and try again later.', 'astra-child')), 429);
    if (!$issued_at || !hash_equals($expected_proof, $proof) || $form_age < 2 || $form_age > 7 * DAY_IN_SECONDS) wp_send_json_error(array('message' => __('Please refresh the page and try again.', 'astra-child')), 403);
    if (!$name || !is_email($email) || !$consent) wp_send_json_error(array('message' => __('Please enter your name, a valid email address and confirm your subscription.', 'astra-child')), 422);

    $existing = get_posts(array('post_type' => 'mt_subscriber', 'post_status' => array('private', 'publish'), 'meta_key' => '_mt_subscriber_email', 'meta_value' => strtolower($email), 'numberposts' => 1, 'fields' => 'ids'));
    if ($existing && get_post_meta($existing[0], '_mt_subscriber_confirmed_at', true)) mirrortalk_newsletter_generic_success();
    if (!$existing) {
        $subscriber_id = wp_insert_post(array('post_type' => 'mt_subscriber', 'post_status' => 'private', 'post_title' => $name));
        if (is_wp_error($subscriber_id) || !$subscriber_id) wp_send_json_error(array('message' => __('We could not save your subscription just now. Please try again.', 'astra-child')), 500);
        update_post_meta($subscriber_id, '_mt_subscriber_email', strtolower($email));
        update_post_meta($subscriber_id, '_mt_subscriber_consent_at', gmdate('c'));
        update_post_meta($subscriber_id, '_mt_subscriber_source', 'website_modal');
        update_post_meta($subscriber_id, '_mt_subscriber_source_path', wp_parse_url((string) wp_get_referer(), PHP_URL_PATH) ?: '/');
    } else {
        $subscriber_id = $existing[0];
    }
    $token = bin2hex(random_bytes(24));
    update_post_meta($subscriber_id, '_mt_subscriber_confirmation_hash', hash('sha256', $token));
    update_post_meta($subscriber_id, '_mt_subscriber_confirmation_expires', time() + 2 * DAY_IN_SECONDS);
    $confirm_url = add_query_arg(array('action' => 'mirrortalk_confirm_newsletter', 'subscriber' => $subscriber_id, 'token' => $token), admin_url('admin-post.php'));
    $subject = __('Confirm your Mirror Talk newsletter subscription', 'astra-child');
    $body = sprintf(__('Hello %1$s,\n\nPlease confirm that you would like to receive the Mirror Talk newsletter:\n%2$s\n\nIf you did not request this, you can safely ignore this message.', 'astra-child'), $name, $confirm_url);
    wp_mail($email, $subject, $body);
    mirrortalk_newsletter_generic_success();
}
add_action('wp_ajax_mirrortalk_newsletter_signup', 'mirrortalk_newsletter_signup');
add_action('wp_ajax_nopriv_mirrortalk_newsletter_signup', 'mirrortalk_newsletter_signup');

function mirrortalk_confirm_newsletter() {
    $subscriber_id = isset($_GET['subscriber']) ? absint($_GET['subscriber']) : 0;
    $token = isset($_GET['token']) ? sanitize_text_field(wp_unslash($_GET['token'])) : '';
    $stored = $subscriber_id ? (string) get_post_meta($subscriber_id, '_mt_subscriber_confirmation_hash', true) : '';
    $expires = $subscriber_id ? (int) get_post_meta($subscriber_id, '_mt_subscriber_confirmation_expires', true) : 0;
    if (!$subscriber_id || !$token || !$stored || $expires < time() || !hash_equals($stored, hash('sha256', $token))) {
        wp_safe_redirect(add_query_arg('newsletter', 'invalid', home_url('/'))); exit;
    }
    update_post_meta($subscriber_id, '_mt_subscriber_confirmed_at', gmdate('c'));
    delete_post_meta($subscriber_id, '_mt_subscriber_confirmation_hash');
    delete_post_meta($subscriber_id, '_mt_subscriber_confirmation_expires');
    if (function_exists('mirrortalk_intelligence_record_operational_event')) {
        mirrortalk_intelligence_record_operational_event('newsletter_subscribed', array(
            'path' => (string) get_post_meta($subscriber_id, '_mt_subscriber_source_path', true) ?: '/',
        ));
    }
    $name = get_the_title($subscriber_id); $email = get_post_meta($subscriber_id, '_mt_subscriber_email', true);
    wp_mail(get_option('admin_email'), __('Confirmed Mirror Talk newsletter subscriber', 'astra-child'), sprintf("Name: %s\nEmail: %s", $name, $email));
    wp_safe_redirect(add_query_arg('newsletter', 'confirmed', home_url('/'))); exit;
}
add_action('admin_post_mirrortalk_confirm_newsletter', 'mirrortalk_confirm_newsletter');
add_action('admin_post_nopriv_mirrortalk_confirm_newsletter', 'mirrortalk_confirm_newsletter');

function mirrortalk_render_player_window() {
    if (!isset($_GET['mirror_player']) || sanitize_text_field(wp_unslash($_GET['mirror_player'])) !== '1') {
        return;
    }
    status_header(200);
    nocache_headers();
    include get_stylesheet_directory() . '/player-window.php';
    exit;
}
add_action('template_redirect', 'mirrortalk_render_player_window', 0);
