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
            <?php while (have_posts()) : the_post(); ?>
                <article <?php post_class('mt-library-card'); ?>>
                    <a class="mt-library-card__link" href="<?php the_permalink(); ?>">
                        <?php if (has_post_thumbnail()) : ?>
                            <?php the_post_thumbnail('large', array('class' => 'mt-library-card__image', 'loading' => 'lazy')); ?>
                        <?php else : ?>
                            <span class="mt-library-card__image mt-library-card__image--placeholder" aria-hidden="true"></span>
                        <?php endif; ?>
                        <span class="mt-library-card__content">
                            <span class="mt-library-card__meta"><?php echo esc_html(get_the_date()); ?></span>
                            <h2><?php the_title(); ?></h2>
                            <span class="mt-library-card__excerpt"><?php echo esc_html(wp_trim_words(get_the_excerpt(), 25)); ?></span>
                            <strong><?php esc_html_e('Read and reflect', 'astra-child'); ?> →</strong>
                        </span>
                    </a>
                </article>
            <?php endwhile; ?>
            </div>
            <nav class="mt-library__pagination" aria-label="<?php esc_attr_e('Blog pages', 'astra-child'); ?>"><?php the_posts_pagination(array('mid_size' => 1)); ?></nav>
        <?php else : ?>
            <div class="mt-empty"><h2><?php esc_html_e('New conversations are on the way.', 'astra-child'); ?></h2></div>
        <?php endif; ?>
    </section>
</main>
<?php get_footer(); ?>
