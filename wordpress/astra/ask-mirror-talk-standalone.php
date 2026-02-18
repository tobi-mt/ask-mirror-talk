<?php
/**
 * Ask Mirror Talk - Standalone Version
 * Version: 2.1.0
 * 
 * This version calls the Railway API directly from JavaScript
 * No WordPress AJAX needed - simpler and faster!
 * 
 * Features:
 * - Beautiful loading animation
 * - Enhanced citation cards with excerpts
 * - Hover effects and smooth transitions
 * - Direct API calls to Railway
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
        '2.1.0'  // Beautiful loading animation and enhanced citations
    );
    
    wp_enqueue_script(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.js',
        array(),
        '2.1.0',  // Beautiful loading animation and enhanced citations
        true
    );
    
    // Pass API URL to JavaScript
    wp_localize_script('ask-mirror-talk', 'AskMirrorTalkConfig', array(
        'apiUrl' => 'https://ask-mirror-talk-production.up.railway.app/ask',
        'version' => '2.1.0'
    ));
}
add_action('wp_enqueue_scripts', 'ask_mirror_talk_enqueue_assets');
