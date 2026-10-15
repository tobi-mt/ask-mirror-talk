<?php
/** First-party Mirror Talk contact experience. */
if (!defined('ABSPATH')) { exit; }

function mirrortalk_register_contact_message_type() {
    register_post_type('mt_contact_message', array(
        'labels' => array(
            'name' => __('Contact messages', 'astra-child'),
            'singular_name' => __('Contact message', 'astra-child'),
            'menu_name' => __('Contact messages', 'astra-child'),
        ),
        'public' => false,
        'show_ui' => current_user_can('manage_options'),
        'show_in_menu' => 'tools.php',
        'supports' => array('title', 'editor'),
        'capability_type' => 'post',
        'map_meta_cap' => true,
    ));
}
add_action('init', 'mirrortalk_register_contact_message_type');

function mirrortalk_contact_rate_limit() {
    $ip = function_exists('mirrortalk_newsletter_client_ip') ? mirrortalk_newsletter_client_ip() : sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR'] ?? 'unknown'));
    $key = hash_hmac('sha256', (string) $ip, wp_salt('auth'));
    foreach (array(
        array('key' => 'mt_contact_hour_' . $key, 'limit' => 5, 'ttl' => HOUR_IN_SECONDS),
        array('key' => 'mt_contact_day_' . $key, 'limit' => 15, 'ttl' => DAY_IN_SECONDS),
    ) as $window) {
        $count = (int) get_transient($window['key']);
        if ($count >= $window['limit']) return false;
        set_transient($window['key'], $count + 1, $window['ttl']);
    }
    return true;
}

function mirrortalk_contact_generic_success() {
    wp_send_json_success(array('message' => __('Thank you. Your message has reached Mirror Talk.', 'astra-child')));
}

function mirrortalk_contact_submit() {
    check_ajax_referer('mirrortalk_contact_submit', 'nonce');
    $name = sanitize_text_field(wp_unslash($_POST['name'] ?? ''));
    $email = sanitize_email(wp_unslash($_POST['email'] ?? ''));
    $topic = sanitize_key(wp_unslash($_POST['topic'] ?? 'general'));
    $message = sanitize_textarea_field(wp_unslash($_POST['message'] ?? ''));
    $consent = sanitize_text_field(wp_unslash($_POST['consent'] ?? '')) === '1';
    $trap = sanitize_text_field(wp_unslash($_POST['company_website'] ?? ''));
    $issued_at = absint($_POST['issued_at'] ?? 0);
    $proof = sanitize_text_field(wp_unslash($_POST['proof'] ?? ''));
    $age = time() - $issued_at;
    $expected = hash_hmac('sha256', (string) $issued_at, wp_salt('nonce'));

    if ($trap) mirrortalk_contact_generic_success();
    if (!mirrortalk_contact_rate_limit()) wp_send_json_error(array('message' => __('Too many messages were attempted. Please wait before trying again.', 'astra-child')), 429);
    if (!$issued_at || !hash_equals($expected, $proof) || $age < 3 || $age > 7 * DAY_IN_SECONDS) wp_send_json_error(array('message' => __('Please refresh the page and try again.', 'astra-child')), 403);
    if (strlen($name) < 2 || !is_email($email) || strlen($message) < 20 || strlen($message) > 5000 || !$consent) wp_send_json_error(array('message' => __('Please provide your name, a valid email address, a message of at least 20 characters and your consent.', 'astra-child')), 422);
    if (preg_match_all('~https?://|www\.~i', $message) > 3) wp_send_json_error(array('message' => __('Please remove excessive links and try again.', 'astra-child')), 422);

    $topics = array('general', 'guest', 'partnership', 'press', 'support', 'privacy');
    if (!in_array($topic, $topics, true)) $topic = 'general';
    $message_id = wp_insert_post(array(
        'post_type' => 'mt_contact_message',
        'post_status' => 'private',
        'post_title' => sprintf('%s — %s', $name, wp_date('Y-m-d H:i')),
        'post_content' => $message,
    ), true);
    if (is_wp_error($message_id)) wp_send_json_error(array('message' => __('We could not save your message just now. Please try again.', 'astra-child')), 500);
    update_post_meta($message_id, '_mt_contact_name', $name);
    update_post_meta($message_id, '_mt_contact_email', strtolower($email));
    update_post_meta($message_id, '_mt_contact_topic', $topic);
    update_post_meta($message_id, '_mt_contact_consent_at', gmdate('c'));
    update_post_meta($message_id, '_mt_contact_source', esc_url_raw(wp_get_referer() ?: home_url('/contact/')));

    $subject = sprintf(__('Mirror Talk contact: %1$s — %2$s', 'astra-child'), ucfirst($topic), $name);
    $body = sprintf("Name: %s\nEmail: %s\nTopic: %s\n\n%s\n\nSaved message: %s", $name, $email, $topic, $message, admin_url('post.php?post=' . $message_id . '&action=edit'));
    wp_mail(get_option('admin_email'), $subject, $body, array('Reply-To: ' . $name . ' <' . $email . '>'));
    mirrortalk_contact_generic_success();
}
add_action('wp_ajax_mirrortalk_contact_submit', 'mirrortalk_contact_submit');
add_action('wp_ajax_nopriv_mirrortalk_contact_submit', 'mirrortalk_contact_submit');

function mirrortalk_render_contact_form() {
    ?>
    <section class="mt-contact" aria-labelledby="mt-contact-title">
        <div class="mt-contact__intro">
            <p class="mt-section-kicker"><?php esc_html_e('A real conversation begins here', 'astra-child'); ?></p>
            <h2 id="mt-contact-title"><?php esc_html_e('Write to Mirror Talk.', 'astra-child'); ?></h2>
            <p><?php esc_html_e('Questions, thoughtful feedback, partnerships and guest enquiries are welcome. Your message is stored privately and sent directly to the Mirror Talk team.', 'astra-child'); ?></p>
            <ul>
                <li><?php esc_html_e('No advertising lists or resale of your details', 'astra-child'); ?></li>
                <li><?php esc_html_e('Protected by first-party anti-spam controls', 'astra-child'); ?></li>
                <li><?php esc_html_e('Private by default', 'astra-child'); ?></li>
            </ul>
        </div>
        <form class="mt-contact-form" data-mt-contact-form novalidate>
            <div class="mt-contact-form__row">
                <label><span><?php esc_html_e('Your name', 'astra-child'); ?></span><input type="text" name="name" autocomplete="name" minlength="2" maxlength="120" required></label>
                <label><span><?php esc_html_e('Email address', 'astra-child'); ?></span><input type="email" name="email" autocomplete="email" maxlength="254" required></label>
            </div>
            <label><span><?php esc_html_e('What would you like to discuss?', 'astra-child'); ?></span><select name="topic"><option value="general"><?php esc_html_e('General message', 'astra-child'); ?></option><option value="guest"><?php esc_html_e('Podcast guest enquiry', 'astra-child'); ?></option><option value="partnership"><?php esc_html_e('Partnership or collaboration', 'astra-child'); ?></option><option value="press"><?php esc_html_e('Press or media', 'astra-child'); ?></option><option value="support"><?php esc_html_e('Website or listening support', 'astra-child'); ?></option><option value="privacy"><?php esc_html_e('Privacy request', 'astra-child'); ?></option></select></label>
            <label><span><?php esc_html_e('Your message', 'astra-child'); ?></span><textarea name="message" rows="8" minlength="20" maxlength="5000" required></textarea><small><?php esc_html_e('Please include enough context for us to respond meaningfully.', 'astra-child'); ?></small></label>
            <label class="mt-contact-form__consent"><input type="checkbox" name="consent" value="1" required><span><?php esc_html_e('I consent to Mirror Talk using these details to respond to this enquiry.', 'astra-child'); ?></span></label>
            <label class="mt-contact-form__trap" aria-hidden="true">Website<input type="text" name="company_website" tabindex="-1" autocomplete="off"></label>
            <div class="mt-contact-form__footer"><button class="mt-button" type="submit"><?php esc_html_e('Send message', 'astra-child'); ?></button><p data-mt-contact-status role="status" aria-live="polite"></p></div>
        </form>
    </section>
    <?php
}

function mirrortalk_contact_assets() {
    $content = is_singular(array('post','page')) ? (string)get_post_field('post_content',get_queried_object_id()) : '';
    if (!is_page(array('contact', 'join-us')) && !has_shortcode($content,'mirror_talk_contact')) return;
    wp_enqueue_script('mirror-talk-contact', get_stylesheet_directory_uri() . '/contact-form.js', array(), function_exists('mirrortalk_asset_version') ? mirrortalk_asset_version('contact-form.js') : wp_get_theme()->get('Version'), true);
    wp_script_add_data('mirror-talk-contact', 'strategy', 'defer');
    $issued_at = time();
    wp_localize_script('mirror-talk-contact', 'MirrorTalkContact', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('mirrortalk_contact_submit'),
        'issuedAt' => $issued_at,
        'proof' => hash_hmac('sha256', (string) $issued_at, wp_salt('nonce')),
    ));
}
add_action('wp_enqueue_scripts', 'mirrortalk_contact_assets', 30);

add_shortcode('mirror_talk_contact', function () {
    ob_start(); mirrortalk_render_contact_form(); return (string)ob_get_clean();
});

add_shortcode('mirror_talk_newsletter', function () {
    return '<aside class="mt-story-newsletter mt-migrated-newsletter"><div><p class="mt-section-kicker">'.esc_html__('A thoughtful note, not more noise','astra-child').'</p><h2>'.esc_html__('Let the reflection continue gently.','astra-child').'</h2><p>'.esc_html__('Receive new conversations and carefully chosen prompts for living with greater clarity and intention.','astra-child').'</p></div><button class="mt-button" type="button" data-mt-open-dialog="mt-newsletter-invite">'.esc_html__('Join the newsletter','astra-child').'</button></aside>';
});

function mirrortalk_remove_third_party_contact_assets() {
    if (!is_page(array('contact', 'join-us'))) return;
    foreach (array('srfm-frontend-default', 'srfm-common', 'srfm-form', 'srfm-tom-select', 'srfm-intl-tel-input', 'contact-form-7', 'astra-contact-form-7') as $handle) wp_dequeue_style($handle);
    foreach (array('srfm-form-submit', 'srfm-frontend', 'srfm-input', 'contact-form-7', 'swv') as $handle) wp_dequeue_script($handle);
}
add_action('wp_enqueue_scripts', 'mirrortalk_remove_third_party_contact_assets', PHP_INT_MAX);
