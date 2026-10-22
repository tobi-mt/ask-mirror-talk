<?php
/**
 * Mirror Talk Story Studio.
 *
 * A guided, reversible publishing layer for the Editorial Composer. Editors
 * provide the truthful source; this file selects and places supporting media
 * and invitations without writing generated markup into post_content.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_STORY_STUDIO_VERSION', '1.3.2');

/** Extract a YouTube ID directly from source text, including encoded query URLs. */
function mirrortalk_story_studio_find_video_id($source) {
    $source = html_entity_decode((string) $source, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    if (preg_match('~(?:https?:)?//(?:www\.)?(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:shorts/|embed/|watch\?[^\s"\'<>]*?\bv=))([A-Za-z0-9_-]{11})~i', $source, $match)) return $match[1];
    return '';
}

/** Return a video explicitly owned by this document, never the channel fallback. */
function mirrortalk_story_studio_source_video_id($post_id, $settings = array()) {
    if (!$post_id || !function_exists('mirrortalk_youtube_video_id')) return '';
    // Current editorial content is the strongest ownership signal. It must
    // outrank stale Story Studio values left by historical fallback releases.
    $content = (string) get_post_field('post_content', $post_id);
    if (preg_match('/\[mirror_talk_video\b[^\]]*\bid=["\']([A-Za-z0-9_-]{11})["\']/i', $content, $match)) return $match[1];
    if ($id = mirrortalk_story_studio_find_video_id($content)) return $id;
    $manual = esc_url_raw((string) ($settings['youtube_url'] ?? ''));
    if ($id = mirrortalk_youtube_video_id($manual)) return $id;
    $legacy = stripslashes((string) get_post_meta($post_id, '_elementor_data', true));
    if ($id = mirrortalk_story_studio_find_video_id($legacy)) return $id;
    return '';
}

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
        // Posts are editorial listening experiences. Published pages remain
        // quiet unless they own a YouTube video; that is strong author intent.
        $owns_video = $post && $post->post_type === 'page' && mirrortalk_story_studio_source_video_id($post_id, $defaults);
        $defaults['enabled'] = $post && ($post->post_type === 'post' || $owns_video) ? '1' : ($post && $post->post_status === 'publish' ? '0' : '1');
        return $defaults;
    }
    $settings=array_merge($defaults, $saved);
    // Historical releases could persist the entire Story Studio as disabled
    // before media became a governed part of every editorial post. Restore the
    // shell while preserving explicit per-player `none` and CTA choices.
    if(get_post_type($post_id)==='post')$settings['enabled']='1';
    return $settings;
}

/**
 * Keep the listening experience complete on every editorial post. This never
 * rewrites article copy. An explicit editorial decision can still disable an
 * individual module; missing and automatic legacy settings are repaired.
 */
function mirrortalk_story_studio_ensure_post_media($post_id) {
    $post=get_post($post_id);if(!$post||!in_array($post->post_type,array('post','page'),true)||in_array($post->post_status,array('trash','auto-draft'),true))return false;
    $settings=mirrortalk_story_studio_settings($post_id);$changed=false;
    $page_video=$post->post_type==='page'?mirrortalk_story_studio_source_video_id($post_id,$settings):'';
    if($post->post_type==='page'&&!$page_video)return false;
    if($post->post_type==='page'){
        if(($settings['enabled']??'')!=='1'){$settings['enabled']='1';$changed=true;}
        if(($settings['youtube_mode']??'')==='none'||empty($settings['youtube_mode'])){$settings['youtube_mode']='latest';$changed=true;}
    }
    foreach(array('enabled'=>'1','podcast_mode'=>'latest','youtube_mode'=>'latest','show_follow'=>'1','show_newsletter'=>'1')as$key=>$value){
        if($post->post_type==='page'&&in_array($key,array('podcast_mode','show_follow','show_newsletter'),true))continue;
        if(!array_key_exists($key,$settings)||$settings[$key]===''){$settings[$key]=$value;$changed=true;}
    }
    if($post->post_type==='post'&&$post->post_status==='publish'&&($settings['enabled']??'')!=='1'){$settings['enabled']='1';$changed=true;}
    $rss_audio=esc_url_raw((string)get_post_meta($post_id,'_mt_rss_audio_url',true));
    if($rss_audio&&($settings['podcast_audio']??'')!==$rss_audio){$settings['podcast_audio']=$rss_audio;$settings['podcast_mode']='latest';$changed=true;}
    if($changed||!is_array(get_post_meta($post_id,'_mt_story_studio',true)))update_post_meta($post_id,'_mt_story_studio',$settings);
    if(function_exists('mirrortalk_composer_v2_decisions')){
        $decisions=mirrortalk_composer_v2_decisions($post_id);$decision_changed=false;
        foreach($post->post_type==='page'?array('youtube_player'):array('podcast_player','youtube_player')as$key){
            if(($decisions[$key]['status']??'automatic')==='editorial')continue;
            if(empty($decisions[$key]['enabled'])){$decisions[$key]['enabled']=true;$decisions[$key]['status']='automatic';$decisions[$key]['updated_at']=time();$decision_changed=true;}
        }
        if($decision_changed)update_post_meta($post_id,'_mt_composer_decisions',$decisions);
    }
    return true;
}

add_action('save_post',function($post_id,$post){
    if(wp_is_post_revision($post_id)||wp_is_post_autosave($post_id)||(defined('DOING_AUTOSAVE')&&DOING_AUTOSAVE))return;
    mirrortalk_story_studio_ensure_post_media($post_id);
},90,2);

/** Small restartable backfill for posts created before Story Studio 1.1. */
function mirrortalk_story_studio_media_backfill(){
    global $wpdb;$cursor=(int)get_option('mirrortalk_story_media_cursor',0);
    $ids=$wpdb->get_col($wpdb->prepare(
        "SELECT ID FROM {$wpdb->posts} WHERE post_type IN ('post','page') AND post_status IN ('publish','future','draft','pending','private') AND ID>%d ORDER BY ID ASC LIMIT 20",
        $cursor
    ));
    if(!$ids){update_option('mirrortalk_story_media_backfill_version',MIRRORTALK_STORY_STUDIO_VERSION,false);delete_option('mirrortalk_story_media_cursor');return;}
    foreach($ids as$id){mirrortalk_story_studio_ensure_post_media($id);$cursor=max($cursor,(int)$id);}
    update_option('mirrortalk_story_media_cursor',$cursor,false);
    if(!wp_next_scheduled('mirrortalk_story_media_backfill'))wp_schedule_single_event(time()+2*MINUTE_IN_SECONDS,'mirrortalk_story_media_backfill');
}
add_action('mirrortalk_story_media_backfill','mirrortalk_story_studio_media_backfill');
add_action('init',function(){
    if(get_option('mirrortalk_story_media_backfill_version')===MIRRORTALK_STORY_STUDIO_VERSION)return;
    if(!wp_next_scheduled('mirrortalk_story_media_backfill'))wp_schedule_single_event(time()+MINUTE_IN_SECONDS,'mirrortalk_story_media_backfill');
},30);

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
    if ($chosen) foreach ($episodes as $episode) if (isset($episode['audio']) && $episode['audio'] === $chosen) return apply_filters('mirrortalk_story_studio_episode', $episode, $post_id);
    if ($chosen && $post_id) {
        $owned = apply_filters('mirrortalk_story_studio_episode', array(), $post_id);
        if (!empty($owned['audio']) && $owned['audio'] === $chosen) return $owned;
    }
    if ($post_id && ($source=mirrortalk_story_studio_title_tokens(get_the_title($post_id)))) {
        $best=array();$best_score=0;
        foreach($episodes as$episode){$candidate=mirrortalk_story_studio_title_tokens($episode['title']??'');$union=array_unique(array_merge($source,$candidate));$score=$union?count(array_intersect($source,$candidate))/count($union):0;if($score>$best_score){$best_score=$score;$best=$episode;}}
        if($best_score>=0.18)return apply_filters('mirrortalk_story_studio_episode', $best, $post_id);
    }
    $fallback=isset($episodes[0]) && is_array($episodes[0]) ? $episodes[0] : array();
    return apply_filters('mirrortalk_story_studio_episode', $fallback, $post_id);
}

function mirrortalk_story_studio_resolve_video($settings, $post_id = 0) {
    if (($settings['youtube_mode'] ?? 'latest') === 'none') return array();
    $id = mirrortalk_story_studio_source_video_id($post_id, $settings);
    if($id)return array('id'=>$id,'url'=>'https://www.youtube.com/watch?v='.$id,'title'=>$post_id?get_the_title($post_id):__('Selected Mirror Talk video','astra-child'),'thumbnail'=>'https://i.ytimg.com/vi/'.$id.'/hqdefault.jpg','source'=>'document');
    if(function_exists('mirrortalk_latest_youtube_video'))return (array)mirrortalk_latest_youtube_video();
    return function_exists('mirrortalk_youtube_fallback_video') ? (array)mirrortalk_youtube_fallback_video() : array();
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
    $source = ($video['source'] ?? '') === 'document' ? 'document' : 'latest';
    return '<aside class="mt-story-video" data-mt-story-video data-video-id="'.esc_attr($video['id']).'" data-video-source="'.esc_attr($source).'" aria-labelledby="mt-story-video-'.$post_id.'"><div class="mt-story-video__copy"><p class="mt-section-kicker">'.esc_html__('Watch and notice','astra-child').'</p><h2 id="mt-story-video-'.$post_id.'">'.esc_html($title).'</h2></div><div class="mt-story-video__media"'.$poster_style.'><button type="button" data-mt-story-video-play aria-label="'.esc_attr(sprintf(__('Play %s','astra-child'),$title)).'"><span aria-hidden="true">▶</span><strong>'.esc_html__('Play video','astra-child').'</strong><small>'.esc_html__('Starts muted','astra-child').'</small></button><div data-mt-story-video-frame></div></div></aside>';
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

/**
 * Place video at a genuine editorial boundary. With two or more article H2s,
 * insert immediately before the second section; otherwise place it before the
 * related-content/reflection close. Existing players are always respected.
 */
function mirrortalk_story_studio_insert_video($content, $module) {
    if (!$module || preg_match('/(?:data-mt-story-video|mt-legacy-video-facade|youtube(?:-nocookie)?\.com\/embed\/)/i', $content)) return $content;
    $search_from = 0;
    foreach (array('mt-composer-lead','mt-composer-takeaways') as $class) {
        $start = strpos($content, $class);
        if ($start !== false && preg_match('/<\/(?:section|aside)>/i', $content, $close, PREG_OFFSET_CAPTURE, $start)) $search_from = max($search_from, $close[0][1] + strlen($close[0][0]));
    }
    if (preg_match_all('/<h2\b[^>]*>/i', $content, $headings, PREG_OFFSET_CAPTURE, $search_from) && count($headings[0]) >= 2) {
        $position = $headings[0][1][1];
        return substr($content, 0, $position).$module.substr($content, $position);
    }
    foreach (array('<aside class="mt-composer-links"','<aside class="mt-reflection-bridge"') as $marker) {
        $position = strpos($content, $marker, $search_from);
        if ($position !== false) return substr($content, 0, $position).$module.substr($content, $position);
    }
    return $content.$module;
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
    // after the editorial orientation.
    if ($podcast) {
        $takeaway = strpos($content, 'mt-composer-takeaways');
        $position = $takeaway !== false ? strpos($content, '</aside>', $takeaway) : false;
        $content = $position !== false ? substr($content,0,$position+8).$podcast.substr($content,$position+8) : mirrortalk_story_studio_insert_after($content,$podcast,'</section>',1);
    }
    if($video)$content=mirrortalk_story_studio_insert_video($content,$video);
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
