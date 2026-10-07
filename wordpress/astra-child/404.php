<?php
/** Mirror Talk not-found page. */
if (!defined('ABSPATH')) { exit; }
get_header();
?>
<main id="primary" class="site-main mt-not-found">
    <div class="mt-not-found__inner">
        <p class="mt-section-kicker"><?php esc_html_e('A pause in the journey', 'astra-child'); ?></p>
        <h1><?php esc_html_e('This page has moved beyond the mirror.', 'astra-child'); ?></h1>
        <p><?php esc_html_e('The conversation may have moved, changed name or returned to the archive. Begin again from somewhere meaningful.', 'astra-child'); ?></p>
        <div class="mt-home__actions"><a class="mt-button" href="<?php echo esc_url(home_url('/')); ?>"><?php esc_html_e('Return home', 'astra-child'); ?></a><a class="mt-button mt-button--quiet" href="<?php echo esc_url(home_url('/podcast-episodes/')); ?>"><?php esc_html_e('Explore conversations', 'astra-child'); ?></a></div>
    </div>
</main>
<?php get_footer(); ?>
