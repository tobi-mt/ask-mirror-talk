<?php
/** Mirror Talk-owned global footer. */
if (!defined('ABSPATH')) { exit; }
?>
<?php if (function_exists('mirrortalk_render_youtube_studio')) mirrortalk_render_youtube_studio(); ?>
</div>
<footer class="mt-site-footer">
    <div class="mt-site-footer__inner">
        <section class="mt-site-footer__statement" aria-labelledby="mt-footer-title">
            <p class="mt-section-kicker"><?php esc_html_e('Mirror Talk: Soulful Conversations', 'astra-child'); ?></p>
            <h2 id="mt-footer-title"><?php esc_html_e('Carry one honest question with you.', 'astra-child'); ?></h2>
            <p><?php esc_html_e('Conversations for greater clarity, courage, purpose and human connection.', 'astra-child'); ?></p>
            <a class="mt-button" href="<?php echo esc_url(home_url('/ask-mirror-talk/')); ?>"><?php esc_html_e('Ask Mirror Talk', 'astra-child'); ?></a>
        </section>
        <div class="mt-site-footer__links">
            <nav aria-label="<?php esc_attr_e('Explore Mirror Talk', 'astra-child'); ?>">
                <strong><?php esc_html_e('Explore', 'astra-child'); ?></strong>
                <a href="<?php echo esc_url(home_url('/listen/')); ?>"><?php esc_html_e('Listen', 'astra-child'); ?></a>
                <a href="<?php echo esc_url(home_url('/podcast-episodes/')); ?>"><?php esc_html_e('Browse episodes', 'astra-child'); ?></a>
                <a href="<?php echo esc_url(home_url('/insights/')); ?>"><?php esc_html_e('Insights', 'astra-child'); ?></a>
                <a href="<?php echo esc_url(home_url('/contact/')); ?>"><?php esc_html_e('Connect', 'astra-child'); ?></a>
            </nav>
            <nav aria-label="<?php esc_attr_e('Follow Mirror Talk', 'astra-child'); ?>">
                <strong><?php esc_html_e('Follow', 'astra-child'); ?></strong>
                <?php foreach (array_slice(function_exists('mirrortalk_listen_platforms') ? mirrortalk_listen_platforms(true) : array(), 0, 3) as $platform) : ?><a href="<?php echo esc_url($platform['url']); ?>" target="_blank" rel="noopener" data-mt-platform-link="<?php echo esc_attr($platform['id']); ?>"><?php echo esc_html($platform['name']); ?></a><?php endforeach; ?>
            </nav>
        </div>
    </div>
    <div class="mt-site-footer__legal">
        <span>© <?php echo esc_html(wp_date('Y')); ?> <?php bloginfo('name'); ?></span>
        <span><?php esc_html_e('A reflective space—not medical, therapeutic or emergency care.', 'astra-child'); ?></span>
        <?php if (get_privacy_policy_url()) : ?><a href="<?php echo esc_url(get_privacy_policy_url()); ?>"><?php esc_html_e('Privacy', 'astra-child'); ?></a><?php endif; ?>
        <a href="<?php echo esc_url(home_url('/editorial-standards/')); ?>"><?php esc_html_e('Editorial standards', 'astra-child'); ?></a>
        <a href="<?php echo esc_url(home_url('/corrections/')); ?>"><?php esc_html_e('Corrections', 'astra-child'); ?></a>
    </div>
</footer>
<?php wp_footer(); ?>
</body>
</html>
