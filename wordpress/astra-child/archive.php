<?php
/** Dark editorial archive template for tags, dates and authors. */
if (!defined('ABSPATH')) { exit; }
get_header();
?>
<main id="primary" class="site-main mt-library">
    <header class="mt-library__hero">
        <div class="mt-library__shell">
            <p class="mt-section-kicker"><?php esc_html_e('Explore the archive', 'astra-child'); ?></p>
            <?php
            if (is_tag()) {
                echo '<h1>' . esc_html(single_tag_title('', false)) . '</h1>';
            } elseif (is_category()) {
                echo '<h1>' . esc_html(single_cat_title('', false)) . '</h1>';
            } else {
                the_archive_title('<h1>', '</h1>');
            }
            ?>
            <div class="mt-library__description"><?php the_archive_description(); ?></div>
        </div>
    </header>
    <section class="mt-library__shell mt-library__content">
        <?php if (have_posts()) : ?><div class="mt-library__grid">
            <?php $mt_card_index=0;while (have_posts()) : the_post();mirrortalk_render_editorial_card(get_the_ID(),$mt_card_index++,'h2');endwhile; ?>
        </div><nav class="mt-library__pagination"><?php the_posts_pagination(array('mid_size' => 1)); ?></nav>
        <?php else : ?><div class="mt-empty"><h2><?php esc_html_e('Nothing here yet.', 'astra-child'); ?></h2></div><?php endif; ?>
    </section>
</main>
<?php get_footer(); ?>
