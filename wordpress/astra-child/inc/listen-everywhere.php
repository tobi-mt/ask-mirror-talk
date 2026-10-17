<?php
/** Verified, reusable Listen Everywhere experience. */
if (!defined('ABSPATH')) { exit; }

function mirrortalk_listen_statuses() {
    return array(
        'verified_native' => __('Confirmed native listing', 'astra-child'),
        'verified_web' => __('Confirmed web playback', 'astra-child'),
        'rss_capable' => __('Confirmed RSS subscription', 'astra-child'),
        'unverified' => __('Unverified', 'astra-child'),
        'unavailable' => __('Unavailable', 'astra-child'),
    );
}

function mirrortalk_listen_platform_defaults() {
    $feed = get_theme_mod('mirrortalk_podcast_feed_url', 'https://anchor.fm/s/261b1464/podcast/rss');
    $checked = '2026-10-11';
    $rows = array(
        array('id'=>'spotify','name'=>'Spotify','url'=>'https://open.spotify.com/show/0trwqguYCic32smqh3Ny60','icon_url'=>'','description'=>__('Listen and follow on Spotify.', 'astra-child'),'category'=>'primary','capabilities'=>array('native','web'),'status'=>'verified_native','method'=>'Approved official show URL','last_checked'=>$checked,'order'=>10,'enabled'=>1,'devices'=>array('apple','android','desktop')),
        array('id'=>'apple-podcasts','name'=>'Apple Podcasts','url'=>'https://podcasts.apple.com/us/podcast/mirror-talk-soulful-conversations/id1518394292','icon_url'=>'','description'=>__('Listen and follow on Apple Podcasts.', 'astra-child'),'category'=>'primary','capabilities'=>array('native','web'),'status'=>'verified_native','method'=>'Apple Podcasts ID 1518394292','last_checked'=>$checked,'order'=>20,'enabled'=>1,'devices'=>array('apple','desktop')),
        array('id'=>'youtube','name'=>'YouTube','url'=>'https://www.youtube.com/channel/UCFj3nBFVYJhsEGciiu52eEw/','icon_url'=>'','description'=>__('Watch conversations and subscribe on YouTube.', 'astra-child'),'category'=>'primary','capabilities'=>array('web','video'),'status'=>'verified_web','method'=>'Approved official channel URL','last_checked'=>$checked,'order'=>30,'enabled'=>1,'devices'=>array('apple','android','desktop')),
        array('id'=>'rss','name'=>'Podcast RSS','url'=>esc_url_raw($feed),'icon_url'=>'','description'=>__('Copy or open the official feed in an RSS-compatible podcast app.', 'astra-child'),'category'=>'fallback','capabilities'=>array('rss'),'status'=>'rss_capable','method'=>'Configured official podcast feed','last_checked'=>$checked,'order'=>40,'enabled'=>1,'devices'=>array('apple','android','desktop')),
    );
    $review = array('YouTube Music','Amazon Music','Pocket Casts','Overcast','iHeartRadio','Deezer','Castbox','Pandora','Spreaker','Goodpods','AntennaPod','Breez','Podbean','Podcast Guru','Apollo','Castro','gPodder','Moon FM','Player FM','Podcast Republic','Podcast Addict','Anytime Player','Podchaser','Podverse','iVoox','Metacast','Steno.fm','PodLP','Podcast Index','Castamatic','Curiocaster','Great Pods');
    foreach ($review as $index => $name) {
        $rows[] = array('id'=>sanitize_title($name),'name'=>$name,'url'=>'','icon_url'=>'','description'=>'','category'=>$index < 8 ? 'secondary' : 'discovery','capabilities'=>array(),'status'=>'unverified','method'=>'','last_checked'=>'','order'=>100 + $index,'enabled'=>0,'devices'=>array());
    }
    return $rows;
}

function mirrortalk_listen_platforms($public_only = false) {
    $stored = get_option('mirrortalk_listen_platforms_v1', array());
    $platforms = is_array($stored) && $stored ? $stored : mirrortalk_listen_platform_defaults();
    $allowed_public = array('verified_native','verified_web','rss_capable');
    $platforms = array_values(array_filter($platforms, function ($platform) use ($public_only, $allowed_public) {
        return !$public_only || (!empty($platform['enabled']) && !empty($platform['url']) && in_array($platform['status'] ?? '', $allowed_public, true));
    }));
    usort($platforms, function ($a, $b) { return ((int) ($a['order'] ?? 999)) <=> ((int) ($b['order'] ?? 999)); });
    return $platforms;
}

function mirrortalk_listen_route() { add_rewrite_rule('^listen/?$', 'index.php?mirror_listen=1', 'top'); }
add_action('init', 'mirrortalk_listen_route');
add_filter('query_vars', function ($vars) { $vars[] = 'mirror_listen'; return $vars; });
add_filter('template_include', function ($template) {
    if (!get_query_var('mirror_listen')) return $template;
    global $wp_query;
    $wp_query->is_404 = false; $wp_query->is_page = true; $wp_query->is_home = false;
    status_header(200);
    $owned = get_stylesheet_directory() . '/listen.php';
    return is_readable($owned) ? $owned : $template;
}, 95);
function mirrortalk_refresh_listen_route_once() {
    $version = function_exists('mirrortalk_release_version') ? mirrortalk_release_version() : '1';
    if (get_option('mirrortalk_listen_route_version') === $version) return;
    flush_rewrite_rules(false);
    update_option('mirrortalk_listen_route_version', $version, false);
    if (function_exists('mirrortalk_indexnow_queue_url')) mirrortalk_indexnow_queue_url(home_url('/listen/'));
}
// Route recovery belongs to activation/wp-admin. Public visitors should never
// pay for a rewrite-table flush immediately after a release.
add_action('after_switch_theme', 'mirrortalk_refresh_listen_route_once', 60);
add_action('admin_init', 'mirrortalk_refresh_listen_route_once', 60);

function mirrortalk_listen_platform_badge($platform) {
    $name = trim((string) ($platform['name'] ?? ''));
    $parts = preg_split('/\s+/', $name);
    $letters = '';
    foreach (array_slice($parts, 0, 2) as $part) $letters .= function_exists('mb_substr') ? mb_substr($part, 0, 1) : substr($part, 0, 1);
    return strtoupper($letters ?: '▶');
}

function mirrortalk_render_platform_cards($context = 'directory', $limit = 0) {
    $platforms = mirrortalk_listen_platforms(true);
    if ($limit > 0) $platforms = array_slice($platforms, 0, $limit);
    if (!$platforms) return;
    $render = function ($items, $class = '') {
    echo '<div class="mt-listen-platforms ' . esc_attr($class) . '" data-mt-platform-directory>';
    foreach ($items as $platform) {
        $id = sanitize_title($platform['id'] ?? $platform['name']);
        $is_rss = $id === 'rss';
        $devices = implode(' ', array_map('sanitize_html_class', (array) ($platform['devices'] ?? array())));
        echo '<article class="mt-listen-platform" data-mt-platform-card data-platform="' . esc_attr($id) . '" data-devices="' . esc_attr($devices) . '">';
        if (!empty($platform['icon_url'])) echo '<span class="mt-listen-platform__mark"><img src="' . esc_url($platform['icon_url']) . '" alt="" loading="lazy" decoding="async"></span><div>';
        else echo '<span class="mt-listen-platform__mark" aria-hidden="true">' . esc_html(mirrortalk_listen_platform_badge($platform)) . '</span><div>';
        echo '<h3>' . esc_html($platform['name']) . '</h3><p>' . esc_html($platform['description'] ?: __('Choose this verified way to listen to Mirror Talk.', 'astra-child')) . '</p>';
        $destination = $is_rss ? $platform['url'] : mirrortalk_campaign_url($platform['url'], 'listen_directory', $id);
        echo '<div class="mt-listen-platform__actions"><a href="' . esc_url($destination) . '" target="_blank" rel="noopener" data-mt-platform-link="' . esc_attr($id) . '">' . esc_html($is_rss ? __('Open RSS feed', 'astra-child') : sprintf(__('Listen on %s', 'astra-child'), $platform['name'])) . ' <span aria-hidden="true">↗</span></a>';
        if ($is_rss) echo '<button type="button" data-mt-copy-rss="' . esc_url($platform['url']) . '">' . esc_html__('Copy feed URL', 'astra-child') . '</button>';
        echo '</div></div></article>';
    }
    echo '</div>';
    };
    if ($context === 'directory' && count($platforms) > 6) {
        $render(array_slice($platforms, 0, 6), 'mt-listen-platforms--directory');
        echo '<details class="mt-listen-platforms__more"><summary>' . esc_html__('More verified ways to listen', 'astra-child') . '</summary>';
        $render(array_slice($platforms, 6), 'mt-listen-platforms--directory');
        echo '</details>';
    } else $render($platforms, 'mt-listen-platforms--' . sanitize_html_class($context));
}

function mirrortalk_render_listen_invitation($context = 'home') {
    $episodes = function_exists('mirrortalk_get_feed_episodes') ? mirrortalk_get_feed_episodes(1) : array();
    $latest = $episodes ? $episodes[0] : array();
    ?>
    <section class="mt-listen-invite mt-listen-invite--<?php echo esc_attr($context); ?>" aria-labelledby="mt-listen-invite-<?php echo esc_attr($context); ?>">
        <div class="mt-listen-invite__copy"><p class="mt-section-kicker"><?php esc_html_e('Listen your way', 'astra-child'); ?></p><h2 id="mt-listen-invite-<?php echo esc_attr($context); ?>"><?php esc_html_e('Carry the conversation wherever life takes you.', 'astra-child'); ?></h2>
        <?php if (!empty($latest['title'])) : ?><p class="mt-listen-invite__latest"><span><?php esc_html_e('Latest episode', 'astra-child'); ?></span><strong><?php echo esc_html($latest['title']); ?></strong></p><?php endif; ?>
        <div class="mt-listen-invite__actions"><a class="mt-button" href="<?php echo esc_url(home_url('/listen/')); ?>"><?php esc_html_e('Choose where to listen', 'astra-child'); ?></a><a href="<?php echo esc_url(home_url('/podcast-episodes/')); ?>"><?php esc_html_e('Browse every conversation', 'astra-child'); ?> →</a></div></div>
        <div class="mt-listen-invite__platforms"><?php mirrortalk_render_platform_cards($context, 3); ?></div>
    </section>
    <?php
}

function mirrortalk_listen_schema($graph) {
    if (!is_array($graph) || !get_query_var('mirror_listen')) return $graph;
    $same_as = array();
    foreach (mirrortalk_listen_platforms(true) as $platform) if (($platform['id'] ?? '') !== 'rss') $same_as[] = $platform['url'];
    foreach ($graph['@graph'] as &$node) {
        if (($node['@type'] ?? '') === 'PodcastSeries') {
            $node['url'] = home_url('/listen/');
            $node['sameAs'] = array_values(array_unique(array_map('esc_url_raw', $same_as)));
        }
    }
    $graph['@graph'][] = array('@type'=>'CollectionPage','@id'=>home_url('/listen/') . '#webpage','url'=>home_url('/listen/'),'name'=>'Listen to Mirror Talk: Soulful Conversations Anywhere','isPartOf'=>array('@id'=>home_url('/') . '#website'),'about'=>array('@id'=>home_url('/') . '#podcast'));
    return $graph;
}
add_filter('mirrortalk_schema_graph', 'mirrortalk_listen_schema', 20);

function mirrortalk_listen_sanitize_platforms($input) {
    $statuses = array_keys(mirrortalk_listen_statuses());
    $categories = array('primary','secondary','fallback','discovery');
    $output = array();
    foreach ((array) $input as $raw) {
        $id = sanitize_title($raw['id'] ?? $raw['name'] ?? '');
        if (!$id) continue;
        $output[] = array(
            'id'=>$id,
            'name'=>sanitize_text_field($raw['name'] ?? ''),
            'url'=>esc_url_raw($raw['url'] ?? '', array('http','https')),
            'icon_url'=>esc_url_raw($raw['icon_url'] ?? '', array('http','https')),
            'description'=>sanitize_text_field($raw['description'] ?? ''),
            'category'=>in_array($raw['category'] ?? '', $categories, true) ? $raw['category'] : 'secondary',
            'capabilities'=>array_values(array_intersect((array) ($raw['capabilities'] ?? array()), array('native','web','rss','video'))),
            'status'=>in_array($raw['status'] ?? '', $statuses, true) ? $raw['status'] : 'unverified',
            'method'=>sanitize_text_field($raw['method'] ?? ''),
            'last_checked'=>preg_match('/^\d{4}-\d{2}-\d{2}$/', $raw['last_checked'] ?? '') ? $raw['last_checked'] : '',
            'order'=>absint($raw['order'] ?? 999),
            'enabled'=>empty($raw['enabled']) ? 0 : 1,
            'devices'=>array_values(array_intersect((array) ($raw['devices'] ?? array()), array('apple','android','desktop'))),
        );
    }
    return $output;
}

function mirrortalk_listen_health_check($force = false) {
    if (!$force && get_transient('mirrortalk_listen_health_lock')) return get_option('mirrortalk_listen_health_v1', array());
    set_transient('mirrortalk_listen_health_lock', 1, 10 * MINUTE_IN_SECONDS);
    $results = array();
    foreach (mirrortalk_listen_platforms(true) as $platform) {
        $started = microtime(true);
        $response = wp_safe_remote_get($platform['url'], array('timeout'=>3,'redirection'=>2,'limit_response_size'=>262144,'user-agent'=>'MirrorTalkLinkHealth/1.0; ' . home_url('/')));
        if (is_wp_error($response)) {
            $results[$platform['id']] = array('state'=>'review','code'=>0,'note'=>$response->get_error_message(),'checked_at'=>gmdate('c'));
            continue;
        }
        $code = (int) wp_remote_retrieve_response_code($response);
        $state = ($code >= 200 && $code < 400) ? 'healthy' : (in_array($code, array(401,403,405,429), true) ? 'review' : 'potentially_broken');
        $results[$platform['id']] = array('state'=>$state,'code'=>$code,'note'=>sprintf('%d ms', (int) ((microtime(true)-$started)*1000)),'checked_at'=>gmdate('c'));
    }
    update_option('mirrortalk_listen_health_v1', $results, false);
    delete_transient('mirrortalk_listen_health_lock');
    return $results;
}
add_action('mirrortalk_listen_health_event', function(){mirrortalk_runtime_run('listening_health','mirrortalk_listen_health_check',15*MINUTE_IN_SECONDS);});
function mirrortalk_listen_schedule_health_check() {
    if (!wp_next_scheduled('mirrortalk_listen_health_event')) wp_schedule_event(time() + HOUR_IN_SECONDS, 'daily', 'mirrortalk_listen_health_event');
}
add_action('after_switch_theme', 'mirrortalk_listen_schedule_health_check', 40);
add_action('admin_init', 'mirrortalk_listen_schedule_health_check', 40);

function mirrortalk_listen_admin_menu() {
    add_submenu_page('mirror-talk-intelligence', __('Listening platforms', 'astra-child'), __('Listening platforms', 'astra-child'), 'manage_mirrortalk_seo', 'mirror-talk-listening-platforms', 'mirrortalk_listen_admin_page');
}
add_action('admin_menu', 'mirrortalk_listen_admin_menu', 20);

function mirrortalk_listen_admin_page() {
    if (!current_user_can('manage_mirrortalk_seo')) wp_die(esc_html__('You cannot manage listening platforms.', 'astra-child'));
    if (isset($_POST['mt_listen_save'])) {
        check_admin_referer('mirrortalk_listen_save');
        update_option('mirrortalk_listen_platforms_v1', mirrortalk_listen_sanitize_platforms(wp_unslash($_POST['platforms'] ?? array())), false);
        echo '<div class="notice notice-success"><p>' . esc_html__('Listening platforms saved.', 'astra-child') . '</p></div>';
    }
    if (isset($_POST['mt_listen_check'])) { check_admin_referer('mirrortalk_listen_check'); mirrortalk_listen_health_check(true); echo '<div class="notice notice-success"><p>' . esc_html__('Public destinations checked. Review-needed results were not disabled.', 'astra-child') . '</p></div>'; }
    $platforms = mirrortalk_listen_platforms(false); $health = get_option('mirrortalk_listen_health_v1', array()); $statuses = mirrortalk_listen_statuses();
    ?>
    <div class="wrap"><h1><?php esc_html_e('Mirror Talk listening platforms', 'astra-child'); ?></h1><p><?php esc_html_e('Only enabled destinations with a confirmed status and URL can appear publicly. Automated checks never prove identity and never disable a destination.', 'astra-child'); ?></p>
    <form method="post"><?php wp_nonce_field('mirrortalk_listen_check'); ?><button class="button" name="mt_listen_check" value="1"><?php esc_html_e('Check public destinations now', 'astra-child'); ?></button></form>
    <form method="post" style="margin-top:16px"><?php wp_nonce_field('mirrortalk_listen_save'); ?><input type="hidden" name="mt_listen_save" value="1"><table class="widefat striped"><thead><tr><th><?php esc_html_e('Platform', 'astra-child'); ?></th><th><?php esc_html_e('Destination and description', 'astra-child'); ?></th><th><?php esc_html_e('Verification', 'astra-child'); ?></th><th><?php esc_html_e('Display', 'astra-child'); ?></th><th><?php esc_html_e('Health', 'astra-child'); ?></th></tr></thead><tbody>
    <?php foreach ($platforms as $i=>$platform) : $row_health = $health[$platform['id']] ?? array(); ?>
    <tr><td><input type="hidden" name="platforms[<?php echo esc_attr($i); ?>][id]" value="<?php echo esc_attr($platform['id']); ?>"><input class="regular-text" name="platforms[<?php echo esc_attr($i); ?>][name]" value="<?php echo esc_attr($platform['name']); ?>"></td>
    <td><input class="large-text" type="url" name="platforms[<?php echo esc_attr($i); ?>][url]" value="<?php echo esc_attr($platform['url']); ?>" placeholder="https://"><br><input class="large-text" name="platforms[<?php echo esc_attr($i); ?>][description]" value="<?php echo esc_attr($platform['description']); ?>" placeholder="<?php esc_attr_e('Short public description', 'astra-child'); ?>"><br><input class="large-text" type="url" name="platforms[<?php echo esc_attr($i); ?>][icon_url]" value="<?php echo esc_attr($platform['icon_url'] ?? ''); ?>" placeholder="<?php esc_attr_e('Approved icon URL (optional)', 'astra-child'); ?>"></td>
    <td><select name="platforms[<?php echo esc_attr($i); ?>][status]"><?php foreach ($statuses as $value=>$label) echo '<option value="' . esc_attr($value) . '" ' . selected($platform['status'], $value, false) . '>' . esc_html($label) . '</option>'; ?></select><br><input name="platforms[<?php echo esc_attr($i); ?>][method]" value="<?php echo esc_attr($platform['method']); ?>" placeholder="<?php esc_attr_e('Evidence/method', 'astra-child'); ?>"><br><input type="date" name="platforms[<?php echo esc_attr($i); ?>][last_checked]" value="<?php echo esc_attr($platform['last_checked']); ?>"></td>
    <td><label><input type="checkbox" name="platforms[<?php echo esc_attr($i); ?>][enabled]" value="1" <?php checked(!empty($platform['enabled'])); ?>> <?php esc_html_e('Public', 'astra-child'); ?></label><br><label><?php esc_html_e('Order', 'astra-child'); ?> <input type="number" min="0" max="999" name="platforms[<?php echo esc_attr($i); ?>][order]" value="<?php echo esc_attr((string) $platform['order']); ?>" style="width:72px"></label><br><select name="platforms[<?php echo esc_attr($i); ?>][category]"><?php foreach (array('primary','secondary','fallback','discovery') as $category) echo '<option value="' . esc_attr($category) . '" ' . selected($platform['category'], $category, false) . '>' . esc_html(ucfirst($category)) . '</option>'; ?></select><?php foreach ((array)($platform['capabilities'] ?? array()) as $capability) : ?><input type="hidden" name="platforms[<?php echo esc_attr($i); ?>][capabilities][]" value="<?php echo esc_attr($capability); ?>"><?php endforeach; ?><?php foreach ((array)($platform['devices'] ?? array()) as $device) : ?><input type="hidden" name="platforms[<?php echo esc_attr($i); ?>][devices][]" value="<?php echo esc_attr($device); ?>"><?php endforeach; ?></td>
    <td><strong><?php echo esc_html($row_health['state'] ?? __('Not checked', 'astra-child')); ?></strong><br><small><?php echo esc_html(trim(($row_health['code'] ?? '') . ' ' . ($row_health['checked_at'] ?? ''))); ?></small></td></tr>
    <?php endforeach; ?></tbody></table><?php submit_button(__('Save listening platforms', 'astra-child')); ?></form></div>
    <?php
}
