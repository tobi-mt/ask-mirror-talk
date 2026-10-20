<?php
/** Virtual topic collection: groups existing posts without requiring manual category migration. */
if (!defined('ABSPATH')) { exit; }
get_header();

$topic_slug = sanitize_key((string) get_query_var('mirror_topic'));
$topic_map = mirrortalk_topic_map();
$topic = $topic_map[$topic_slug] ?? $topic_map['purpose'];
$candidate_query = new WP_Query(array(
    'post_type' => 'post',
    'post_status' => 'publish',
    'posts_per_page' => 120,
    'ignore_sticky_posts' => true,
    'no_found_rows' => true,
));
$matches = array_values(array_filter($candidate_query->posts, function ($post) use ($topic_slug) {
    $resolved = mirrortalk_resolve_topic_context($post->ID);
    return $resolved['slug'] === $topic_slug;
}));
$page = max(1, (int) get_query_var('paged', 1));
$per_page = 12;
$page_posts = array_slice($matches, ($page - 1) * $per_page, $per_page);
$page_count = max(1, (int) ceil(count($matches) / $per_page));
$ask_url = mirrortalk_build_ask_url(0, array('slug' => $topic_slug, 'prompt' => $topic['prompt']));
?>
<main id="primary" class="site-main mt-topic-hub">
    <header class="mt-topic-hub__hero"><div class="mt-topic-hub__shell">
        <p class="mt-section-kicker"><?php esc_html_e('Explore by what you need', 'astra-child'); ?></p>
        <h1><?php echo esc_html($topic['label']); ?></h1>
        <p class="mt-topic-hub__description"><?php echo esc_html($topic['description']); ?></p>
        <div class="mt-home__actions"><a class="mt-button" href="<?php echo esc_url($ask_url); ?>"><?php esc_html_e('Reflect on this topic', 'astra-child'); ?></a><a class="mt-button mt-button--quiet" href="<?php echo esc_url(home_url('/blog/')); ?>"><?php esc_html_e('View all conversations', 'astra-child'); ?></a></div>
    </div></header>
    <section class="mt-topic-hub__shell mt-topic-hub__content">
        <p class="mt-section-kicker"><?php echo esc_html(sprintf(_n('%s related conversation', '%s related conversations', count($matches), 'astra-child'), number_format_i18n(count($matches)))); ?></p>
        <h2 class="mt-section-heading"><?php esc_html_e('Conversations selected for this part of your journey.', 'astra-child'); ?></h2>
        <?php if ($page_posts) : ?><div class="mt-library__grid">
            <?php foreach ($page_posts as $mt_card_index=>$post) : setup_postdata($post);mirrortalk_render_editorial_card(get_the_ID(),$mt_card_index,'h3');endforeach;wp_reset_postdata(); ?>
        </div><?php if ($page_count > 1) : ?><nav class="mt-library__pagination"><?php echo wp_kses_post(paginate_links(array('total' => $page_count, 'current' => $page))); ?></nav><?php endif; ?>
        <?php else : ?><div class="mt-empty"><h2><?php esc_html_e('We are still organising this collection.', 'astra-child'); ?></h2><p><?php esc_html_e('Explore all conversations or bring this theme directly to Ask Mirror Talk.', 'astra-child'); ?></p></div><?php endif; ?>
    </section>
</main>
<?php get_footer(); ?>
