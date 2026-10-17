<?php
/**
 * Mirror Talk Story Studio.
 *
 * A guided, reversible publishing layer for the Editorial Composer. Editors
 * provide the truthful source; this file selects and places supporting media
 * and invitations without writing generated markup into post_content.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_STORY_STUDIO_VERSION', '1.0.0');

function mirrortalk_story_studio_defaults() {
    return array(
        'enabled' => '1',
        'podcast_mode' => 'latest',
        'podcast_audio' => '',
        'youtube_mode' => 'latest',
        'youtube_url' => '',
        'show_follow' => '1',
        'show_newsletter' => '1',
    );
}

function mirrortalk_story_studio_settings($post_id) {
    $saved = get_post_meta($post_id, '_mt_story_studio', true);
    $defaults = mirrortalk_story_studio_defaults();
    if (!is_array($saved)) {
        $post = get_post($post_id);
        // Posts are editorial listening experiences, so the governed layer is
        // useful by default. Pages remain quiet unless an editor opts in.
        $defaults['enabled'] = $post && $post->post_type === 'post' ? '1' : ($post && $post->post_status === 'publish' ? '0' : '1');
        return $defaults;
    }
    return array_merge($defaults, $saved);
}

function mirrortalk_story_studio_episode_options() {
    $episodes = get_transient('mirrortalk_feed_episodes_v2');
    if (!is_array($episodes) || !$episodes) $episodes = get_option('mirrortalk_feed_episodes_last_good_v2', array());
    if ((!is_array($episodes) || !$episodes) && !wp_next_scheduled('mirrortalk_refresh_podcast_feed')) wp_schedule_single_event(time()+10, 'mirrortalk_refresh_podcast_feed');
    return is_array($episodes) ? array_slice($episodes, 0, 12) : array();
}

function mirrortalk_story_studio_title_tokens($value) {
    $words=preg_split('/[^\p{L}\p{N}]+/u',strtolower(remove_accents(wp_strip_all_tags((string)$value))),-1,PREG_SPLIT_NO_EMPTY);
    $stop=array_flip(array('the','and','with','from','that','this','your','you','how','why','what','into','mirror','talk','soulful','conversations'));
    return array_values(array_unique(array_filter($words,function($word)use($stop){return !isset($stop[$word])&&strlen($word)>=4;})));
}

function mirrortalk_story_studio_resolve_episode($settings, $post_id = 0) {
    if (($settings['podcast_mode'] ?? 'latest') === 'none') return array();
    $episodes = mirrortalk_story_studio_episode_options();
    $chosen = esc_url_raw((string) ($settings['podcast_audio'] ?? ''));
    if ($chosen) foreach ($episodes as $episode) if (isset($episode['audio']) && $episode['audio'] === $chosen) return $episode;
    if ($post_id && ($source=mirrortalk_story_studio_title_tokens(get_the_title($post_id)))) {
        $best=array();$best_score=0;
        foreach($episodes as$episode){$candidate=mirrortalk_story_studio_title_tokens($episode['title']??'');$union=array_unique(array_merge($source,$candidate));$score=$union?count(array_intersect($source,$candidate))/count($union):0;if($score>$best_score){$best_score=$score;$best=$episode;}}
        if($best_score>=0.18)return $best;
    }
    return isset($episodes[0]) && is_array($episodes[0]) ? $episodes[0] : array();
}

function mirrortalk_story_studio_resolve_video($settings, $post_id = 0) {
    if (($settings['youtube_mode'] ?? 'latest') === 'none') return array();
    $url = esc_url_raw((string) ($settings['youtube_url'] ?? ''));
    $id = function_exists('mirrortalk_youtube_video_id') ? mirrortalk_youtube_video_id($url) : '';
    if ($id) return array('id'=>$id,'url'=>'https://www.youtube.com/watch?v='.$id,'title'=>__('Selected Mirror Talk video','astra-child'),'thumbnail'=>'https://i.ytimg.com/vi/'.$id.'/hqdefault.jpg');
    if($post_id&&function_exists('mirrortalk_youtube_video_id')){$content=(string)get_post_field('post_content',$post_id);if(preg_match('#https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)[A-Za-z0-9_-]{11}[^\s"\'<]*#i',$content,$match)){$id=mirrortalk_youtube_video_id($match[0]);if($id)return array('id'=>$id,'url'=>'https://www.youtube.com/watch?v='.$id,'title'=>get_the_title($post_id),'thumbnail'=>'https://i.ytimg.com/vi/'.$id.'/hqdefault.jpg');}}
    return function_exists('mirrortalk_youtube_fallback_video') ? (array) mirrortalk_youtube_fallback_video() : array();
}

function mirrortalk_story_studio_plan($post_id) {
    $settings = mirrortalk_story_studio_settings($post_id);
    return array(
        'version' => MIRRORTALK_STORY_STUDIO_VERSION,
        'episode' => mirrortalk_story_studio_resolve_episode($settings, $post_id),
        'video' => mirrortalk_story_studio_resolve_video($settings, $post_id),
        'show_follow' => !empty($settings['show_follow']),
        'show_newsletter' => !empty($settings['show_newsletter']),
    );
}

function mirrortalk_story_studio_meta_box($post) {
    $settings = mirrortalk_story_studio_settings($post->ID);
    $episodes = mirrortalk_story_studio_episode_options();
    $word_count = str_word_count(trim(wp_strip_all_tags(strip_shortcodes((string)$post->post_content))));
    $publish_label = get_post_time(get_option('date_format').' · '.get_option('time_format'), false, $post, true);
    wp_nonce_field('mirrortalk_story_studio_save_'.$post->ID, 'mirrortalk_story_studio_nonce');
    ?>
    <div class="mt-story-studio-admin">
        <p><strong><?php esc_html_e('Give us the truth. The Composer shapes the experience.', 'astra-child'); ?></strong></p>
        <p><?php esc_html_e('Use the normal WordPress fields for the original title, content, featured image, author and publication date/time. Story Studio places the supporting experience without changing that source.', 'astra-child'); ?></p>
        <div class="mt-story-studio-admin__readiness" aria-label="<?php esc_attr_e('Source readiness','astra-child'); ?>">
            <span class="<?php echo $post->post_title ? 'is-ready' : 'needs-attention'; ?>"><strong><?php esc_html_e('Title','astra-child'); ?></strong><?php echo esc_html($post->post_title ? __('Ready','astra-child') : __('Needed','astra-child')); ?></span>
            <span class="<?php echo $word_count >= 80 ? 'is-ready' : 'needs-attention'; ?>"><strong><?php esc_html_e('Original content','astra-child'); ?></strong><?php echo esc_html(sprintf(__('%d words','astra-child'),$word_count)); ?></span>
            <span class="is-ready"><strong><?php esc_html_e('Featured image','astra-child'); ?></strong><?php echo esc_html(has_post_thumbnail($post->ID) ? __('Ready','astra-child') : __('Branded fallback','astra-child')); ?></span>
            <span class="is-ready"><strong><?php esc_html_e('Publication','astra-child'); ?></strong><?php echo esc_html($publish_label); ?></span>
        </div>
        <div class="mt-story-studio-admin__grid">
            <fieldset><legend><strong><?php esc_html_e('Podcast moment', 'astra-child'); ?></strong></legend>
                <label><input type="radio" name="mt_story_podcast_mode" value="latest" <?php checked($settings['podcast_mode'], 'latest'); ?>> <?php esc_html_e('Use the selected episode, or the latest when unavailable', 'astra-child'); ?></label><br>
                <label><input type="radio" name="mt_story_podcast_mode" value="none" <?php checked($settings['podcast_mode'], 'none'); ?>> <?php esc_html_e('No inline podcast player', 'astra-child'); ?></label>
                <p><label for="mt-story-episode"><?php esc_html_e('Episode', 'astra-child'); ?></label><br><select class="widefat" id="mt-story-episode" name="mt_story_podcast_audio"><option value=""><?php esc_html_e('Latest episode automatically', 'astra-child'); ?></option><?php foreach ($episodes as $episode) : ?><option value="<?php echo esc_attr($episode['audio']); ?>" <?php selected($settings['podcast_audio'], $episode['audio']); ?>><?php echo esc_html($episode['title']); ?></option><?php endforeach; ?></select></p>
            </fieldset>
            <fieldset><legend><strong><?php esc_html_e('YouTube moment', 'astra-child'); ?></strong></legend>
                <label><input type="radio" name="mt_story_youtube_mode" value="latest" <?php checked($settings['youtube_mode'], 'latest'); ?>> <?php esc_html_e('Use this URL, or the latest channel video when blank', 'astra-child'); ?></label><br>
                <label><input type="radio" name="mt_story_youtube_mode" value="none" <?php checked($settings['youtube_mode'], 'none'); ?>> <?php esc_html_e('No inline video', 'astra-child'); ?></label>
                <p><label for="mt-story-youtube"><?php esc_html_e('YouTube video or Short URL (optional)', 'astra-child'); ?></label><br><input class="widefat" id="mt-story-youtube" name="mt_story_youtube_url" type="url" value="<?php echo esc_attr($settings['youtube_url']); ?>" placeholder="https://youtube.com/watch?v=…"></p>
            </fieldset>
        </div>
        <p><label><input type="checkbox" name="mt_story_enabled" value="1" <?php checked(!empty($settings['enabled'])); ?>> <strong><?php esc_html_e('Enable the composed Story Studio experience on this page', 'astra-child'); ?></strong></label></p>
        <p><label><input type="checkbox" name="mt_story_show_follow" value="1" <?php checked(!empty($settings['show_follow'])); ?>> <?php esc_html_e('Invite readers to follow the podcast after listening', 'astra-child'); ?></label></p>
        <p><label><input type="checkbox" name="mt_story_show_newsletter" value="1" <?php checked(!empty($settings['show_newsletter'])); ?>> <?php esc_html_e('Offer the newsletter after the reader receives value', 'astra-child'); ?></label></p>
        <p class="description"><?php esc_html_e('Placement is automatic, responsive and reversible. Quotations, transcripts, factual statements, embeds and the permalink are never rewritten.', 'astra-child'); ?></p>
    </div>
    <?php
}

add_action('add_meta_boxes', function () {
    foreach (array('post','page') as $type) add_meta_box('mirrortalk-story-studio', __('Mirror Talk Story Studio', 'astra-child'), 'mirrortalk_story_studio_meta_box', $type, 'normal', 'high');
}, 29);

add_action('admin_head-post.php', 'mirrortalk_story_studio_admin_style');
add_action('admin_head-post-new.php', 'mirrortalk_story_studio_admin_style');
function mirrortalk_story_studio_admin_style() {
    echo '<style>.mt-story-studio-admin{padding:8px 4px 4px}.mt-story-studio-admin>p:first-child{font-family:Georgia,serif;font-size:1.35rem;color:#35243a}.mt-story-studio-admin__readiness{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:18px 0}.mt-story-studio-admin__readiness span{display:flex;min-height:54px;padding:10px;border:1px solid #d6cbd8;border-radius:10px;flex-direction:column;justify-content:center;background:#fff}.mt-story-studio-admin__readiness span.is-ready{border-color:#b7d5c0;background:#f4fbf6}.mt-story-studio-admin__readiness span.needs-attention{border-color:#e3c58b;background:#fffaf0}.mt-story-studio-admin__readiness strong{margin-bottom:3px;color:#54365d}.mt-story-studio-admin__grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:20px 0}.mt-story-studio-admin fieldset{padding:16px;border:1px solid #d6cbd8;border-radius:12px;background:#fcf9fc}.mt-story-studio-admin legend{padding:0 6px;color:#54365d}.mt-story-studio-admin select,.mt-story-studio-admin input[type=url]{margin-top:6px}@media(max-width:782px){.mt-story-studio-admin__grid,.mt-story-studio-admin__readiness{grid-template-columns:1fr}}</style>';
}

function mirrortalk_story_studio_save($post_id, $post) {
    if (wp_is_post_revision($post_id) || wp_is_post_autosave($post_id) || (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) || !$post || !in_array($post->post_type, array('post','page'), true)) return;
    if (!isset($_POST['mirrortalk_story_studio_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['mirrortalk_story_studio_nonce'])), 'mirrortalk_story_studio_save_'.$post_id) || !current_user_can('edit_post', $post_id)) return;
    $podcast_mode = sanitize_key(wp_unslash($_POST['mt_story_podcast_mode'] ?? 'latest'));
    $youtube_mode = sanitize_key(wp_unslash($_POST['mt_story_youtube_mode'] ?? 'latest'));
    $settings = array(
        'enabled' => !empty($_POST['mt_story_enabled']) ? '1' : '0',
        'podcast_mode' => in_array($podcast_mode, array('latest','none'), true) ? $podcast_mode : 'latest',
        'podcast_audio' => esc_url_raw(wp_unslash($_POST['mt_story_podcast_audio'] ?? '')),
        'youtube_mode' => in_array($youtube_mode, array('latest','none'), true) ? $youtube_mode : 'latest',
        'youtube_url' => esc_url_raw(wp_unslash($_POST['mt_story_youtube_url'] ?? '')),
        'show_follow' => !empty($_POST['mt_story_show_follow']) ? '1' : '0',
        'show_newsletter' => !empty($_POST['mt_story_show_newsletter']) ? '1' : '0',
    );
    $allowed_audio = array_column(mirrortalk_story_studio_episode_options(), 'audio');
    if ($settings['podcast_audio'] && !in_array($settings['podcast_audio'], $allowed_audio, true)) $settings['podcast_audio'] = '';
    if ($settings['youtube_url'] && (!function_exists('mirrortalk_youtube_video_id') || !mirrortalk_youtube_video_id($settings['youtube_url']))) $settings['youtube_url'] = '';
    if (function_exists('mirrortalk_composer_v2_snapshot')) mirrortalk_composer_v2_snapshot($post_id);
    update_post_meta($post_id, '_mt_story_studio', $settings);
    mirrortalk_composer_v2_log($post_id, 'story_studio_updated', array('podcast'=>$settings['podcast_mode'],'video'=>$settings['youtube_mode']));
}
add_action('save_post', 'mirrortalk_story_studio_save', 65, 2);

function mirrortalk_story_studio_podcast($episode, $post_id) {
    if (empty($episode['audio'])) return '';
    $title = (string) ($episode['title'] ?? __('Latest Mirror Talk episode', 'astra-child'));
    $duration = trim((string) ($episode['duration'] ?? ''));
    if ($duration !== '' && ctype_digit($duration)) {
        $seconds = (int) $duration;
        $duration = $seconds >= HOUR_IN_SECONDS ? sprintf('%d:%02d:%02d', intdiv($seconds,HOUR_IN_SECONDS), intdiv($seconds%HOUR_IN_SECONDS,MINUTE_IN_SECONDS), $seconds%MINUTE_IN_SECONDS) : sprintf('%d:%02d', intdiv($seconds,MINUTE_IN_SECONDS), $seconds%MINUTE_IN_SECONDS);
    }
    return '<aside class="mt-story-podcast" aria-labelledby="mt-story-podcast-'.$post_id.'"><div class="mt-story-podcast__eyebrow">'.esc_html__('Listen into the conversation','astra-child').'</div><div class="mt-story-podcast__heading"><div><h2 id="mt-story-podcast-'.$post_id.'">'.esc_html($title).'</h2><p>'.esc_html__('Stay with the idea in its original voice. You can pause, return, or continue reading at any time.','astra-child').'</p></div><span aria-hidden="true">◖</span></div><audio controls preload="none" src="'.esc_url($episode['audio']).'" data-mt-story-audio data-episode-title="'.esc_attr($title).'"></audio><div class="mt-story-podcast__meta">'.esc_html(trim((string)($episode['date']??'').($duration?' · '.$duration:''))).'</div></aside>';
}

function mirrortalk_story_studio_replaces_listen_invitation($post_id) {
    if (!$post_id || get_post_type($post_id) !== 'post') return false;
    $settings = mirrortalk_story_studio_settings($post_id);
    $plan = mirrortalk_story_studio_plan($post_id);
    $decisions = function_exists('mirrortalk_composer_v2_decisions') ? mirrortalk_composer_v2_decisions($post_id) : array();
    return !empty($settings['enabled']) && !empty($plan['show_follow']) && !empty($decisions['follow_cta']['enabled']);
}

function mirrortalk_story_studio_video($video, $post_id) {
    if (empty($video['id'])) return '';
    $title = (string) ($video['title'] ?? __('A Mirror Talk video reflection', 'astra-child'));
    $poster = get_the_post_thumbnail_url($post_id, 'large');
    $poster_style = $poster ? ' style="--mt-story-poster:url(\''.esc_url($poster).'\')"' : '';
    return '<aside class="mt-story-video" data-mt-story-video data-video-id="'.esc_attr($video['id']).'" aria-labelledby="mt-story-video-'.$post_id.'"><div class="mt-story-video__copy"><p class="mt-section-kicker">'.esc_html__('Watch and notice','astra-child').'</p><h2 id="mt-story-video-'.$post_id.'">'.esc_html($title).'</h2><p>'.esc_html__('A visual companion to help this conversation land. The video loads only when you choose it.','astra-child').'</p></div><div class="mt-story-video__media"'.$poster_style.'><button type="button" data-mt-story-video-play aria-label="'.esc_attr(sprintf(__('Play %s','astra-child'),$title)).'"><span aria-hidden="true">▶</span><strong>'.esc_html__('Play the video','astra-child').'</strong><small>'.esc_html__('YouTube privacy-enhanced mode','astra-child').'</small></button><div data-mt-story-video-frame></div></div></aside>';
}

function mirrortalk_story_studio_follow($post_id) {
    $apple=mirrortalk_campaign_url('https://podcasts.apple.com/podcast/mirror-talk/id1518394292','article_follow','apple');
    $spotify=mirrortalk_campaign_url('https://open.spotify.com/show/0trwqguYCic32smqh3Ny60','article_follow','spotify');
    $youtube=mirrortalk_campaign_url('https://www.youtube.com/channel/UCFj3nBFVYJhsEGciiu52eEw/','article_follow','youtube');
    return '<aside class="mt-story-follow" aria-labelledby="mt-story-follow-'.$post_id.'"><p class="mt-section-kicker">'.esc_html__('Keep the conversation close','astra-child').'</p><h2 id="mt-story-follow-'.$post_id.'">'.esc_html__('Listen in the way that feels natural to you.','astra-child').'</h2><div><a href="'.esc_url($apple).'" target="_blank" rel="noopener">Apple Podcasts <span>↗</span></a><a href="'.esc_url($spotify).'" target="_blank" rel="noopener">Spotify <span>↗</span></a><a href="'.esc_url($youtube).'" target="_blank" rel="noopener">YouTube <span>↗</span></a></div></aside>';
}

function mirrortalk_story_studio_newsletter($post_id) {
    return '<aside class="mt-story-newsletter" aria-labelledby="mt-story-newsletter-'.$post_id.'"><div><p class="mt-section-kicker">'.esc_html__('A thoughtful note, not more noise','astra-child').'</p><h2 id="mt-story-newsletter-'.$post_id.'">'.esc_html__('Let the reflection continue gently.','astra-child').'</h2><p>'.esc_html__('Receive new conversations and carefully chosen prompts for living with greater clarity and intention.','astra-child').'</p></div><button class="mt-button" type="button" data-mt-open-dialog="mt-newsletter-invite">'.esc_html__('Join the newsletter','astra-child').'</button></aside>';
}

function mirrortalk_story_studio_insert_after($content, $module, $closing_tag, $occurrence = 1) {
    if (!$module) return $content;
    $offset = 0;$position = false;
    for ($index = 0; $index < $occurrence; $index++) {
        $position = stripos($content, $closing_tag, $offset);
        if ($position === false) return $content.$module;
        $offset = $position + strlen($closing_tag);
    }
    return substr($content, 0, $offset).$module.substr($content, $offset);
}

function mirrortalk_story_studio_render($content) {
    if (!function_exists('mirrortalk_composer_v2_should_render')) return $content;
    $post_id = get_the_ID();
    if (!mirrortalk_composer_v2_should_render($post_id)) return $content;
    $plan = mirrortalk_story_studio_plan($post_id);
    $settings = mirrortalk_story_studio_settings($post_id);
    if (empty($settings['enabled'])) return $content;
    $decisions = mirrortalk_composer_v2_decisions($post_id);
    $result = (array) get_post_meta($post_id, '_mt_composer_v2_result', true);
    $podcast = !empty($decisions['podcast_player']['enabled']) ? mirrortalk_story_studio_podcast($plan['episode'], $post_id) : '';
    $video = !empty($decisions['youtube_player']['enabled']) ? mirrortalk_story_studio_video($plan['video'], $post_id) : '';
    $follow = $plan['show_follow'] && !empty($decisions['follow_cta']['enabled']) ? mirrortalk_story_studio_follow($post_id) : '';
    $newsletter = $plan['show_newsletter'] && !empty($decisions['newsletter_cta']['enabled']) ? mirrortalk_story_studio_newsletter($post_id) : '';
    // Give readers context before asking them to play anything. The audio sits
    // after the editorial orientation; video appears deeper in the story.
    if ($podcast) {
        $takeaway = strpos($content, 'mt-composer-takeaways');
        $position = $takeaway !== false ? strpos($content, '</aside>', $takeaway) : false;
        $content = $position !== false ? substr($content,0,$position+8).$podcast.substr($content,$position+8) : mirrortalk_story_studio_insert_after($content,$podcast,'</section>',1);
    }
    if ($video) $content = mirrortalk_story_studio_insert_after($content,$video,'</p>',4);
    return $content.$follow.$newsletter;
}
add_filter('the_content', 'mirrortalk_story_studio_render', 27);

/**
 * Asset eligibility must not call mirrortalk_composer_v2_should_render().
 * wp_enqueue_scripts runs before the main content loop, so in_the_loop() is
 * necessarily false there even when the Composer will render the document.
 */
function mirrortalk_story_studio_should_enqueue($post_id) {
    if (!$post_id || !is_singular(array('post','page')) || is_front_page()) return false;
    if ((function_exists('mirrortalk_is_trust_page') && mirrortalk_is_trust_page($post_id)) || is_page(array('ask-mirror-talk','contact','join-us','insights'))) return false;
    if (strpos((string) get_post_field('post_content', $post_id), 'mirror-talk:preserve-format') !== false) return false;
    $result = (array) get_post_meta($post_id, '_mt_composer_v2_result', true);
    $settings = mirrortalk_story_studio_settings($post_id);
    return !empty($result) && !empty($settings['enabled']);
}

add_action('wp_enqueue_scripts', function () {
    if (!mirrortalk_story_studio_should_enqueue(get_queried_object_id())) return;
    wp_enqueue_script('mirror-talk-story-studio', get_stylesheet_directory_uri().'/editorial-story-studio.js', array(), function_exists('mirrortalk_asset_version') ? mirrortalk_asset_version('editorial-story-studio.js') : wp_get_theme()->get('Version'), true);
    wp_script_add_data('mirror-talk-story-studio', 'strategy', 'defer');
});

add_filter('mirrortalk_schema_graph', function ($schema) {
    if (!is_singular(array('post','page')) || empty($schema['@graph'])) return $schema;
    $post_id = get_queried_object_id();
    $settings = mirrortalk_story_studio_settings($post_id);
    if (empty($settings['enabled'])) return $schema;
    $plan = mirrortalk_story_studio_plan($post_id);
    foreach ($schema['@graph'] as &$node) {
        if (!in_array('Article', (array)($node['@type']??array()), true)) continue;
        if (!empty($plan['episode']['permalink'])) $node['subjectOf'][] = array('@type'=>'PodcastEpisode','name'=>$plan['episode']['title'],'url'=>$plan['episode']['permalink']);
        if (!empty($plan['video']['id'])) $node['video'] = array('@type'=>'VideoObject','name'=>$plan['video']['title'],'thumbnailUrl'=>$plan['video']['thumbnail'],'embedUrl'=>'https://www.youtube-nocookie.com/embed/'.$plan['video']['id']);
    }
    unset($node);
    return $schema;
}, 70);
