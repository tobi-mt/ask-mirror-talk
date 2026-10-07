<?php
/** Standalone same-origin player window that survives navigation in the main tab. */
if (!defined('ABSPATH')) { exit; }
$episodes = mirrortalk_get_feed_episodes();
$latest = $episodes[0] ?? array('title' => __('Mirror Talk: Soulful Conversations', 'astra-child'), 'audio' => '');
$version = wp_get_theme()->get('Version');
?><!doctype html>
<html <?php language_attributes(); ?>><head><meta charset="<?php bloginfo('charset'); ?>"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title><?php esc_html_e('Mirror Talk Player', 'astra-child'); ?></title><link rel="stylesheet" href="<?php echo esc_url(get_stylesheet_directory_uri() . '/mirror-talk-site.css?ver=' . rawurlencode($version)); ?>"></head>
<body class="mt-player-window">
<main class="mt-player-window__shell" data-mt-player-window data-return-url="<?php echo esc_url(home_url('/')); ?>">
    <header><p class="mt-section-kicker"><?php esc_html_e('Mirror Talk: Soulful Conversations', 'astra-child'); ?></p><h1><?php esc_html_e('Keep listening.', 'astra-child'); ?></h1><p><?php esc_html_e('This compact player remains open while you explore the website in the main window.', 'astra-child'); ?></p></header>
    <div class="mt-listen__now"><span class="mt-listen__art" aria-hidden="true"></span><div><small><?php esc_html_e('Now selected', 'astra-child'); ?></small><strong data-mt-window-title><?php echo esc_html($latest['title']); ?></strong></div></div>
    <audio data-mt-window-audio controls preload="metadata" src="<?php echo esc_url($latest['audio']); ?>"></audio>
    <section class="mt-player-window__queue" aria-label="<?php esc_attr_e('Recent episodes', 'astra-child'); ?>">
        <?php foreach ($episodes as $index => $episode) : ?><button type="button" data-mt-window-episode data-audio="<?php echo esc_url($episode['audio']); ?>" data-title="<?php echo esc_attr($episode['title']); ?>"><span><?php echo esc_html(str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT)); ?></span><strong><?php echo esc_html($episode['title']); ?></strong><span aria-hidden="true">▶</span></button><?php endforeach; ?>
    </section>
    <a class="mt-player-window__return" href="<?php echo esc_url(home_url('/')); ?>" data-mt-return-site><?php esc_html_e('Return to the website', 'astra-child'); ?> ↗</a>
</main>
<script src="<?php echo esc_url(get_stylesheet_directory_uri() . '/listen-window.js?ver=' . rawurlencode($version)); ?>" defer></script>
</body></html>
