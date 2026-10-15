<?php
/** Mirror Talk-owned global document header. */
if (!defined('ABSPATH')) { exit; }
?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <?php wp_head(); ?>
</head>
<body <?php body_class('mt-site'); ?>>
<?php wp_body_open(); ?>
<a class="mt-skip-link" href="#primary"><?php esc_html_e('Skip to the conversation', 'astra-child'); ?></a>
<header class="mt-site-header" data-mt-site-header>
    <div class="mt-site-header__inner">
        <a class="mt-site-brand" href="<?php echo esc_url(home_url('/')); ?>" rel="home" aria-label="<?php esc_attr_e('Mirror Talk home', 'astra-child'); ?>">
            <?php if (has_custom_logo()) : ?>
                <span class="mt-site-brand__mark"><?php echo wp_kses_post(wp_get_attachment_image((int) get_theme_mod('custom_logo'), 'full', false, array('class' => 'custom-logo', 'loading' => 'eager', 'fetchpriority' => 'high'))); ?></span>
            <?php else : ?>
                <span class="mt-site-brand__symbol" aria-hidden="true">◉</span>
            <?php endif; ?>
            <span><strong><?php bloginfo('name'); ?></strong><small><?php esc_html_e('Soulful Conversations', 'astra-child'); ?></small></span>
        </a>
        <button class="mt-site-nav-toggle" type="button" data-mt-nav-toggle aria-expanded="false" aria-controls="mt-primary-navigation">
            <span><?php esc_html_e('Menu', 'astra-child'); ?></span><i aria-hidden="true"></i>
        </button>
        <nav id="mt-primary-navigation" class="mt-site-nav" data-mt-site-nav aria-label="<?php esc_attr_e('Primary navigation', 'astra-child'); ?>">
            <?php
            if (has_nav_menu('primary')) {
                wp_nav_menu(array('theme_location' => 'primary', 'container' => false, 'menu_class' => 'mt-site-nav__list', 'fallback_cb' => false, 'depth' => 2));
            } else {
                ?>
                <ul class="mt-site-nav__list">
                    <li><a href="<?php echo esc_url(home_url('/')); ?>"><?php esc_html_e('Home', 'astra-child'); ?></a></li>
                    <li><a href="<?php echo esc_url(home_url('/listen/')); ?>"><?php esc_html_e('Listen', 'astra-child'); ?></a></li>
                    <li><a href="<?php echo esc_url(home_url('/ask-mirror-talk/')); ?>"><?php esc_html_e('Ask Mirror Talk', 'astra-child'); ?></a><ul class="sub-menu"><li><a href="<?php echo esc_url(home_url('/insights/')); ?>"><?php esc_html_e('Insights', 'astra-child'); ?></a></li></ul></li>
                    <li><a href="<?php echo esc_url(home_url('/contact/')); ?>"><?php esc_html_e('Connect', 'astra-child'); ?></a></li>
                </ul>
                <?php
            }
            ?>
        </nav>
    </div>
</header>
<div class="mt-site-frame">
