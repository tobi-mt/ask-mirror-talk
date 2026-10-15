<?php
/** Cohesive treatment for standard WordPress pages. */
if (!defined('ABSPATH')) { exit; }
get_header();
$is_ask_page = is_page('ask-mirror-talk');
$is_contact_page = is_page(array('contact', 'join-us'));
$is_trust_page = function_exists('mirrortalk_is_trust_page') && mirrortalk_is_trust_page();
?>
<main id="primary" class="site-main mt-page<?php echo $is_ask_page ? ' mt-page--ask' : ''; ?><?php echo $is_trust_page ? ' mt-page--trust' : ''; ?>">
<?php while (have_posts()) : the_post(); ?>
    <?php if ($is_trust_page) : $trust = mirrortalk_trust_page_details(get_the_ID()); ?>
        <header class="mt-trust-hero">
            <div class="mt-trust-shell">
                <p class="mt-section-kicker"><?php echo esc_html($trust['eyebrow']); ?></p>
                <h1><?php the_title(); ?></h1>
                <p class="mt-trust-hero__summary"><?php echo esc_html($trust['summary']); ?></p>
                <p class="mt-trust-hero__reviewed"><?php echo esc_html(sprintf(__('Policy updated %s', 'astra-child'), get_the_modified_date('F Y'))); ?></p>
            </div>
        </header>
        <div class="mt-trust-shell mt-trust-layout">
            <article <?php post_class('mt-trust-document entry-content mt-editorial-content'); ?>>
                <?php
                $trust_content = apply_filters('the_content', get_the_content());
                $trust_content = preg_replace('/<h1\b[^>]*>.*?<\/h1>/is', '', $trust_content, 1);
                echo $trust_content; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- normal filtered post content.
                wp_link_pages();
                ?>
            </article>
            <aside class="mt-trust-aside" aria-labelledby="mt-trust-aside-title">
                <p class="mt-section-kicker"><?php esc_html_e('A clear next step', 'astra-child'); ?></p>
                <h2 id="mt-trust-aside-title"><?php echo esc_html($trust['aside_title']); ?></h2>
                <p><?php echo esc_html($trust['aside_copy']); ?></p>
                <a class="mt-button" href="<?php echo esc_url($trust['aside_url']); ?>"><?php echo esc_html($trust['aside_label']); ?> <span aria-hidden="true">→</span></a>
            </aside>
        </div>
    <?php else : ?>
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
    <?php endif; ?>
<?php endwhile; ?>
</main>
<?php get_footer(); ?>
