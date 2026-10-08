<?php
/** Cohesive treatment for standard WordPress pages. */
if (!defined('ABSPATH')) { exit; }
get_header();
$is_ask_page = is_page('ask-mirror-talk');
$is_contact_page = is_page(array('contact', 'join-us'));
?>
<main id="primary" class="site-main mt-page<?php echo $is_ask_page ? ' mt-page--ask' : ''; ?>">
<?php while (have_posts()) : the_post(); ?>
    <?php $content_has_h1 = (bool) preg_match('/<h1\b/i', (string) get_post_field('post_content', get_the_ID())); ?>
    <?php if (!$is_ask_page && ($is_contact_page || !$content_has_h1)) : ?>
        <header class="mt-page__hero"><div class="mt-page__shell"><p class="mt-section-kicker"><?php esc_html_e('Mirror Talk', 'astra-child'); ?></p><h1><?php the_title(); ?></h1><?php if (has_excerpt()) : ?><p><?php echo esc_html(get_the_excerpt()); ?></p><?php endif; ?></div></header>
    <?php endif; ?>
    <article <?php post_class('mt-page__body mt-page__shell entry-content mt-editorial-content'); ?>>
        <?php if ($is_ask_page && shortcode_exists('ask_mirror_talk')) : ?>
            <?php echo do_shortcode('[ask_mirror_talk]'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- trusted shortcode renderer. ?>
        <?php elseif ($is_contact_page && function_exists('mirrortalk_render_contact_form')) : ?>
            <?php mirrortalk_render_contact_form(); ?>
        <?php else : ?>
            <?php the_content(); ?>
        <?php endif; ?>
        <?php wp_link_pages(); ?>
    </article>
<?php endwhile; ?>
</main>
<?php get_footer(); ?>
