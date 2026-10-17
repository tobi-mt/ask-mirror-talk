<?php
/** Dark editorial single-post template. */
if (!defined('ABSPATH')) { exit; }
get_header();
?>
<main id="primary" class="site-main mt-reading">
<?php while (have_posts()) : the_post(); ?>
    <?php
    $primary_category = get_the_category();
    $topic_context = function_exists('mirrortalk_resolve_topic_context') ? mirrortalk_resolve_topic_context(get_the_ID()) : null;
    $section_label = $primary_category ? $primary_category[0]->name : __('Mirror Talk conversation', 'astra-child');
    if (in_array(strtolower($section_label), array('general', 'uncategorized'), true) && !empty($topic_context['label'])) $section_label = $topic_context['label'];
    $reading_minutes = max(1, (int) ceil(str_word_count(wp_strip_all_tags(get_the_content())) / 220));
    $reading_label = sprintf(
        _n('%s minute read', '%s minute read', $reading_minutes, 'astra-child'),
        number_format_i18n($reading_minutes)
    );
    ?>
    <article <?php post_class('mt-reading__article'); ?>>
        <header class="mt-reading__hero">
            <div class="mt-reading__shell">
                <a class="mt-reading__back" href="<?php echo esc_url(home_url('/blog/')); ?>">← <?php esc_html_e('All conversations', 'astra-child'); ?></a>
                <p class="mt-section-kicker"><?php echo esc_html($section_label); ?></p>
                <h1><?php the_title(); ?></h1>
                <div class="mt-reading__meta">
                    <span><?php echo esc_html(get_the_date()); ?></span>
                    <span><?php echo esc_html($reading_label); ?></span>
                </div>
            </div>
            <?php if (has_post_thumbnail()) : ?>
                <figure class="mt-reading__image"><?php the_post_thumbnail('full', array('fetchpriority' => 'high')); ?></figure>
            <?php endif; ?>
        </header>
        <div class="mt-reading__body mt-reading__shell entry-content mt-editorial-content">
            <?php the_content(); ?>
            <?php wp_link_pages(); ?>
        </div>
        <?php if (!function_exists('mirrortalk_story_studio_replaces_listen_invitation') || !mirrortalk_story_studio_replaces_listen_invitation(get_the_ID())) : ?>
            <div class="mt-reading__shell"><?php if (function_exists('mirrortalk_render_listen_invitation')) mirrortalk_render_listen_invitation('episode'); ?></div>
        <?php endif; ?>
        <?php if (function_exists('mirrortalk_render_citation_brief')) mirrortalk_render_citation_brief(get_the_ID()); ?>
        <footer class="mt-reading__footer mt-reading__shell">
            <div class="mt-reading__tags"><?php the_tags('', ' ', ''); ?></div>
            <nav class="mt-reading__next" aria-label="<?php esc_attr_e('More conversations', 'astra-child'); ?>">
                <div><?php previous_post_link('%link', '<small>' . esc_html__('Previous', 'astra-child') . '</small>%title'); ?></div>
                <div><?php next_post_link('%link', '<small>' . esc_html__('Next', 'astra-child') . '</small>%title'); ?></div>
            </nav>
        </footer>
    </article>
<?php endwhile; ?>
</main>
<?php get_footer(); ?>
