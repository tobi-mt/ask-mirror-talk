<?php
/**
 * Contextual discovery and reflection journey helpers.
 *
 * These features connect editorial content to Ask Mirror Talk without loading
 * the heavy Ask application outside its dedicated page.
 */

if (!defined('ABSPATH')) {
    exit;
}

function mirrortalk_topic_map() {
    return array(
        'purpose' => array(
            'label' => __('Purpose', 'astra-child'),
            'description' => __('Direction, calling and the work of living with intention.', 'astra-child'),
            'keywords' => array('purpose', 'calling', 'meaning', 'direction', 'career'),
            'prompt' => __('What is this season teaching me about purpose and my next meaningful step?', 'astra-child'),
        ),
        'resilience' => array(
            'label' => __('Resilience', 'astra-child'),
            'description' => __('Courage, recovery and steadiness through difficult seasons.', 'astra-child'),
            'keywords' => array('resilience', 'courage', 'adversity', 'recovery', 'strength'),
            'prompt' => __('How can I meet this difficult season with courage without ignoring what I feel?', 'astra-child'),
        ),
        'relationships' => array(
            'label' => __('Relationships', 'astra-child'),
            'description' => __('Honest connection, communication, trust and healthy boundaries.', 'astra-child'),
            'keywords' => array('relationship', 'relationships', 'love', 'communication', 'boundaries'),
            'prompt' => __('What would a healthier and more honest way of relating look like here?', 'astra-child'),
        ),
        'faith' => array(
            'label' => __('Faith & spirituality', 'astra-child'),
            'description' => __('Spiritual grounding, surrender, hope and inner formation.', 'astra-child'),
            'keywords' => array('faith', 'spiritual', 'spirituality', 'god', 'surrender'),
            'prompt' => __('How might faith and honest reflection help me see this situation differently?', 'astra-child'),
        ),
        'healing' => array(
            'label' => __('Healing', 'astra-child'),
            'description' => __('Gentle conversations about grief, change, forgiveness and wholeness.', 'astra-child'),
            'keywords' => array('healing', 'grief', 'trauma', 'forgiveness', 'change'),
            'prompt' => __('What might healing ask me to acknowledge, release or approach with more compassion?', 'astra-child'),
        ),
        'leadership' => array(
            'label' => __('Leadership', 'astra-child'),
            'description' => __('Leading with clarity, service, integrity and humanity.', 'astra-child'),
            'keywords' => array('leadership', 'leader', 'business', 'success', 'work'),
            'prompt' => __('What would it mean to lead this next step with clarity, integrity and care?', 'astra-child'),
        ),
    );
}

function mirrortalk_resolve_topic_context($post_id = 0) {
    $post_id = $post_id ?: (is_singular() ? get_queried_object_id() : 0);
    $searchable = '';

    if ($post_id) {
        $searchable .= ' ' . get_the_title($post_id);
        $searchable .= ' ' . get_the_excerpt($post_id);
        $post_content = get_post_field('post_content', $post_id);
        $searchable .= ' ' . wp_trim_words(wp_strip_all_tags((string) $post_content), 120, '');
        $categories = get_the_category($post_id);
        foreach ($categories as $category) {
            $searchable .= ' ' . $category->slug . ' ' . $category->name;
        }
    }

    $searchable = strtolower($searchable);
    foreach (mirrortalk_topic_map() as $slug => $topic) {
        foreach ($topic['keywords'] as $keyword) {
            if (strpos($searchable, strtolower($keyword)) !== false) {
                return array_merge(array('slug' => $slug), $topic);
            }
        }
    }

    return array(
        'slug' => 'reflection',
        'label' => __('Reflection', 'astra-child'),
        'description' => __('A quiet invitation to notice what matters and choose a grounded next step.', 'astra-child'),
        'prompt' => __('What is this conversation inviting me to notice about my life and my next step?', 'astra-child'),
    );
}

function mirrortalk_topic_rewrite_rules() {
    add_rewrite_rule(
        '^explore/(purpose|resilience|relationships|faith|healing|leadership)/?$',
        'index.php?mirror_topic=$matches[1]',
        'top'
    );
}
add_action('init', 'mirrortalk_topic_rewrite_rules');

function mirrortalk_topic_query_var($query_vars) {
    $query_vars[] = 'mirror_topic';
    return $query_vars;
}
add_filter('query_vars', 'mirrortalk_topic_query_var');

function mirrortalk_topic_template($template) {
    $topic_slug = get_query_var('mirror_topic');
    if ($topic_slug && isset(mirrortalk_topic_map()[$topic_slug])) {
        return get_stylesheet_directory() . '/topic.php';
    }
    return $template;
}
add_filter('template_include', 'mirrortalk_topic_template');

function mirrortalk_refresh_topic_routes_once() {
    $route_version = function_exists('mirrortalk_release_version') ? mirrortalk_release_version() : '2';
    if (get_option('mirrortalk_topic_routes_version') !== $route_version) {
        flush_rewrite_rules(false);
        update_option('mirrortalk_topic_routes_version', $route_version, false);
    }
}
add_action('init', 'mirrortalk_refresh_topic_routes_once', 99);

function mirrortalk_build_ask_url($post_id = 0, $context = array()) {
    $post_id = $post_id ?: (is_singular() ? get_queried_object_id() : 0);
    $topic = array_merge(mirrortalk_resolve_topic_context($post_id), $context);
    $post = $post_id ? get_post($post_id) : null;

    return add_query_arg(
        array(
            'intent' => 'content_reflection',
            'theme' => sanitize_title($topic['slug']),
            'ref' => $post ? sanitize_title($post->post_name) : 'site_journey',
            'prefill' => $topic['prompt'],
        ),
        home_url('/ask-mirror-talk/')
    );
}

function mirrortalk_append_reflection_bridge($content) {
    if (!is_singular('post') || !in_the_loop() || !is_main_query()) {
        return $content;
    }

    $post_id = get_the_ID();
    $topic = mirrortalk_resolve_topic_context($post_id);
    $ask_url = mirrortalk_build_ask_url($post_id, $topic);

    ob_start();
    ?>
    <aside class="mt-reflection-bridge" aria-labelledby="mt-reflection-title-<?php echo esc_attr($post_id); ?>">
        <p class="mt-reflection-bridge__kicker"><?php esc_html_e('Reflect on this conversation', 'astra-child'); ?></p>
        <h2 id="mt-reflection-title-<?php echo esc_attr($post_id); ?>"><?php echo esc_html($topic['prompt']); ?></h2>
        <p><?php esc_html_e('Take this question into Ask Mirror Talk and receive a response grounded in related moments from the podcast archive.', 'astra-child'); ?></p>
        <a class="mt-button" href="<?php echo esc_url($ask_url); ?>"><?php esc_html_e('Reflect with Ask Mirror Talk', 'astra-child'); ?></a>
        <small><?php esc_html_e('You will be able to edit the question before sending it.', 'astra-child'); ?></small>
    </aside>
    <?php
    return $content . ob_get_clean();
}
add_filter('the_content', 'mirrortalk_append_reflection_bridge', 24);

function mirrortalk_render_ask_dock() {
    if (is_admin() || is_page('ask-mirror-talk') || is_404() || isset($_GET['mirror_player'])) {
        return;
    }

    $post_id = is_singular() ? get_queried_object_id() : 0;
    $topic = mirrortalk_resolve_topic_context($post_id);
    $label = is_singular('post')
        ? __('Reflect on this episode', 'astra-child')
        : __('Ask Mirror Talk', 'astra-child');
    ?>
    <a class="mt-ask-dock" href="<?php echo esc_url(mirrortalk_build_ask_url($post_id, $topic)); ?>" aria-label="<?php echo esc_attr($label); ?>" data-mt-open-dialog="mt-ask-invite">
        <span class="mt-ask-dock__mark" aria-hidden="true">✦</span>
        <span><?php echo esc_html($label); ?></span>
    </a>
    <?php
}
add_action('wp_footer', 'mirrortalk_render_ask_dock', 20);
