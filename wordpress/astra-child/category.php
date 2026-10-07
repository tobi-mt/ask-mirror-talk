<?php
/**
 * Search-friendly topic hub built from native WordPress categories.
 */

if (!defined('ABSPATH')) {
    exit;
}

get_header();

$category = get_queried_object();
$topic = mirrortalk_resolve_topic_context();
$category_text = strtolower(($category->slug ?? '') . ' ' . ($category->name ?? ''));

foreach (mirrortalk_topic_map() as $slug => $candidate) {
    foreach ($candidate['keywords'] as $keyword) {
        if (strpos($category_text, strtolower($keyword)) !== false) {
            $topic = array_merge(array('slug' => $slug), $candidate);
            break 2;
        }
    }
}

$description = category_description();
if (!$description) {
    $description = '<p>' . esc_html($topic['description']) . '</p>';
}

$ask_url = mirrortalk_build_ask_url(
    0,
    array(
        'slug' => $topic['slug'],
        'prompt' => $topic['prompt'],
    )
);
?>
<main id="primary" class="site-main mt-topic-hub">
    <header class="mt-topic-hub__hero">
        <div class="mt-topic-hub__shell">
            <p class="mt-section-kicker"><?php esc_html_e('Explore the Mirror Talk library', 'astra-child'); ?></p>
            <h1><?php single_cat_title(); ?></h1>
            <div class="mt-topic-hub__description"><?php echo wp_kses_post($description); ?></div>
            <div class="mt-home__actions">
                <a class="mt-button" href="<?php echo esc_url($ask_url); ?>"><?php esc_html_e('Reflect on this topic', 'astra-child'); ?></a>
                <a class="mt-button mt-button--quiet" href="<?php echo esc_url(home_url('/podcast-episodes/')); ?>"><?php esc_html_e('Browse all conversations', 'astra-child'); ?></a>
            </div>
        </div>
    </header>

    <section class="mt-topic-hub__shell mt-topic-hub__content" aria-labelledby="mt-topic-conversations">
        <p class="mt-section-kicker"><?php esc_html_e('Listen and read', 'astra-child'); ?></p>
        <h2 id="mt-topic-conversations" class="mt-section-heading"><?php esc_html_e('Conversations to help you go deeper.', 'astra-child'); ?></h2>

        <?php if (have_posts()) : ?>
            <div class="mt-topic-hub__grid">
                <?php while (have_posts()) : the_post(); ?>
                    <article <?php post_class('mt-card mt-topic-card'); ?>>
                        <a class="mt-episode-card" href="<?php the_permalink(); ?>">
                            <?php if (has_post_thumbnail()) : ?>
                                <?php the_post_thumbnail('large', array('class' => 'mt-episode-card__image', 'loading' => 'lazy')); ?>
                            <?php else : ?>
                                <span class="mt-episode-card__image" aria-hidden="true"></span>
                            <?php endif; ?>
                            <p class="mt-topic-card__date"><?php echo esc_html(get_the_date()); ?></p>
                            <h3><?php the_title(); ?></h3>
                            <p><?php echo esc_html(wp_trim_words(get_the_excerpt(), 28)); ?></p>
                            <span class="mt-episode-card__meta"><?php esc_html_e('Open conversation', 'astra-child'); ?></span>
                        </a>
                    </article>
                <?php endwhile; ?>
            </div>
            <nav class="mt-topic-hub__pagination" aria-label="<?php esc_attr_e('Topic pages', 'astra-child'); ?>">
                <?php the_posts_pagination(array('mid_size' => 1)); ?>
            </nav>
        <?php else : ?>
            <div class="mt-card">
                <h2><?php esc_html_e('More conversations are coming.', 'astra-child'); ?></h2>
                <p><?php esc_html_e('Try another topic or bring your question directly to Ask Mirror Talk.', 'astra-child'); ?></p>
            </div>
        <?php endif; ?>
    </section>

    <section class="mt-topic-hub__shell mt-topic-hub__reflection">
        <div class="mt-home__closing">
            <div>
                <p class="mt-section-kicker"><?php esc_html_e('Pause and reflect', 'astra-child'); ?></p>
                <h2><?php echo esc_html($topic['prompt']); ?></h2>
            </div>
            <a class="mt-button" href="<?php echo esc_url($ask_url); ?>"><?php esc_html_e('Take this question to Ask', 'astra-child'); ?></a>
        </div>
    </section>
</main>
<?php
get_footer();
