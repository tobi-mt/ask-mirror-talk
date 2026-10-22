<?php
/** Owned, server-rendered link-in-bio destination. */
if (!defined('ABSPATH')) { exit; }
get_header();
$episodes = function_exists('mirrortalk_get_feed_episodes') ? mirrortalk_get_feed_episodes(4) : array();
$latest = $episodes ? $episodes[0] : array();
$platforms = function_exists('mirrortalk_listen_platforms') ? mirrortalk_listen_platforms(true) : array();
?>
<main id="primary" class="site-main mt-link-hub" data-mt-link-hub>
    <section class="mt-link-hub__hero" aria-labelledby="mt-link-hub-title">
        <div class="mt-link-hub__glow" aria-hidden="true"></div>
        <div class="mt-link-hub__identity">
            <img src="<?php echo esc_url(get_stylesheet_directory_uri() . '/assets/art/mirror-talk-cover-art.jpg'); ?>" width="1000" height="1000" alt="<?php esc_attr_e('Mirror Talk: Soulful Conversations podcast cover with host Tobi Ojekunle', 'astra-child'); ?>" fetchpriority="high" decoding="async">
            <div><p class="mt-section-kicker"><?php esc_html_e('Mirror Talk: Soulful Conversations', 'astra-child'); ?></p><h1 id="mt-link-hub-title"><?php esc_html_e('A conversation can change what you see.', 'astra-child'); ?></h1><p><?php esc_html_e('Listen, reflect and find the next conversation for where you are now.', 'astra-child'); ?></p></div>
        </div>
        <button class="mt-link-hub__share" type="button" data-mt-link-hub-share aria-label="<?php esc_attr_e('Share this official Mirror Talk page', 'astra-child'); ?>"><span aria-hidden="true">↗</span> <strong><?php esc_html_e('Share', 'astra-child'); ?></strong></button>
        <p class="mt-link-hub__share-status" data-mt-link-hub-share-status role="status" aria-live="polite"></p>

        <?php if ($latest) : ?>
        <article class="mt-link-hub__now" aria-labelledby="mt-link-hub-now-title">
            <div class="mt-link-hub__now-copy"><span class="mt-link-hub__signal" aria-hidden="true"><i></i><i></i><i></i></span><div><small><?php esc_html_e('Latest conversation', 'astra-child'); ?></small><h2 id="mt-link-hub-now-title" data-mt-link-hub-title><?php echo esc_html($latest['title']); ?></h2><p><?php $duration = mirrortalk_link_hub_duration_label($latest['duration'] ?? ''); echo esc_html(trim(($latest['date'] ?? '') . ($duration ? ' · ' . $duration : ''))); ?></p></div></div>
            <audio controls preload="metadata" src="<?php echo esc_url($latest['audio']); ?>" data-mt-link-hub-audio data-episode-title="<?php echo esc_attr($latest['title']); ?>"></audio>
            <?php if (count($episodes) > 1) : ?><details class="mt-link-hub__queue"><summary><?php esc_html_e('Choose a recent episode', 'astra-child'); ?> <span aria-hidden="true">⌄</span></summary><div><?php foreach ($episodes as $index=>$episode) : ?><button type="button" data-mt-link-hub-episode data-audio="<?php echo esc_url($episode['audio']); ?>" data-title="<?php echo esc_attr($episode['title']); ?>"<?php echo $index === 0 ? ' class="is-current"' : ''; ?>><span><?php echo esc_html(str_pad((string)($index+1),2,'0',STR_PAD_LEFT)); ?></span><strong><?php echo esc_html($episode['title']); ?></strong><i aria-hidden="true">▶</i></button><?php endforeach; ?></div></details><?php endif; ?>
        </article>
        <?php endif; ?>

        <?php mirrortalk_render_link_hub_youtube(); ?>

        <nav class="mt-link-hub__primary" aria-label="<?php esc_attr_e('Explore Mirror Talk', 'astra-child'); ?>">
            <a class="is-featured" href="<?php echo esc_url(home_url('/ask-mirror-talk/')); ?>" data-mt-link-hub-action="ask"><span><small><?php esc_html_e('The Living Mirror', 'astra-child'); ?></small><strong><?php esc_html_e('Ask Mirror Talk', 'astra-child'); ?></strong><em><?php esc_html_e('Bring a real question and reflect with the archive.', 'astra-child'); ?></em></span><b aria-hidden="true">→</b></a>
            <a href="<?php echo esc_url(home_url('/podcast-episodes/')); ?>" data-mt-link-hub-action="episodes"><span><small><?php esc_html_e('Discover', 'astra-child'); ?></small><strong><?php esc_html_e('Explore every conversation', 'astra-child'); ?></strong><em><?php esc_html_e('Search the archive by person, question or theme.', 'astra-child'); ?></em></span><b aria-hidden="true">→</b></a>
            <a href="<?php echo esc_url(home_url('/confessions-book/')); ?>" data-mt-link-hub-action="confessions"><span><small><?php esc_html_e('Read and reflect', 'astra-child'); ?></small><strong><?php esc_html_e('Discover Confessions', 'astra-child'); ?></strong><em><?php esc_html_e('Take a break. Reflect on life. Love.', 'astra-child'); ?></em></span><b aria-hidden="true">→</b></a>
            <button type="button" data-mt-open-dialog="mt-newsletter-invite" data-mt-link-hub-action="newsletter"><span><small><?php esc_html_e('A thoughtful note', 'astra-child'); ?></small><strong><?php esc_html_e('Join the newsletter', 'astra-child'); ?></strong><em><?php esc_html_e('New conversations and reflections—without the noise.', 'astra-child'); ?></em></span><b aria-hidden="true">＋</b></button>
        </nav>
    </section>

    <section class="mt-link-hub__listen" aria-labelledby="mt-link-hub-listen-title">
        <div class="mt-link-hub__section-heading"><p class="mt-section-kicker"><?php esc_html_e('Listen your way', 'astra-child'); ?></p><h2 id="mt-link-hub-listen-title"><?php esc_html_e('Open Mirror Talk in your favourite app.', 'astra-child'); ?></h2><p><?php esc_html_e('Official destinations, ordered intelligently for your device and remembered only on this browser.', 'astra-child'); ?></p></div>
        <div class="mt-link-hub__platforms" data-mt-platform-directory>
        <?php foreach ($platforms as $platform) : if (($platform['id'] ?? '') === 'rss') continue; $id = sanitize_title($platform['id'] ?? $platform['name']); ?>
            <a href="<?php echo esc_url(mirrortalk_link_hub_action_url($platform['url'], $id)); ?>" target="_blank" rel="noopener" data-mt-platform-link="<?php echo esc_attr($id); ?>" data-mt-platform-card data-platform="<?php echo esc_attr($id); ?>" data-devices="<?php echo esc_attr(implode(' ', (array)($platform['devices'] ?? array()))); ?>"><span aria-hidden="true"><?php echo esc_html(mirrortalk_listen_platform_badge($platform)); ?></span><strong><?php echo esc_html($platform['name']); ?></strong><i aria-hidden="true">↗</i></a>
        <?php endforeach; ?>
        </div>
        <a class="mt-link-hub__all" href="<?php echo esc_url(home_url('/listen/')); ?>" data-mt-link-hub-action="listen-directory"><?php esc_html_e('See every verified listening option', 'astra-child'); ?> <span aria-hidden="true">→</span></a>
    </section>

    <section class="mt-link-hub__connect" aria-labelledby="mt-link-hub-connect-title">
        <div class="mt-link-hub__section-heading"><p class="mt-section-kicker"><?php esc_html_e('Stay close', 'astra-child'); ?></p><h2 id="mt-link-hub-connect-title"><?php esc_html_e('Continue the conversation.', 'astra-child'); ?></h2></div>
        <div class="mt-link-hub__connections">
        <?php foreach (mirrortalk_link_hub_connections() as $link) : ?>
            <a href="<?php echo esc_url(mirrortalk_link_hub_action_url($link['url'], $link['id'])); ?>" target="_blank" rel="noopener" data-mt-link-hub-action="<?php echo esc_attr($link['id']); ?>"><span aria-hidden="true"><?php echo esc_html($link['mark']); ?></span><div><strong><?php echo esc_html($link['label']); ?></strong><small><?php echo esc_html($link['detail']); ?></small></div><i aria-hidden="true">↗</i></a>
        <?php endforeach; ?>
            <a href="<?php echo esc_url(home_url('/contact/')); ?>" data-mt-link-hub-action="contact"><span aria-hidden="true">✦</span><div><strong><?php esc_html_e('Write to Mirror Talk', 'astra-child'); ?></strong><small><?php esc_html_e('Questions, collaboration and guest enquiries', 'astra-child'); ?></small></div><i aria-hidden="true">→</i></a>
        </div>
    </section>

    <p class="mt-link-hub__trust"><?php esc_html_e('Official Mirror Talk links. No link-shortener, hidden redirect or third-party profile layer.', 'astra-child'); ?></p>
</main>
<?php get_footer(); ?>

