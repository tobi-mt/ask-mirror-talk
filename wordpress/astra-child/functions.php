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

/**
 * Enqueue parent theme stylesheet
 * This loads the parent Astra theme's CSS before the child theme's CSS
 */
function astra_child_enqueue_parent_styles() {
    wp_enqueue_style('astra-parent-style', get_template_directory_uri() . '/style.css');
}
add_action('wp_enqueue_scripts', 'astra_child_enqueue_parent_styles', 10);

/**
 * Load Ask Mirror Talk widget
 * This file contains the shortcode, AJAX handlers, and PWA setup
 */
require_once get_stylesheet_directory() . '/ask-mirror-talk.php';

add_action('wp_enqueue_scripts', 'mirrortalk_child_enqueue_styles', 20);
function mirrortalk_child_enqueue_styles() {
    wp_enqueue_style(
        'astra-child-style',
        get_stylesheet_uri(),
        array('astra-theme-css'),
        wp_get_theme()->get('Version')
    );
}
