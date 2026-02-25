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
        <h2>Ask Mirror Talk</h2>
        <div id="ask-mirror-talk-qotd" class="amt-qotd" style="display:none;"></div>
        <div id="ask-mirror-talk-topics" class="amt-topics" style="display:none;">
            <p class="amt-topics-label">Browse by topic:</p>
            <div class="amt-topics-list"></div>
        </div>
        <div id="ask-mirror-talk-suggestions" class="amt-suggestions">
            <p class="amt-suggestions-label">Try asking about:</p>
            <div class="amt-suggestions-list"></div>
        </div>
        <form id="ask-mirror-talk-form">
            <label for="ask-mirror-talk-input">What’s on your heart?</label>
            <textarea id="ask-mirror-talk-input" rows="3" placeholder="Ask a question..." autocomplete="off" autocapitalize="sentences"></textarea>
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
        <div id="ask-mirror-talk-followups" class="amt-followups" style="display:none;">
            <p class="amt-followups-label">You might also want to ask:</p>
            <div class="amt-followups-list"></div>
        </div>
    </div>
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
    wp_enqueue_style(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.css',
        array(),
        '3.4.0'
    );
    wp_enqueue_script(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.js',
        array('jquery'),
        '3.4.0',
        true
    );

    // Analytics add-on: citation click tracking + feedback buttons
    wp_enqueue_script(
        'ask-mirror-talk-analytics',
        $theme_uri . '/analytics-addon.js',
        array('ask-mirror-talk'),
        '3.4.0',
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
