<?php
/** Mirror Talk search results. */
if (!defined('ABSPATH')) { exit; }
get_header();
?>
<main id="primary" class="site-main mt-library">
    <header class="mt-library__hero"><div class="mt-library__shell">
        <p class="mt-section-kicker"><?php esc_html_e('Search the conversations', 'astra-child'); ?></p>
        <h1><?php echo esc_html(sprintf(__('Results for “%s”', 'astra-child'), get_search_query())); ?></h1>
    </div></header>
    <section class="mt-library__shell mt-library__content">
        <?php if (have_posts()) : ?><div class="mt-library__grid">
            <?php $mt_card_index=0;while (have_posts()) : the_post();mirrortalk_render_editorial_card(get_the_ID(),$mt_card_index++,'h2');endwhile; ?>
        </div><nav class="mt-library__pagination"><?php the_posts_pagination(array('mid_size' => 1)); ?></nav>
        <?php else : ?><div class="mt-empty"><h2><?php esc_html_e('No conversation matched those words.', 'astra-child'); ?></h2><p><?php esc_html_e('Try a broader phrase or explore the latest conversations.', 'astra-child'); ?></p><?php get_search_form(); ?></div><?php endif; ?>
    </section>
</main>
<?php get_footer(); ?>
