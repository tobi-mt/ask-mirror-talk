<?php
/**
 * Ask Mirror Talk shortcode + AJAX handler for Astra theme.
 * Updated version - Uses direct wp_remote_post() instead of WPGetAPI
 *
 * Usage: [ask_mirror_talk]
 */

if (!defined('ABSPATH')) {
    exit;
}

function ask_mirror_talk_shortcode() {
    ob_start();
    ?>
    <div class="ask-mirror-talk">
        <h2>Ask Mirror Talk</h2>
        <form id="ask-mirror-talk-form">
            <label for="ask-mirror-talk-input">What's on your heart?</label>
            <textarea id="ask-mirror-talk-input" rows="4" placeholder="Ask a question..."></textarea>
            <button type="submit" id="ask-mirror-talk-submit">Ask</button>
        </form>
        <div class="ask-mirror-talk-response">
            <h3>Response</h3>
            <div id="ask-mirror-talk-output"></div>
        </div>
        <div class="ask-mirror-talk-citations">
            <h3>Referenced Episodes</h3>
            <ul id="ask-mirror-talk-citations"></ul>
        </div>
    </div>
    <?php
    return ob_get_clean();
}
add_shortcode('ask_mirror_talk', 'ask_mirror_talk_shortcode');

function ask_mirror_talk_enqueue_assets() {
    if (!is_singular()) {
        return;
    }

    global $post;
    if (!$post || !has_shortcode($post->post_content, 'ask_mirror_talk')) {
        return;
    }

    $theme_uri = get_stylesheet_directory_uri();
    wp_enqueue_style(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.css',
        array(),
        '2.0.0'  // Updated for UX improvements, deduplication, better AI responses
    );
    wp_enqueue_script(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.js',
        array(),
        '2.0.0',  // Updated for UX improvements, deduplication, better AI responses
        true
    );

    wp_localize_script('ask-mirror-talk', 'AskMirrorTalk', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('ask_mirror_talk_nonce')
    ));
}
add_action('wp_enqueue_scripts', 'ask_mirror_talk_enqueue_assets');

function ask_mirror_talk_ajax_handler() {
    check_ajax_referer('ask_mirror_talk_nonce', 'nonce');

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
