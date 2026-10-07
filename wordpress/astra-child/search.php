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
            <?php while (have_posts()) : the_post(); ?><article <?php post_class('mt-library-card'); ?>><a class="mt-library-card__link" href="<?php the_permalink(); ?>">
                <?php if (has_post_thumbnail()) : the_post_thumbnail('medium_large', array('class' => 'mt-library-card__image', 'loading' => 'lazy', 'decoding' => 'async')); else : ?><span class="mt-library-card__image mt-library-card__image--placeholder" aria-hidden="true"></span><?php endif; ?>
                <span class="mt-library-card__content"><span class="mt-library-card__meta"><?php echo esc_html(get_the_date()); ?></span><h2><?php the_title(); ?></h2><span class="mt-library-card__excerpt"><?php echo esc_html(wp_trim_words(get_the_excerpt(), 25)); ?></span><strong><?php esc_html_e('Open conversation', 'astra-child'); ?> →</strong></span>
            </a></article><?php endwhile; ?>
        </div><nav class="mt-library__pagination"><?php the_posts_pagination(array('mid_size' => 1)); ?></nav>
        <?php else : ?><div class="mt-empty"><h2><?php esc_html_e('No conversation matched those words.', 'astra-child'); ?></h2><p><?php esc_html_e('Try a broader phrase or explore the latest conversations.', 'astra-child'); ?></p><?php get_search_form(); ?></div><?php endif; ?>
    </section>
</main>
<?php get_footer(); ?>
