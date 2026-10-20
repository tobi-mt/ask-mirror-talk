<?php
/**
 * Mirror Talk Intelligence & SEO.
 *
 * Server-rendered SEO, first-party analytics consent, sitemap, content guidance,
 * link monitoring and weekly reporting without publishing private reflections.
 */
if (!defined('ABSPATH')) {
    exit;
}

function mirrortalk_seo_authoritative() {
    return (bool) apply_filters('mirrortalk_seo_authoritative', get_theme_mod('mirrortalk_seo_authoritative', true));
}

function mirrortalk_external_seo_active() {
    if (mirrortalk_seo_authoritative()) return false;
    $plugins = (array) get_option('active_plugins', array());
    return (bool) preg_grep('#^(all-in-one-seo-pack|surerank|wordpress-seo|seo-by-rank-math)/#', $plugins);
}

// AIOSEO's documented master switch prevents duplicate titles, canonicals,
// social markup and schema while it remains installed during the transition.
add_filter('aioseo_disable', function ($disabled) {
    return mirrortalk_seo_authoritative() ? true : $disabled;
}, PHP_INT_MAX);

// Mirror Talk publishes one complete sitemap. Disable WordPress core's parallel
// sitemap only while the native Mirror Talk SEO system is authoritative.
add_filter('wp_sitemaps_enabled', function ($enabled) {
    return mirrortalk_seo_authoritative() ? false : $enabled;
}, PHP_INT_MAX);

function mirrortalk_robots_directives($robots) {
    if (!mirrortalk_seo_authoritative()) return $robots;
    if (is_singular() && get_post_meta(get_queried_object_id(), '_mirrortalk_noindex', true)) {
        unset($robots['index']);
        $robots['noindex'] = true;
        $robots['follow'] = true;
    }
    $robots['max-image-preview'] = 'large';
    $robots['max-snippet'] = '-1';
    $robots['max-video-preview'] = '-1';
    return $robots;
}
add_filter('wp_robots', 'mirrortalk_robots_directives', 20);

function mirrortalk_intelligence_assets() {
    if (is_admin() || isset($_GET['mirror_player']) || (function_exists('mirrortalk_is_editor_preview_request') && mirrortalk_is_editor_preview_request())) {
        return;
    }
    wp_enqueue_script('mirror-talk-intelligence', get_stylesheet_directory_uri() . '/intelligence.js', array(), wp_get_theme()->get('Version'), true);
    wp_script_add_data('mirror-talk-intelligence', 'strategy', 'defer');
    wp_localize_script('mirror-talk-intelligence', 'MirrorTalkIntelligence', array(
        'endpoint' => rest_url('mirror-talk/v1/intelligence/event'),
        'siteHost' => wp_parse_url(home_url('/'), PHP_URL_HOST),
    ));
}
add_action('wp_enqueue_scripts', 'mirrortalk_intelligence_assets', 30);

function mirrortalk_render_analytics_consent() {
    if (is_admin() || isset($_GET['mirror_player']) || (function_exists('mirrortalk_is_editor_preview_request') && mirrortalk_is_editor_preview_request())) {
        return;
    }
    ?>
    <aside class="mt-privacy-choice" data-mt-privacy-choice hidden aria-label="<?php esc_attr_e('Privacy choice', 'astra-child'); ?>">
        <p><strong><?php esc_html_e('Help Mirror Talk learn—privately.', 'astra-child'); ?></strong><br><?php esc_html_e('Allow first-party, pseudonymous analytics so we can improve journeys, podcast discovery and performance. We never include your private questions.', 'astra-child'); ?></p>
        <div><button type="button" data-mt-consent="granted"><?php esc_html_e('Allow insights', 'astra-child'); ?></button><button type="button" data-mt-consent="denied" class="is-quiet"><?php esc_html_e('Necessary only', 'astra-child'); ?></button></div>
    </aside>
    <?php
}
add_action('wp_footer', 'mirrortalk_render_analytics_consent', 90);

function mirrortalk_seo_description($post_id = 0) {
    if (get_query_var('mirror_listen')) return __('Listen to Mirror Talk: Soulful Conversations on the website, Spotify, Apple Podcasts, YouTube and other verified podcast destinations.', 'astra-child');
    if (get_query_var('mirror_blog')) return __('Ideas, podcast conversations and grounded reflections for navigating purpose, relationships, healing, faith and meaningful growth.', 'astra-child');
    if (get_query_var('mirror_topic')) {
        $map = mirrortalk_topic_map();
        $topic = $map[get_query_var('mirror_topic')] ?? null;
        return $topic ? $topic['description'] : '';
    }
    if (is_singular() && $post_id) {
        $custom = get_post_meta($post_id, '_mirrortalk_meta_description', true);
        if ($custom) return wp_strip_all_tags($custom);
        $excerpt = get_the_excerpt($post_id);
        if (!$excerpt) $excerpt = wp_trim_words(wp_strip_all_tags(get_post_field('post_content', $post_id)), 28, '');
        return $excerpt;
    }
    if (is_category() || is_tag()) return wp_strip_all_tags(term_description());
    return get_bloginfo('description') ?: __('Soulful conversations about purpose, healing, faith, relationships, resilience and meaningful growth.', 'astra-child');
}

function mirrortalk_seo_title_parts($parts) {
    if (get_query_var('mirror_blog')) {
        $parts['title'] = __('Conversations', 'astra-child');
    }
    if (is_singular()) {
        $custom_title = trim((string) get_post_meta(get_queried_object_id(), '_mirrortalk_meta_title', true));
        if ($custom_title) $parts['title'] = $custom_title;
    }
    if (get_query_var('mirror_topic')) {
        $map = mirrortalk_topic_map();
        $topic = $map[get_query_var('mirror_topic')] ?? null;
        if ($topic) $parts['title'] = sprintf(__('%s Conversations & Podcast Episodes', 'astra-child'), $topic['label']);
    }
    return $parts;
}
add_filter('document_title_parts', 'mirrortalk_seo_title_parts');

function mirrortalk_authoritative_document_title($title) {
    if (!mirrortalk_seo_authoritative()) return $title;
    if (is_front_page()) return __('Mirror Talk Podcast | Soulful Conversations for Clarity and Growth', 'astra-child');
    if (get_query_var('mirror_listen')) return __('Listen to Mirror Talk Podcast | Spotify, Apple Podcasts & More', 'astra-child');
    if (get_query_var('mirror_blog')) return __('Conversations and Podcast Insights | Mirror Talk', 'astra-child');
    if (get_query_var('mirror_topic')) {
        $map = mirrortalk_topic_map(); $topic = $map[get_query_var('mirror_topic')] ?? null;
        if ($topic) return sprintf(__('%s Conversations and Podcast Episodes | Mirror Talk', 'astra-child'), $topic['label']);
    }
    if (is_singular()) {
        $custom = trim((string) get_post_meta(get_queried_object_id(), '_mirrortalk_meta_title', true));
        return $custom ?: single_post_title('', false) . ' | Mirror Talk';
    }
    return $title;
}
add_filter('pre_get_document_title', 'mirrortalk_authoritative_document_title', PHP_INT_MAX);

function mirrortalk_canonical_url() {
    if (get_query_var('mirror_listen')) return home_url('/listen/');
    $topic = get_query_var('mirror_topic');
    if ($topic) return home_url('/explore/' . sanitize_title($topic) . '/');
    if (is_singular()) return get_permalink();
    if (is_category() || is_tag()) {
        $term_url = get_term_link(get_queried_object());
        $canonical = is_wp_error($term_url) ? '' : $term_url;
        return get_query_var('paged') > 1 ? get_pagenum_link((int) get_query_var('paged')) : $canonical;
    }
    if (is_post_type_archive()) return get_query_var('paged') > 1 ? get_pagenum_link((int) get_query_var('paged')) : get_post_type_archive_link(get_query_var('post_type'));
    if (is_home() || get_query_var('mirror_blog')) return get_query_var('paged') > 1 ? get_pagenum_link((int) get_query_var('paged')) : home_url('/blog/');
    if (is_front_page()) return home_url('/');
    return '';
}

function mirrortalk_social_image($post_id = 0) {
    $fallback = mirrortalk_fallback_visual($post_id);
    if (!$post_id) return $fallback;
    $attachment_id = get_post_thumbnail_id($post_id);
    if (!$attachment_id) return $fallback;
    $source = wp_get_attachment_image_src($attachment_id, 'full');
    if (!$source || empty($source[0])) return $fallback;
    $alt = trim((string) get_post_meta($attachment_id, '_wp_attachment_image_alt', true));
    return array(
        'url' => $source[0],
        'width' => (int) $source[1],
        'height' => (int) $source[2],
        'alt' => $alt ?: get_the_title($post_id),
        'mime' => get_post_mime_type($attachment_id) ?: 'image/jpeg',
    );
}

/** Stable, varied brand art for documents without an editor-supplied image. */
function mirrortalk_fallback_visual($post_id = 0) {
    $choices = array(
        array('file'=>'mirror-talk-hero-atmosphere-1600.jpg','width'=>1600,'height'=>900),
        array('file'=>'topic-journey-atmosphere-1800.jpg','width'=>1800,'height'=>1200),
        array('file'=>'ask-reflection-atmosphere-1600.jpg','width'=>1600,'height'=>900),
    );
    $seed = $post_id ? (string)get_post_field('post_name',$post_id) : 'mirror-talk';
    $choice = $choices[abs(crc32($seed)) % count($choices)];
    return array(
        'url'=>get_stylesheet_directory_uri().'/assets/art/'.$choice['file'],
        'width'=>$choice['width'],'height'=>$choice['height'],
        'alt'=>$post_id ? sprintf(__('Atmospheric artwork for %s','astra-child'),get_the_title($post_id)) : __('Mirror Talk: Soulful Conversations','astra-child'),
        'mime'=>'image/jpeg','fallback'=>true,
    );
}

function mirrortalk_document_visual($post_id, $size='full', $attributes=array()) {
    if (has_post_thumbnail($post_id)) return get_the_post_thumbnail($post_id,$size,$attributes);
    $visual=mirrortalk_fallback_visual($post_id);$defaults=array('class'=>'mt-document-visual__image mt-document-visual__image--fallback','loading'=>'eager','decoding'=>'async');$attributes=array_merge($defaults,$attributes);
    $html='<img src="'.esc_url($visual['url']).'" width="'.esc_attr($visual['width']).'" height="'.esc_attr($visual['height']).'" alt="'.esc_attr($visual['alt']).'"';
    foreach($attributes as$key=>$value)$html.=' '.esc_attr($key).'="'.esc_attr($value).'"';
    return $html.'>';
}

function mirrortalk_schema_graph() {
    $site_url = home_url('/');
    $graph = array(
        array('@type' => 'Organization', '@id' => $site_url . '#organization', 'name' => 'Mirror Talk', 'url' => $site_url, 'description' => 'Soulful conversations and grounded reflections for greater clarity, purpose and personal growth.', 'founder' => array('@id' => $site_url . '#tobi-ojekunle'), 'sameAs' => array(
            'https://podcasts.apple.com/podcast/mirror-talk/id1518394292',
            'https://open.spotify.com/show/0trwqguYCic32smqh3Ny60',
            'https://www.youtube.com/channel/UCFj3nBFVYJhsEGciiu52eEw/',
            'https://www.patreon.com/MirrorTalk',
            'https://whatsapp.com/channel/0029VaEER5vC1Fu8V82fFm0u',
        )),
        array('@type' => 'Person', '@id' => $site_url . '#tobi-ojekunle', 'name' => 'Tobi Ojekunle', 'jobTitle' => 'Host and Founder', 'worksFor' => array('@id' => $site_url . '#organization'), 'knowsAbout' => array('Podcasting', 'Personal growth', 'Purpose', 'Resilience', 'Relationships', 'Spirituality', 'Leadership')),
        array('@type' => 'WebSite', '@id' => $site_url . '#website', 'url' => $site_url, 'name' => 'Mirror Talk', 'inLanguage' => 'en', 'publisher' => array('@id' => $site_url . '#organization')),
        array('@type' => 'PodcastSeries', '@id' => $site_url . '#podcast', 'name' => 'Mirror Talk: Soulful Conversations', 'url' => $site_url, 'inLanguage' => 'en', 'author' => array('@id' => $site_url . '#tobi-ojekunle'), 'publisher' => array('@id' => $site_url . '#organization'), 'sameAs' => array('https://podcasts.apple.com/podcast/mirror-talk/id1518394292', 'https://open.spotify.com/show/0trwqguYCic32smqh3Ny60')),
    );
    $canonical = mirrortalk_canonical_url();
    if (is_singular('post')) {
        $post_id = get_queried_object_id();
        $image = mirrortalk_social_image($post_id);
        $categories = get_the_category($post_id);
        $author_id = (int) get_post_field('post_author', $post_id);
        $author = array('@type' => 'Person', 'name' => get_the_author_meta('display_name', $author_id), 'url' => get_author_posts_url($author_id));
        $expertise = trim((string) get_user_meta($author_id, 'mt_author_expertise', true));
        $credentials = trim((string) get_user_meta($author_id, 'mt_author_credentials', true));
        $same_as = preg_split('/\r\n|\r|\n/', (string) get_user_meta($author_id, 'mt_author_sameas', true));
        $same_as = array_values(array_filter(array_map('esc_url_raw', $same_as)));
        if ($expertise) $author['knowsAbout'] = array_values(array_filter(array_map('trim', explode(',', $expertise))));
        if ($credentials) $author['description'] = $credentials;
        if ($same_as) $author['sameAs'] = $same_as;
        $article = array('@type' => array('Article', 'PodcastEpisode'), '@id' => $canonical . '#episode', 'url' => $canonical,
            'headline' => get_the_title($post_id), 'description' => mirrortalk_seo_description($post_id),
            'datePublished' => get_the_date(DATE_W3C, $post_id), 'dateModified' => get_the_modified_date(DATE_W3C, $post_id),
            'mainEntityOfPage' => array('@type' => 'WebPage', '@id' => $canonical),
            'author' => $author,
            'isPartOf' => array('@id' => $site_url . '#podcast'), 'publisher' => array('@id' => $site_url . '#organization'));
        if ($image['url']) $article['image'] = array('@type' => 'ImageObject', 'url' => $image['url'], 'width' => $image['width'], 'height' => $image['height']);
        if ($categories) $article['articleSection'] = $categories[0]->name;
        $keywords = wp_get_post_tags($post_id, array('fields' => 'names'));
        if ($keywords) $article['keywords'] = implode(', ', $keywords);
        $graph[] = $article;
    }
    if (function_exists('mirrortalk_youtube_surface') && mirrortalk_youtube_surface() && function_exists('mirrortalk_latest_youtube_video')) {
        $video = mirrortalk_latest_youtube_video();
        if (!empty($video['id'])) {
            $video_schema = array(
                '@type' => 'VideoObject',
                '@id' => home_url('/') . '#latest-youtube-video',
                'name' => $video['title'],
                'description' => __('The latest visual conversation from Mirror Talk: Soulful Conversations.', 'astra-child'),
                'thumbnailUrl' => array($video['thumbnail']),
                'embedUrl' => 'https://www.youtube-nocookie.com/embed/' . $video['id'],
                'contentUrl' => $video['url'],
                'publisher' => array('@id' => $site_url . '#organization'),
            );
            if (!empty($video['published'])) $video_schema['uploadDate'] = $video['published'];
            $graph[] = $video_schema;
        }
    }
    if ($canonical && !is_front_page()) {
        $graph[] = array('@type' => 'BreadcrumbList', '@id' => $canonical . '#breadcrumb', 'itemListElement' => array(
            array('@type' => 'ListItem', 'position' => 1, 'name' => 'Home', 'item' => $site_url),
            array('@type' => 'ListItem', 'position' => 2, 'name' => wp_get_document_title(), 'item' => $canonical),
        ));
    }
    return apply_filters('mirrortalk_schema_graph', array('@context' => 'https://schema.org', '@graph' => $graph));
}

function mirrortalk_seo_head() {
    if (is_admin() || is_search() || is_404() || isset($_GET['mirror_player']) || mirrortalk_external_seo_active()) return;
    $post_id = is_singular() ? get_queried_object_id() : 0;
    $description = wp_trim_words(mirrortalk_seo_description($post_id), 30, '');
    $canonical = mirrortalk_canonical_url();
    $image = mirrortalk_social_image($post_id);
    $title = mirrortalk_authoritative_document_title(wp_get_document_title());
    echo "\n" . '<meta name="description" content="' . esc_attr($description) . '">' . "\n";
    if ($canonical) echo '<link rel="canonical" href="' . esc_url($canonical) . '">' . "\n";
    echo '<meta property="og:type" content="' . (is_singular('post') ? 'article' : 'website') . '">' . "\n";
    echo '<meta property="og:site_name" content="' . esc_attr(get_bloginfo('name')) . '">' . "\n";
    echo '<meta property="og:locale" content="' . esc_attr(str_replace('-', '_', get_bloginfo('language'))) . '">' . "\n";
    echo '<meta property="og:title" content="' . esc_attr($title) . '">' . "\n";
    echo '<meta property="og:description" content="' . esc_attr($description) . '">' . "\n";
    if ($canonical) echo '<meta property="og:url" content="' . esc_url($canonical) . '">' . "\n";
    if ($image['url']) {
        echo '<meta property="og:image" content="' . esc_url($image['url']) . '">' . "\n";
        echo '<meta property="og:image:secure_url" content="' . esc_url(set_url_scheme($image['url'], 'https')) . '">' . "\n";
        echo '<meta property="og:image:type" content="' . esc_attr($image['mime']) . '">' . "\n";
        echo '<meta property="og:image:width" content="' . esc_attr((string) $image['width']) . '">' . "\n";
        echo '<meta property="og:image:height" content="' . esc_attr((string) $image['height']) . '">' . "\n";
        echo '<meta property="og:image:alt" content="' . esc_attr($image['alt']) . '">' . "\n";
    }
    echo '<meta name="twitter:card" content="summary_large_image">' . "\n";
    echo '<meta name="twitter:title" content="' . esc_attr($title) . '">' . "\n";
    echo '<meta name="twitter:description" content="' . esc_attr($description) . '">' . "\n";
    echo '<link rel="alternate" type="text/plain" title="Mirror Talk AI source guide" href="' . esc_url(home_url('/llms.txt')) . '">' . "\n";
    if ($image['url']) echo '<meta name="twitter:image" content="' . esc_url($image['url']) . '"><meta name="twitter:image:alt" content="' . esc_attr($image['alt']) . '">' . "\n";
    if (is_singular('post')) {
        echo '<meta property="article:published_time" content="' . esc_attr(get_the_date(DATE_W3C, $post_id)) . '">' . "\n";
        echo '<meta property="article:modified_time" content="' . esc_attr(get_the_modified_date(DATE_W3C, $post_id)) . '">' . "\n";
        $categories = get_the_category($post_id);
        if ($categories) echo '<meta property="article:section" content="' . esc_attr($categories[0]->name) . '">' . "\n";
        foreach (wp_get_post_tags($post_id, array('fields' => 'names')) as $tag) echo '<meta property="article:tag" content="' . esc_attr($tag) . '">' . "\n";
    }
    echo '<script type="application/ld+json">' . wp_json_encode(mirrortalk_schema_graph(), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . '</script>' . "\n";
}
remove_action('wp_head', 'rel_canonical');
add_action('wp_head', 'mirrortalk_seo_head', 2);

function mirrortalk_sitemap_rules() {
    // Avoid collisions with SEO plugins that reserve every .xml request before
    // WordPress reaches the active theme. XML does not require a file suffix.
    add_rewrite_rule('^mirror-talk-sitemap/?$', 'index.php?mirror_sitemap=1', 'top');
}
add_action('init', 'mirrortalk_sitemap_rules');
add_filter('query_vars', function ($vars) { $vars[] = 'mirror_sitemap'; return $vars; });

function mirrortalk_render_sitemap() {
    $request_path = wp_parse_url((string) ($_SERVER['REQUEST_URI'] ?? ''), PHP_URL_PATH);
    if (!get_query_var('mirror_sitemap') && untrailingslashit((string) $request_path) !== '/mirror-talk-sitemap') return;
    status_header(200); nocache_headers(); header('Content-Type: application/xml; charset=UTF-8');
    $render = function () {
    $urls = array(array('loc' => home_url('/'), 'modified' => gmdate('c')), array('loc' => home_url('/listen/'), 'modified' => gmdate('c')));
    $posts = get_posts(array('post_type' => array('post', 'page'), 'post_status' => 'publish', 'numberposts' => -1, 'orderby' => 'modified', 'order' => 'DESC'));
    foreach ($posts as $post) {
        if (get_post_meta($post->ID, '_mirrortalk_noindex', true)) continue;
        $image = mirrortalk_social_image($post->ID);
        $urls[] = array('loc' => get_permalink($post), 'modified' => get_post_modified_time('c', true, $post), 'image' => $image['url']);
    }
    $terms = get_terms(array('taxonomy' => array('category', 'post_tag'), 'hide_empty' => true));
    if (!is_wp_error($terms)) foreach ($terms as $term) $urls[] = array('loc' => get_term_link($term), 'modified' => gmdate('c'));
    foreach (array_keys(mirrortalk_topic_map()) as $slug) $urls[] = array('loc' => home_url('/explore/' . $slug . '/'), 'modified' => gmdate('c'));
    echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:image=\"http://www.google.com/schemas/sitemap-image/1.1\">\n";
    foreach ($urls as $url) {
        echo '<url><loc>' . esc_url($url['loc']) . '</loc><lastmod>' . esc_html($url['modified']) . '</lastmod>';
        if (!empty($url['image'])) echo '<image:image><image:loc>' . esc_url($url['image']) . '</image:loc></image:image>';
        echo '</url>' . "\n";
    }
    echo '</urlset>';
    };
    echo function_exists('mirrortalk_discovery_document')
        ? mirrortalk_discovery_document('mirrortalk_main_sitemap_v2', 3 * HOUR_IN_SECONDS, $render)
        : (function () use ($render) { ob_start(); $render(); return (string) ob_get_clean(); })();
    exit;
}
add_action('template_redirect', 'mirrortalk_render_sitemap', 0);

function mirrortalk_seo_meta_box() {
    add_meta_box('mirrortalk-seo', __('Mirror Talk SEO Intelligence', 'astra-child'), 'mirrortalk_seo_meta_box_html', array('post', 'page'), 'side', 'high');
}
add_action('add_meta_boxes', 'mirrortalk_seo_meta_box');
function mirrortalk_seo_meta_box_html($post) {
    wp_nonce_field('mirrortalk_seo_save', 'mirrortalk_seo_nonce');
    $title = get_post_meta($post->ID, '_mirrortalk_meta_title', true);
    $description = get_post_meta($post->ID, '_mirrortalk_meta_description', true);
    $noindex = (bool) get_post_meta($post->ID, '_mirrortalk_noindex', true);
    $plain = wp_strip_all_tags($post->post_content); $words = str_word_count($plain); $links = substr_count($post->post_content, 'href=');
    echo '<p><label for="mirrortalk-meta-title"><strong>' . esc_html__('Search and social title', 'astra-child') . '</strong></label></p><input style="width:100%" type="text" maxlength="70" id="mirrortalk-meta-title" name="mirrortalk_meta_title" value="' . esc_attr($title) . '" placeholder="' . esc_attr__('Automatic from the page title', 'astra-child') . '">';
    echo '<p><label for="mirrortalk-meta-description"><strong>' . esc_html__('Search description', 'astra-child') . '</strong></label></p><textarea style="width:100%" rows="4" maxlength="170" id="mirrortalk-meta-description" name="mirrortalk_meta_description">' . esc_textarea($description) . '</textarea>';
    $social = mirrortalk_social_image($post->ID);
    echo '<p><strong>' . esc_html__('Shared-link preview', 'astra-child') . '</strong><br><img src="' . esc_url($social['url']) . '" alt="" style="display:block;width:100%;height:auto;margin-top:8px;border-radius:8px"><small>' . esc_html(has_post_thumbnail($post) ? __('Uses this featured image automatically.', 'astra-child') : __('Add a featured image to replace the Mirror Talk fallback card.', 'astra-child')) . '</small></p>';
    echo '<p><label><input type="checkbox" name="mirrortalk_noindex" value="1" ' . checked($noindex, true, false) . '> ' . esc_html__('Keep this page out of search results and the sitemap', 'astra-child') . '</label></p>';
    echo '<p><strong>' . esc_html__('Content signals', 'astra-child') . '</strong><br>' . esc_html(sprintf(__('%1$d words · %2$d links', 'astra-child'), $words, $links)) . '</p><ul>';
    if ($words < 500) echo '<li>' . esc_html__('Consider adding a fuller summary, key insights and transcript-derived context.', 'astra-child') . '</li>';
    if (!$links) echo '<li>' . esc_html__('Add at least one relevant internal topic or episode link.', 'astra-child') . '</li>';
    if (!has_post_thumbnail($post)) echo '<li>' . esc_html__('Add a meaningful featured image and alt text.', 'astra-child') . '</li>';
    echo '</ul>';
}
add_action('save_post', function ($post_id) {
    if (!isset($_POST['mirrortalk_seo_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['mirrortalk_seo_nonce'])), 'mirrortalk_seo_save') || !current_user_can('edit_post', $post_id)) return;
    if (isset($_POST['mirrortalk_meta_title'])) update_post_meta($post_id, '_mirrortalk_meta_title', sanitize_text_field(wp_unslash($_POST['mirrortalk_meta_title'])));
    if (isset($_POST['mirrortalk_meta_description'])) update_post_meta($post_id, '_mirrortalk_meta_description', sanitize_textarea_field(wp_unslash($_POST['mirrortalk_meta_description'])));
    if (isset($_POST['mirrortalk_noindex'])) update_post_meta($post_id, '_mirrortalk_noindex', '1');
    else delete_post_meta($post_id, '_mirrortalk_noindex');
});

function mirrortalk_weekly_seo_report() {
    $urls = array(home_url('/'), home_url('/listen/'), home_url('/podcast-episodes/'), home_url('/blog/'), home_url('/ask-mirror-talk/'));
    foreach (array_keys(mirrortalk_topic_map()) as $slug) $urls[] = home_url('/explore/' . $slug . '/');
    $issues = array(); $redirects = array();
    foreach ($urls as $url) {
        $response = wp_remote_head($url, array('timeout' => 3, 'redirection' => 0));
        $code = is_wp_error($response) ? 0 : wp_remote_retrieve_response_code($response);
        if ($code >= 300 && $code < 400) $redirects[] = $url . ' — HTTP ' . $code . ' → ' . wp_remote_retrieve_header($response, 'location');
        if ($code < 200 || $code >= 400) $issues[] = $url . ' — HTTP ' . $code;
    }
    update_option('mirrortalk_last_seo_audit', array('time' => time(), 'issues' => $issues, 'redirects' => $redirects), false);
    $subject = sprintf(__('Mirror Talk weekly intelligence & SEO report — %s', 'astra-child'), wp_date('j M Y'));
    $body = "Mirror Talk weekly site audit\n\nChecked: " . count($urls) . " priority URLs\nBroken/unavailable: " . count($issues) . "\nRedirects: " . count($redirects) . "\n";
    if ($issues) $body .= "\n" . implode("\n", $issues) . "\n";
    if ($redirects) $body .= "\nRedirect observations:\n" . implode("\n", $redirects) . "\n";
    $latest_reports = (array) get_option('mirrortalk_intelligence_weekly_reports', array());
    $latest_report = $latest_reports ? end($latest_reports) : array();
    if (!empty($latest_report['summary'])) $body .= "\nAudience and listening summary:\n" . $latest_report['summary'] . "\n";
    $body .= "\nIntelligence dashboard: " . admin_url('admin.php?page=mirror-talk-intelligence') . "\nSitemap: " . home_url('/mirror-talk-sitemap/');
    wp_mail(get_option('admin_email'), $subject, $body);
}
add_action('mirrortalk_weekly_seo_report',function(){mirrortalk_runtime_queue('mirrortalk_weekly_seo_email',array(),10);});
add_action('mirrortalk_weekly_seo_email',function(){mirrortalk_runtime_run('weekly_seo_email','mirrortalk_weekly_seo_report',15*MINUTE_IN_SECONDS);});
function mirrortalk_intelligence_schedule_weekly_report() {
    $schema_version = function_exists('mirrortalk_release_version') ? mirrortalk_release_version() : '2';
    if (get_option('mirrortalk_intelligence_schema_version') !== $schema_version) {
        flush_rewrite_rules(false);
        update_option('mirrortalk_intelligence_schema_version', $schema_version, false);
    }
    if (!wp_next_scheduled('mirrortalk_weekly_seo_report')) wp_schedule_event(time() + HOUR_IN_SECONDS, 'weekly', 'mirrortalk_weekly_seo_report');
}
add_action('after_switch_theme', 'mirrortalk_intelligence_schedule_weekly_report', 40);
add_action('admin_init', 'mirrortalk_intelligence_schedule_weekly_report', 40);
add_action('switch_theme', function () { wp_clear_scheduled_hook('mirrortalk_weekly_seo_report'); });
