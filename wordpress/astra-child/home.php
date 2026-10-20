<?php
/** Dark editorial posts index. */
if (!defined('ABSPATH')) { exit; }
get_header();
$posts_page_id = (int) get_option('page_for_posts');
$blog_title = $posts_page_id ? get_the_title($posts_page_id) : __('Conversations', 'astra-child');
?>
<main id="primary" class="site-main mt-library">
    <header class="mt-library__hero">
        <div class="mt-library__shell">
            <p class="mt-section-kicker"><?php esc_html_e('Listen · Read · Reflect', 'astra-child'); ?></p>
            <h1><?php echo esc_html($blog_title); ?></h1>
            <p><?php esc_html_e('Ideas, stories and podcast conversations for navigating purpose, relationships, healing, faith and meaningful growth.', 'astra-child'); ?></p>
        </div>
    </header>
    <section class="mt-library__shell mt-library__content" aria-label="<?php esc_attr_e('Latest conversations', 'astra-child'); ?>">
        <?php if (have_posts()) : ?>
            <div class="mt-library__grid">
            <?php $mt_card_index=0;while (have_posts()) : the_post();mirrortalk_render_editorial_card(get_the_ID(),$mt_card_index++,'h2');endwhile; ?>
            </div>
            <nav class="mt-library__pagination" aria-label="<?php esc_attr_e('Blog pages', 'astra-child'); ?>"><?php the_posts_pagination(array('mid_size' => 1)); ?></nav>
        <?php else : ?>
            <div class="mt-empty"><h2><?php esc_html_e('New conversations are on the way.', 'astra-child'); ?></h2></div>
        <?php endif; ?>
    </section>
</main>
<?php get_footer(); ?>
