<?php
/**
 * Template Name: Mirror Talk Editorial Home
 * Template Post Type: page
 *
 * An opt-in, native WordPress homepage. Editors can select this template on a
 * page and set that page as the static homepage after reviewing it in staging.
 */

if (!defined('ABSPATH')) {
    exit;
}

get_header();

$ask_url = home_url('/ask-mirror-talk/');
$episodes_url = home_url('/podcast-episodes/');
$listen_url = home_url('/listen/');
$contact_url = home_url('/contact/');
?>
<main id="primary" class="site-main mt-home">
    <section class="mt-home__shell mt-home__hero" aria-labelledby="mt-home-title">
        <div>
            <p class="mt-home__eyebrow"><?php esc_html_e('Mirror Talk: Soulful Conversations', 'astra-child'); ?></p>
            <p class="mt-home__welcome" data-mt-welcome><?php esc_html_e('Welcome. Take a breath and begin where you are.', 'astra-child'); ?></p>
            <h1 id="mt-home-title"><?php esc_html_e('See your life more clearly.', 'astra-child'); ?></h1>
            <p class="mt-home__lead"><?php esc_html_e('Honest conversations and grounded reflections for people navigating purpose, faith, resilience, relationships and personal growth.', 'astra-child'); ?></p>
            <div class="mt-home__actions">
                <a class="mt-button" href="<?php echo esc_url($ask_url); ?>"><?php esc_html_e('Ask Mirror Talk', 'astra-child'); ?></a>
                <a class="mt-button mt-button--quiet" href="<?php echo esc_url($listen_url); ?>"><?php esc_html_e('Start listening', 'astra-child'); ?></a>
            </div>
        </div>
        <div class="mt-home__mirror" aria-label="A quiet space for reflection">
            <div class="mt-home__mirror-copy">
                <strong><?php esc_html_e('The right conversation can change what you see.', 'astra-child'); ?></strong>
                <span><?php esc_html_e('Listen. Reflect. Move forward with greater clarity.', 'astra-child'); ?></span>
            </div>
        </div>
    </section>

    <nav class="mt-home__shell mt-journey-rail" aria-label="<?php esc_attr_e('The Mirror Talk journey', 'astra-child'); ?>">
        <?php
        $journey_steps = array(
            __('Listen', 'astra-child'),
            __('Read', 'astra-child'),
            __('Explore', 'astra-child'),
            __('Reflect', 'astra-child'),
            __('Ask', 'astra-child'),
            __('Connect', 'astra-child'),
            __('Return', 'astra-child'),
        );
        ?>
        <?php foreach ($journey_steps as $index => $journey_step) : ?>
            <span class="mt-journey-rail__step">
                <small><?php echo esc_html(str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT)); ?></small>
                <strong><?php echo esc_html($journey_step); ?></strong>
            </span>
        <?php endforeach; ?>
    </nav>

    <?php
    $featured_conversations = new WP_Query(
        array(
            'post_type' => 'post',
            'post_status' => 'publish',
            'posts_per_page' => 5,
            'ignore_sticky_posts' => false,
        )
    );
    ?>
    <?php if ($featured_conversations->have_posts()) : ?>
        <section class="mt-home__shell mt-home__feature" aria-labelledby="mt-feature-title" data-mt-slider>
            <div class="mt-feature__heading">
                <div>
                    <p class="mt-section-kicker"><?php esc_html_e('Featured conversations', 'astra-child'); ?></p>
                    <h2 id="mt-feature-title"><?php esc_html_e('A thought worth staying with.', 'astra-child'); ?></h2>
                </div>
            </div>
            <div class="mt-feature__viewport">
                <?php $feature_index = 0; ?>
                <?php while ($featured_conversations->have_posts()) : $featured_conversations->the_post(); ?>
                    <?php
                    $feature_image = get_the_post_thumbnail_url(get_the_ID(), 'large');
                    if (!$feature_image) {
                        $feature_visual = function_exists('mirrortalk_fallback_visual') ? mirrortalk_fallback_visual(get_the_ID()) : array();
                        $feature_image = !empty($feature_visual['url']) ? $feature_visual['url'] : get_stylesheet_directory_uri() . '/assets/art/topic-journey-atmosphere-1800.jpg';
                    }
                    $feature_topic = mirrortalk_resolve_topic_context(get_the_ID());
                    $feature_words = str_word_count(wp_strip_all_tags(get_the_title() . ' ' . get_the_excerpt()));
                    ?>
                    <article
                        class="mt-feature__slide<?php echo $feature_index === 0 ? ' is-active' : ''; ?>"
                        style="--mt-slide-image: url('<?php echo esc_url($feature_image); ?>');"
                        data-mt-slide
                        data-mt-topic="<?php echo esc_attr($feature_topic['slug']); ?>"
                        data-mt-words="<?php echo esc_attr((string) $feature_words); ?>"
                        aria-hidden="<?php echo $feature_index === 0 ? 'false' : 'true'; ?>"
                    >
                        <div class="mt-feature__content">
                            <p class="mt-feature__meta"><?php echo esc_html(get_the_date()); ?></p>
                            <h3><?php the_title(); ?></h3>
                            <p><?php echo esc_html(wp_trim_words(get_the_excerpt(), 28)); ?></p>
                            <a class="mt-button" href="<?php the_permalink(); ?>"><?php esc_html_e('Enter the conversation', 'astra-child'); ?></a>
                        </div>
                    </article>
                    <?php $feature_index++; ?>
                <?php endwhile; ?>
                <?php wp_reset_postdata(); ?>
            </div>
            <div class="mt-feature__progress" aria-hidden="true"><span data-mt-slider-progress></span></div>
            <p class="mt-feature__personalization" data-mt-personalization-note hidden></p>
        </section>
    <?php endif; ?>

    <section class="mt-home__section mt-home__section--plum" aria-labelledby="mt-pathways-title">
        <div class="mt-home__shell">
            <p class="mt-section-kicker"><?php esc_html_e('Begin where you are', 'astra-child'); ?></p>
            <h2 id="mt-pathways-title" class="mt-section-heading"><?php esc_html_e('Three gentle ways into the conversation.', 'astra-child'); ?></h2>
            <div class="mt-home__grid">
                <article class="mt-card">
                    <span class="mt-card__number">01</span>
                    <h3><?php esc_html_e('Ask', 'astra-child'); ?></h3>
                    <p><?php esc_html_e('Bring a real question and receive a reflection grounded in moments from the Mirror Talk archive.', 'astra-child'); ?></p>
                    <a href="<?php echo esc_url($ask_url); ?>"><?php esc_html_e('Start a reflection', 'astra-child'); ?></a>
                </article>
                <article class="mt-card">
                    <span class="mt-card__number">02</span>
                    <h3><?php esc_html_e('Listen', 'astra-child'); ?></h3>
                    <p><?php esc_html_e('Explore thoughtful conversations with authors, leaders and people shaped by meaningful life experience.', 'astra-child'); ?></p>
                    <a href="<?php echo esc_url($episodes_url); ?>"><?php esc_html_e('Browse episodes', 'astra-child'); ?></a>
                </article>
                <article class="mt-card">
                    <span class="mt-card__number">03</span>
                    <h3><?php esc_html_e('Belong', 'astra-child'); ?></h3>
                    <p><?php esc_html_e('Join a growing community that values curiosity, courage, compassion and honest personal growth.', 'astra-child'); ?></p>
                    <a href="<?php echo esc_url($contact_url); ?>"><?php esc_html_e('Join the community', 'astra-child'); ?></a>
                </article>
            </div>
        </div>
    </section>

    <section class="mt-home__shell mt-home__section" aria-labelledby="mt-topics-title">
        <p class="mt-section-kicker"><?php esc_html_e('Explore by what you need', 'astra-child'); ?></p>
        <h2 id="mt-topics-title" class="mt-section-heading"><?php esc_html_e('Wisdom for the questions life is asking.', 'astra-child'); ?></h2>
        <div class="mt-topic-links">
            <?php foreach (mirrortalk_topic_map() as $topic_slug => $topic) : ?>
                <?php
                $topic_url = home_url('/explore/' . $topic_slug . '/');
                ?>
                <a class="mt-topic-link" href="<?php echo esc_url($topic_url); ?>" data-mt-topic-link="<?php echo esc_attr($topic_slug); ?>">
                    <span><?php echo esc_html($topic['label']); ?></span>
                    <small><?php echo esc_html($topic['description']); ?></small>
                    <strong aria-hidden="true">↗</strong>
                </a>
            <?php endforeach; ?>
        </div>
    </section>

    <section class="mt-home__shell mt-home__living-question" aria-label="<?php esc_attr_e('Today’s question from Ask Mirror Talk', 'astra-child'); ?>">
        <?php if (function_exists('mirrortalk_render_question_of_the_day')) mirrortalk_render_question_of_the_day('home'); ?>
    </section>

    <section class="mt-home__shell mt-home__section" aria-labelledby="mt-latest-title">
        <p class="mt-section-kicker"><?php esc_html_e('From the archive', 'astra-child'); ?></p>
        <h2 id="mt-latest-title" class="mt-section-heading"><?php esc_html_e('Conversations for the season you are in.', 'astra-child'); ?></h2>
        <div class="mt-home__grid">
            <?php
            $latest_episodes = new WP_Query(
                array(
                    'post_type' => 'post',
                    'post_status' => 'publish',
                    'posts_per_page' => 3,
                    'ignore_sticky_posts' => true,
                )
            );

            if ($latest_episodes->have_posts()) :
                while ($latest_episodes->have_posts()) :
                    $latest_episodes->the_post();
                    ?>
                    <article class="mt-card">
                        <a class="mt-episode-card" href="<?php the_permalink(); ?>">
                            <?php
                            if (function_exists('mirrortalk_document_visual')) {
                                echo mirrortalk_document_visual(get_the_ID(), 'medium_large', array(
                                    'class' => 'mt-episode-card__image' . (has_post_thumbnail() ? '' : ' mt-episode-card__image--fallback'),
                                    'loading' => 'lazy',
                                    'decoding' => 'async',
                                    'fetchpriority' => 'low',
                                    'sizes' => '(max-width: 620px) calc(100vw - 48px), (max-width: 1100px) 45vw, 360px',
                                )); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
                            } elseif (has_post_thumbnail()) {
                                the_post_thumbnail('medium_large', array('class' => 'mt-episode-card__image', 'loading' => 'lazy', 'decoding' => 'async'));
                            } else {
                                echo '<span class="mt-episode-card__image mt-episode-card__image--fallback" aria-hidden="true"></span>';
                            }
                            ?>
                            <h3><?php the_title(); ?></h3>
                            <p><?php echo esc_html(wp_trim_words(get_the_excerpt(), 24)); ?></p>
                            <span class="mt-episode-card__meta"><?php echo esc_html(get_the_date()); ?></span>
                        </a>
                    </article>
                    <?php
                endwhile;
                wp_reset_postdata();
            else :
                ?>
                <p><?php esc_html_e('New conversations are on the way.', 'astra-child'); ?></p>
            <?php endif; ?>
        </div>
    </section>

    <section class="mt-home__shell mt-home__section" aria-label="<?php esc_attr_e('Ways to listen to Mirror Talk', 'astra-child'); ?>">
        <?php if (function_exists('mirrortalk_render_listen_invitation')) mirrortalk_render_listen_invitation('home'); ?>
    </section>

    <section class="mt-home__shell mt-home__section">
        <div class="mt-home__closing">
            <div>
                <p class="mt-section-kicker"><?php esc_html_e('Your next honest question', 'astra-child'); ?></p>
                <h2><?php esc_html_e('You do not need perfect words to begin.', 'astra-child'); ?></h2>
            </div>
            <a class="mt-button" href="<?php echo esc_url($ask_url); ?>"><?php esc_html_e('Ask what is on your heart', 'astra-child'); ?></a>
        </div>
    </section>
</main>
<?php
get_footer();
