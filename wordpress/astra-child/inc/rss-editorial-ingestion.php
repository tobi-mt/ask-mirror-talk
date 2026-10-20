<?php
/**
 * RSS to Editorial Composer ingestion.
 *
 * Remote podcast evidence is inventoried in small, restartable jobs. Missing
 * episodes may become review-only drafts; this service never publishes, never
 * fabricates transcript text, and never replaces an editor-owned article.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_RSS_INGESTION_VERSION', '1.2.0');
define('MIRRORTALK_RSS_INGESTION_BATCH', 20);

function mirrortalk_rss_ingestion_feed_url() {
    return esc_url_raw(apply_filters('mirrortalk_podcast_feed_url', get_theme_mod('mirrortalk_podcast_feed_url', 'https://anchor.fm/s/261b1464/podcast/rss')));
}

function mirrortalk_rss_ingestion_seconds($duration) {
    if (is_numeric($duration)) return max(0, (int)$duration);
    $parts = array_map('intval', explode(':', (string)$duration));
    if (count($parts) === 3) return $parts[0] * HOUR_IN_SECONDS + $parts[1] * MINUTE_IN_SECONDS + $parts[2];
    if (count($parts) === 2) return $parts[0] * MINUTE_IN_SECONDS + $parts[1];
    return 0;
}

function mirrortalk_rss_ingestion_tier($duration) {
    $seconds = mirrortalk_rss_ingestion_seconds($duration);
    if ($seconds && $seconds < 20 * MINUTE_IN_SECONDS) return 'compact';
    if ($seconds && $seconds > 45 * MINUTE_IN_SECONDS) return 'deep-dive';
    return 'editorial';
}

function mirrortalk_rss_ingestion_clean_notes($html) {
    $html = preg_replace('#<(script|style|iframe|form)[^>]*>.*?</\1>#is', '', (string)$html);
    // The WordPress template owns the single H1. Feed headings begin at H2.
    $html = preg_replace('#<\s*h1\b([^>]*)>#i','<h2$1>',$html);
    $html = preg_replace('#<\s*/\s*h1\s*>#i','</h2>',$html);
    $html = wp_kses_post($html);
    return trim($html);
}

/** Fetch one bounded page. Remote I/O happens only inside a background job. */
function mirrortalk_rss_ingestion_fetch_page($offset = 0, $limit = MIRRORTALK_RSS_INGESTION_BATCH) {
    include_once ABSPATH . WPINC . '/feed.php';
    $feed = fetch_feed(mirrortalk_rss_ingestion_feed_url());
    if (is_wp_error($feed)) return $feed;
    $total = (int)$feed->get_item_quantity();
    $episodes = array();
    $items=$feed->get_items(max(0, (int)$offset), max(1, min(25, (int)$limit)));
    foreach ($items as $item_index=>$item) {
        $enclosure = $item->get_enclosure();
        $audio = $enclosure && $enclosure->get_link() ? esc_url_raw($enclosure->get_link()) : '';
        if (!$audio) continue;
        $guid = trim((string)$item->get_id());
        $permalink = esc_url_raw((string)$item->get_permalink());
        $title = sanitize_text_field(wp_strip_all_tags((string)$item->get_title()));
        $duration = $enclosure && method_exists($enclosure, 'get_duration') ? sanitize_text_field((string)$enclosure->get_duration()) : '';
        $source_identity = $guid ?: ($audio ?: ($permalink ?: $title));
        $episodes[] = array(
            'key' => hash('sha256', $source_identity),
            'feed_offset' => max(0, (int)$offset) + (int)$item_index,
            'guid' => sanitize_text_field($guid),
            'title' => $title,
            'audio' => $audio,
            'permalink' => $permalink,
            'published_gmt' => (int)$item->get_date('U'),
            'duration' => $duration,
            'tier' => mirrortalk_rss_ingestion_tier($duration),
            'notes' => mirrortalk_rss_ingestion_clean_notes($item->get_content() ?: $item->get_description()),
            'transcript' => function_exists('mirrortalk_feed_tag_url') ? mirrortalk_feed_tag_url($item, 'transcript') : '',
            'chapters' => function_exists('mirrortalk_feed_tag_url') ? mirrortalk_feed_tag_url($item, 'chapters') : '',
        );
    }
    return array('total'=>$total, 'consumed'=>count($items), 'episodes'=>$episodes);
}

function mirrortalk_rss_ingestion_normalize_title($title) {
    return trim(preg_replace('/\s+/u', ' ', strtolower(remove_accents(wp_strip_all_tags((string)$title)))));
}

/** Exact evidence only: an RSS key, audio URL, or exact normalized title. */
function mirrortalk_rss_ingestion_match($episode) {
    $key = (string)($episode['key'] ?? '');
    foreach (array('_mt_rss_episode_key'=>$key, '_mt_rss_audio_url'=>(string)($episode['audio'] ?? '')) as $meta_key=>$value) {
        if (!$value) continue;
        $ids = get_posts(array('post_type'=>'post','post_status'=>array('publish','draft','pending','future','private'),'numberposts'=>2,'fields'=>'ids','meta_key'=>$meta_key,'meta_value'=>$value,'suppress_filters'=>true));
        if (count($ids) === 1) return array('post_id'=>(int)$ids[0], 'evidence'=>$meta_key);
    }
    $candidates = get_posts(array('post_type'=>'post','post_status'=>array('publish','draft','pending','future','private'),'numberposts'=>8,'s'=>$episode['title'],'suppress_filters'=>true));
    $needle = mirrortalk_rss_ingestion_normalize_title($episode['title']);
    $exact = array_values(array_filter($candidates, function($post) use ($needle) { return mirrortalk_rss_ingestion_normalize_title($post->post_title) === $needle; }));
    return count($exact) === 1 ? array('post_id'=>(int)$exact[0]->ID, 'evidence'=>'exact_title') : array('post_id'=>0, 'evidence'=>count($exact)>1?'ambiguous_title':'missing');
}

function mirrortalk_rss_ingestion_inventory() {
    $value = get_option('mirrortalk_rss_ingestion_inventory', array());
    return is_array($value) ? $value : array();
}

function mirrortalk_rss_ingestion_note_insights($html, $limit = 5) {
    $html=(string)$html;$candidates=array();
    if(preg_match_all('#<(?:h[2-6]|li|p)\b[^>]*>(.*?)</(?:h[2-6]|li|p)>#is',$html,$matches))$candidates=$matches[1];
    if(!$candidates)$candidates=preg_split('/(?<=[.!?])\s+/u',wp_strip_all_tags($html),-1,PREG_SPLIT_NO_EMPTY);
    $insights=array();$seen=array();
    foreach($candidates as$candidate){
        $text=trim(preg_replace('/\s+/u',' ',wp_strip_all_tags((string)$candidate)));
        $words=str_word_count($text);$key=strtolower(remove_accents($text));
        if($words<4||$words>42||isset($seen[$key])||preg_match('/^(?:subscribe|follow|share|listen on|copyright)\b/i',$text))continue;
        $seen[$key]=true;$insights[]=$text;if(count($insights)>=$limit)break;
    }
    return $insights;
}

/**
 * Build a useful source page without pretending that generated prose is a
 * transcript. Every factual sentence is derived from feed-declared fields;
 * reflective prompts are labelled as prompts rather than episode claims.
 */
function mirrortalk_rss_ingestion_source_body($episode) {
    $notes=trim((string)($episode['notes']??''));$title=trim((string)($episode['title']??''));
    $duration=trim((string)($episode['duration']??''));$published=(int)($episode['published_gmt']??0);
    $insights=mirrortalk_rss_ingestion_note_insights($notes);
    $body='<!-- mirror-talk:rss-source-v2 -->';
    $body.='<p class="mt-rss-orientation">'.esc_html(sprintf(__('Listen to “%s” in full, then use the official episode notes and reflection prompts below to stay with the ideas that matter to you.','astra-child'),$title)).'</p>';
    $facts=array();
    if($published)$facts[]=sprintf(__('Published %s','astra-child'),wp_date(get_option('date_format'),$published));
    if($duration)$facts[]=sprintf(__('Episode length: %s','astra-child'),$duration);
    $facts[]=__('Original audio supplied by the official Mirror Talk podcast feed','astra-child');
    $body.='<h2>'.esc_html__('Episode at a glance','astra-child').'</h2><ul>';
    foreach($facts as$fact)$body.='<li>'.esc_html($fact).'</li>';
    $body.='</ul>';
    if($insights){
        $body.='<h2>'.esc_html__('What this conversation explores','astra-child').'</h2><ul>';
        foreach($insights as$insight)$body.='<li>'.esc_html($insight).'</li>';
        $body.='</ul>';
    }
    $body.='<h2>'.esc_html__('Official episode notes','astra-child').'</h2>';
    $body.=$notes?:'<p>'.esc_html__('The publisher supplied the episode title, publication details and original audio, but no extended written synopsis. The recording above remains the primary source for this conversation.','astra-child').'</p>';
    $body.='<h2>'.esc_html__('Reflect after listening','astra-child').'</h2><ul>';
    $body.='<li>'.esc_html__('Which idea from this conversation stayed with you most clearly?','astra-child').'</li>';
    $body.='<li>'.esc_html__('What could you apply, question or explore further in your own life?','astra-child').'</li>';
    $body.='<li>'.esc_html__('Which moment would be valuable to revisit or share with someone you trust?','astra-child').'</li></ul>';
    if(!empty($episode['transcript']))$body.='<h2>'.esc_html__('Verified transcript source','astra-child').'</h2><p><a href="'.esc_url($episode['transcript']).'" target="_blank" rel="noopener">'.esc_html__('Open the transcript declared by the podcast feed','astra-child').'</a></p>';
    if(!empty($episode['chapters']))$body.='<p><a href="'.esc_url($episode['chapters']).'" target="_blank" rel="noopener">'.esc_html__('Open the chapter data declared by the podcast feed','astra-child').'</a></p>';
    $body.='<p class="mt-rss-source-note"><small>'.esc_html__('Source note: episode identity, publication details and media are reconciled against the official Mirror Talk RSS feed. Editorial framing does not replace or alter the original recording.','astra-child').'</small></p>';
    return $body;
}

function mirrortalk_rss_ingestion_enable_media($post_id,$episode) {
    $settings=function_exists('mirrortalk_story_studio_settings')?mirrortalk_story_studio_settings($post_id):array();
    $settings=array_merge(array('enabled'=>'1','podcast_mode'=>'latest','podcast_audio'=>'','youtube_mode'=>'latest','youtube_url'=>'','show_follow'=>'1','show_newsletter'=>'1'),is_array($settings)?$settings:array());
    $settings['enabled']='1';$settings['podcast_mode']='latest';$settings['podcast_audio']=esc_url_raw((string)($episode['audio']??''));$settings['youtube_mode']='latest';$settings['show_follow']='1';$settings['show_newsletter']='1';
    update_post_meta($post_id,'_mt_story_studio',$settings);
    if(function_exists('mirrortalk_composer_v2_decisions')){
        $decisions=mirrortalk_composer_v2_decisions($post_id);
        foreach(array('podcast_player','youtube_player','follow_cta','newsletter_cta')as$key){
            // An explicit editorial override remains authoritative. Automatic
            // and legacy states are repaired to the current publication rule.
            if(($decisions[$key]['status']??'automatic')==='editorial')continue;
            $decisions[$key]['enabled']=true;$decisions[$key]['status']='automatic';$decisions[$key]['updated_at']=time();
        }
        update_post_meta($post_id,'_mt_composer_decisions',$decisions);
    }
}

/** Refresh only pipeline-owned drafts; never overwrite an editor-owned post. */
function mirrortalk_rss_ingestion_recompose_owned_draft($post_id,$episode) {
    if(get_post_meta($post_id,'_mt_rss_episode_key',true)!==($episode['key']??''))return new WP_Error('rss_identity_mismatch',__('The RSS identity no longer matches this draft.','astra-child'));
    $post=get_post($post_id);if(!$post||$post->post_type!=='post')return new WP_Error('rss_post_missing',__('The episode draft could not be loaded.','astra-child'));
    $current=(string)$post->post_content;$managed=strpos($current,'<!-- mirror-talk:rss-source-v1 -->')!==false||strpos($current,'<!-- mirror-talk:rss-source-v2 -->')!==false;
    $owned_hash=(string)get_post_meta($post_id,'_mt_rss_owned_content_hash',true);
    if(!$managed&&(!$owned_hash||!hash_equals($owned_hash,hash('sha256',$current))))return new WP_Error('editor_content_preserved',__('This draft contains editor-owned content and was not overwritten.','astra-child'));
    $content=mirrortalk_rss_ingestion_source_body($episode);
    if(!hash_equals(hash('sha256',$current),hash('sha256',$content))){
        $history=(array)get_post_meta($post_id,'_mt_rss_content_history',true);$history[]=array('time'=>time(),'content'=>$current,'hash'=>hash('sha256',$current));
        update_post_meta($post_id,'_mt_rss_content_history',array_slice($history,-10));
        $updated=wp_update_post(array('ID'=>$post_id,'post_content'=>$content,'post_excerpt'=>wp_trim_words(wp_strip_all_tags((string)($episode['notes']??'')),32,'…')),true);
        if(is_wp_error($updated))return $updated;
    }
    update_post_meta($post_id,'_mt_rss_owned_content_hash',hash('sha256',$content));
    mirrortalk_rss_ingestion_enable_media($post_id,$episode);
    if(function_exists('mirrortalk_composer_v2_run'))mirrortalk_composer_v2_run($post_id,true);
    if(function_exists('mirrortalk_composer_v2_log'))mirrortalk_composer_v2_log($post_id,'rss_source_enriched',array('source'=>'official_feed','source_words'=>str_word_count(wp_strip_all_tags((string)($episode['notes']??''))),'players'=>'podcast,youtube'));
    return true;
}

function mirrortalk_rss_ingestion_author() {
    $users = get_users(array('role__in'=>array('administrator','editor'),'number'=>1,'orderby'=>'ID','order'=>'ASC','fields'=>'ID'));
    return $users ? (int)$users[0] : 1;
}

function mirrortalk_rss_ingestion_create_draft($episode) {
    $match = mirrortalk_rss_ingestion_match($episode);
    if (!empty($match['post_id'])) return (int)$match['post_id'];
    $published=(int)($episode['published_gmt']??0);
    $post_data=array(
        'post_type'=>'post', 'post_status'=>'draft', 'post_author'=>mirrortalk_rss_ingestion_author(),
        'post_title'=>(string)$episode['title'], 'post_content'=>mirrortalk_rss_ingestion_source_body($episode),
        'post_excerpt'=>wp_trim_words(wp_strip_all_tags((string)$episode['notes']), 32, '…'),
    );
    if($published){$post_data['post_date_gmt']=gmdate('Y-m-d H:i:s',$published);$post_data['post_date']=get_date_from_gmt($post_data['post_date_gmt']);}
    $post_id = wp_insert_post($post_data, true);
    if (is_wp_error($post_id)) return $post_id;
    $safe_payload = $episode; unset($safe_payload['notes']);
    foreach (array(
        '_mt_rss_episode_key'=>$episode['key'], '_mt_rss_audio_url'=>$episode['audio'],
        '_mt_rss_source_url'=>$episode['permalink'], '_mt_rss_published_gmt'=>(int)$episode['published_gmt'],
        '_mt_rss_transcript_url'=>$episode['transcript'], '_mt_rss_chapters_url'=>$episode['chapters'],
        '_mt_rss_article_tier'=>$episode['tier'], '_mt_rss_evidence'=>$safe_payload,
        '_mt_rss_review_state'=>'editorial-review-required',
    ) as $key=>$value) update_post_meta($post_id, $key, $value);
    update_post_meta($post_id,'_mt_rss_owned_content_hash',hash('sha256',(string)$post_data['post_content']));
    mirrortalk_rss_ingestion_enable_media($post_id,$episode);
    if (function_exists('mirrortalk_composer_v2_run')) mirrortalk_composer_v2_run($post_id, true);
    if (function_exists('mirrortalk_composer_v2_log')) mirrortalk_composer_v2_log($post_id, 'rss_draft_created', array('source'=>'official_feed','review'=>'required','published'=>'no'));
    return (int)$post_id;
}

/** A deterministic editorial gate: evidence may pass; generated assumptions cannot. */
function mirrortalk_rss_ingestion_review($post_id, $episode) {
    $reasons=array();$notes=wp_strip_all_tags((string)($episode['notes']??''));$words=str_word_count($notes);$title=trim((string)($episode['title']??''));$title_length=function_exists('mb_strlen')?mb_strlen($title):strlen($title);
    if(!$title||$title_length<12||$title_length>180)$reasons[]='title_length';
    if(preg_match('/(?:[:\-–—]|\b(?:part|episode|with))\s*$/iu',$title))$reasons[]='incomplete_title';
    if(empty($episode['audio'])||empty($episode['permalink']))$reasons[]='missing_primary_source';
    if(preg_match('/\b(?:lorem ipsum|tbd|to be announced|coming soon)\b/i',$notes))$reasons[]='placeholder_source';
    $result=(array)get_post_meta($post_id,'_mt_composer_v2_result',true);$description=trim((string)($result['description']??''));$search_title=trim((string)($result['search_title']??''));
    $search_title_length=function_exists('mb_strlen')?mb_strlen($search_title):strlen($search_title);$description_length=function_exists('mb_strlen')?mb_strlen($description):strlen($description);
    if(!$search_title||$search_title_length>70)$reasons[]='search_title_not_ready';
    if($description_length<100||$description_length>320)$reasons[]='description_not_ready';
    if(empty($result['source_preserved']))$reasons[]='source_preservation_unconfirmed';
    $page_words=str_word_count(wp_strip_all_tags((string)get_post_field('post_content',$post_id)));
    if($page_words<90)$reasons[]='episode_page_not_ready';
    $settings=function_exists('mirrortalk_story_studio_settings')?mirrortalk_story_studio_settings($post_id):array();
    if(empty($settings['enabled'])||empty($settings['podcast_audio'])||$settings['podcast_mode']==='none')$reasons[]='episode_player_not_ready';
    if(empty($settings['enabled'])||($settings['youtube_mode']??'none')==='none')$reasons[]='video_companion_not_ready';
    $decision=array('version'=>MIRRORTALK_RSS_INGESTION_VERSION,'time'=>time(),'passed'=>!$reasons,'source_words'=>$words,'page_words'=>$page_words,'source_profile'=>$words>=180?'substantial':($words?'concise':'audio-primary'),'transcript_declared'=>!empty($episode['transcript']),'primary_media_complete'=>!empty($episode['audio'])&&!empty($episode['permalink']),'reasons'=>array_values(array_unique($reasons)));
    update_post_meta($post_id,'_mt_rss_automation_review',$decision);
    update_post_meta($post_id,'_mt_rss_review_state',$decision['passed']?'automation-approved':'editorial-review-required');
    return $decision;
}

function mirrortalk_rss_ingestion_publish_if_ready($post_id,$episode) {
    if(get_post_status($post_id)==='publish')return array('published'=>false,'already_published'=>true,'review'=>(array)get_post_meta($post_id,'_mt_rss_automation_review',true));
    if(get_post_meta($post_id,'_mt_rss_episode_key',true)!==($episode['key']??''))return array('published'=>false,'review'=>array('passed'=>false,'reasons'=>array('source_identity_mismatch')));
    $composed=mirrortalk_rss_ingestion_recompose_owned_draft($post_id,$episode);if(is_wp_error($composed))return array('published'=>false,'review'=>array('passed'=>false,'reasons'=>array($composed->get_error_code())));
    $review=mirrortalk_rss_ingestion_review($post_id,$episode);if(empty($review['passed']))return array('published'=>false,'review'=>$review);
    $updated=wp_update_post(array('ID'=>$post_id,'post_status'=>'publish'),true);if(is_wp_error($updated)){return array('published'=>false,'review'=>$review,'error'=>$updated->get_error_message());}
    update_post_meta($post_id,'_mt_rss_review_state','automatically-published');update_post_meta($post_id,'_mt_rss_automatically_published_at',time());
    if(function_exists('mirrortalk_composer_v2_log'))mirrortalk_composer_v2_log($post_id,'rss_automatically_published',array('gate'=>'passed','source_words'=>$review['source_words']));
    return array('published'=>true,'review'=>$review);
}

function mirrortalk_rss_ingestion_state() {
    return array_merge(array('status'=>'idle','mode'=>'scan','cursor'=>0,'total'=>0,'scanned'=>0,'linked'=>0,'missing'=>0,'drafted'=>0,'published'=>0,'quarantined'=>0,'needs_source'=>0,'errors'=>0,'started'=>0,'updated'=>0,'completed'=>0), (array)get_option('mirrortalk_rss_ingestion_state', array()));
}

function mirrortalk_rss_ingestion_process_batch() {
    $state = mirrortalk_rss_ingestion_state();
    if ($state['status'] !== 'running') return;
    $page = mirrortalk_rss_ingestion_fetch_page((int)$state['cursor'], in_array($state['mode'],array('draft','auto'),true)?5:MIRRORTALK_RSS_INGESTION_BATCH);
    if (is_wp_error($page)) { $state['status']='failed'; $state['errors']++; $state['message']=$page->get_error_message(); $state['updated']=time(); update_option('mirrortalk_rss_ingestion_state',$state,false); return $page; }
    $inventory = mirrortalk_rss_ingestion_inventory();
    $state['total'] = (int)$page['total'];
    foreach ((array)$page['episodes'] as $episode) {
        $match = mirrortalk_rss_ingestion_match($episode); $post_id=(int)$match['post_id'];
        if (!$post_id && in_array($state['mode'],array('draft','auto'),true)) {
            $created = mirrortalk_rss_ingestion_create_draft($episode);
            if (is_wp_error($created)) { $state['errors']++; }
            else { $post_id=(int)$created; $state['drafted']++; $match['evidence']='rss_draft'; }
        }
        $publication=array();if($post_id&&$state['mode']==='auto'&&get_post_meta($post_id,'_mt_rss_episode_key',true)===$episode['key']&&get_post_status($post_id)!=='publish'){$publication=mirrortalk_rss_ingestion_publish_if_ready($post_id,$episode);if(!empty($publication['published']))$state['published']++;else $state['quarantined']++;}
        $status = $post_id ? (get_post_status($post_id)==='publish'?(get_post_meta($post_id,'_mt_rss_review_state',true)==='automatically-published'?'published':'linked'):(get_post_meta($post_id,'_mt_rss_review_state',true)==='editorial-review-required'?'quarantined':'draft')) : (empty($episode['notes'])?'needs-source':'missing');
        $inventory[$episode['key']] = array_merge($episode, array('notes'=>'','status'=>$status,'post_id'=>$post_id,'evidence'=>$match['evidence'],'automation_review'=>(array)($publication['review']??array()),'checked'=>time()));
        $state['scanned']++; if ($post_id) $state['linked']++; else { $state['missing']++; if ($status==='needs-source') $state['needs_source']++; }
    }
    $state['cursor'] += (int)($page['consumed']??count((array)$page['episodes'])); $state['updated']=time();
    if (empty($page['consumed']) || $state['cursor'] >= $state['total']) { $state['status']='complete'; $state['completed']=time(); }
    update_option('mirrortalk_rss_ingestion_inventory', array_slice($inventory, -1000, null, true), false);
    update_option('mirrortalk_rss_ingestion_state', $state, false);
    if ($state['status'] === 'running') mirrortalk_runtime_queue('mirrortalk_rss_ingestion_batch', array(), 20);
    return $state;
}
add_action('mirrortalk_rss_ingestion_batch', function(){ mirrortalk_runtime_run('rss_editorial_ingestion', 'mirrortalk_rss_ingestion_process_batch', 5*MINUTE_IN_SECONDS); });

function mirrortalk_rss_ingestion_start($mode) {
    $current=mirrortalk_rss_ingestion_state();if($current['status']==='running'&&(int)$current['updated']>time()-30*MINUTE_IN_SECONDS)return false;
    $mode=in_array($mode,array('scan','draft','auto'),true)?$mode:'scan';
    $state = array('status'=>'running','mode'=>$mode,'cursor'=>0,'total'=>0,'scanned'=>0,'linked'=>0,'missing'=>0,'drafted'=>0,'published'=>0,'quarantined'=>0,'needs_source'=>0,'errors'=>0,'started'=>time(),'updated'=>time(),'completed'=>0);
    update_option('mirrortalk_rss_ingestion_state',$state,false);
    mirrortalk_runtime_queue('mirrortalk_rss_ingestion_batch',array(),1); mirrortalk_runtime_request_dispatch();
    return true;
}

add_action('admin_post_mirrortalk_rss_ingestion_start', function(){
    if (!current_user_can('manage_options')) wp_die(esc_html__('You cannot run this pipeline.','astra-child'));
    check_admin_referer('mirrortalk_rss_ingestion_start'); $mode=sanitize_key($_POST['mode']??'scan'); mirrortalk_rss_ingestion_start($mode);
    wp_safe_redirect(add_query_arg(array('page'=>'mirror-talk-rss-ingestion','mt_job'=>'queued'),admin_url('admin.php'))); exit;
});

add_action('admin_post_mirrortalk_rss_ingestion_one', function(){
    if (!current_user_can('edit_posts')) wp_die(esc_html__('You cannot import this episode.','astra-child'));
    $key=sanitize_text_field($_GET['episode']??''); check_admin_referer('mirrortalk_rss_ingestion_one_'.$key); $inventory=mirrortalk_rss_ingestion_inventory();
    if(isset($inventory[$key])){$inventory[$key]['status']='queued';update_option('mirrortalk_rss_ingestion_inventory',$inventory,false);mirrortalk_runtime_queue('mirrortalk_rss_ingestion_one',array($key),1);mirrortalk_runtime_request_dispatch();}
    wp_safe_redirect(add_query_arg(array('page'=>'mirror-talk-rss-ingestion','mt_job'=>'queued'),admin_url('admin.php'))); exit;
});

add_action('mirrortalk_rss_ingestion_one',function($key){mirrortalk_runtime_run('rss_episode_'.substr(sanitize_key($key),0,24),function()use($key){
    $inventory=mirrortalk_rss_ingestion_inventory();if(!isset($inventory[$key]))return new WP_Error('rss_inventory_missing',__('The inventory record no longer exists.','astra-child'));
    $page=mirrortalk_rss_ingestion_fetch_page((int)($inventory[$key]['feed_offset']??0),1);if(is_wp_error($page))return $page;$episode=null;
    foreach($page['episodes']as$fresh)if(hash_equals($key,$fresh['key'])){$episode=$fresh;break;}if(!$episode)return new WP_Error('rss_identity_changed',__('The feed changed. Run a new scan before importing this episode.','astra-child'));
    $created=mirrortalk_rss_ingestion_create_draft($episode);if(is_wp_error($created))return $created;$inventory[$key]=array_merge($inventory[$key],array('post_id'=>(int)$created,'status'=>'draft','checked'=>time()));update_option('mirrortalk_rss_ingestion_inventory',$inventory,false);return $created;
},5*MINUTE_IN_SECONDS);},10,1);

function mirrortalk_rss_ingestion_schedule() {
    if(!wp_next_scheduled('mirrortalk_rss_ingestion_daily'))wp_schedule_event(time()+HOUR_IN_SECONDS,'daily','mirrortalk_rss_ingestion_daily');
}
add_action('init','mirrortalk_rss_ingestion_schedule',20);
add_action('after_switch_theme','mirrortalk_rss_ingestion_schedule');
add_action('mirrortalk_rss_ingestion_daily',function(){
    $state=mirrortalk_rss_ingestion_state();if($state['status']==='running'&&(int)$state['updated']>time()-30*MINUTE_IN_SECONDS)return;
    if($state['status']==='running'){ $state['status']='failed';$state['message']='Recovered a stale ingestion run.';update_option('mirrortalk_rss_ingestion_state',$state,false); }
    mirrortalk_rss_ingestion_start('auto');
});

/** Revisit existing drafts and quarantine records once after this upgrade. */
function mirrortalk_rss_ingestion_upgrade_reconcile(){
    $state=mirrortalk_rss_ingestion_state();
    if($state['status']==='running'&&(int)$state['updated']>time()-30*MINUTE_IN_SECONDS)return;
    mirrortalk_rss_ingestion_start('auto');
}
add_action('mirrortalk_rss_ingestion_upgrade_reconcile','mirrortalk_rss_ingestion_upgrade_reconcile');
add_action('init',function(){
    if(get_option('mirrortalk_rss_ingestion_upgrade_version')===MIRRORTALK_RSS_INGESTION_VERSION)return;
    update_option('mirrortalk_rss_ingestion_upgrade_version',MIRRORTALK_RSS_INGESTION_VERSION,false);
    if(!wp_next_scheduled('mirrortalk_rss_ingestion_upgrade_reconcile'))wp_schedule_single_event(time()+2*MINUTE_IN_SECONDS,'mirrortalk_rss_ingestion_upgrade_reconcile');
},31);

function mirrortalk_rss_ingestion_admin_page() {
    if (!current_user_can('edit_posts')) return; $state=mirrortalk_rss_ingestion_state(); $inventory=array_reverse(mirrortalk_rss_ingestion_inventory(),true);
    echo '<div class="wrap"><h1>'.esc_html__('RSS Editorial Pipeline','astra-child').'</h1><p>'.esc_html__('Bring every official episode into the owned Mirror Talk editorial system without duplicates or invented facts. The automatic workflow enriches pipeline-owned drafts, composes their SEO and presentation, verifies their media, and publishes only when every deterministic gate passes.','astra-child').'</p>';
    echo '<div class="notice notice-info inline"><p><strong>'.esc_html__('Factual safeguard:','astra-child').'</strong> '.esc_html__('Verified feed titles, dates, audio, publisher notes, chapters and declared transcript links remain the factual source. Concise notes receive transparent editorial framing and reflection prompts; they are never presented as a transcript. Editor-owned changes are preserved.','astra-child').'</p></div>';
    echo '<div style="display:grid;grid-template-columns:repeat(4,minmax(110px,1fr));gap:10px;margin:18px 0">'; foreach(array('total'=>__('Feed episodes','astra-child'),'scanned'=>__('Scanned','astra-child'),'linked'=>__('Matched','astra-child'),'drafted'=>__('Drafted','astra-child'),'published'=>__('Published automatically','astra-child'),'quarantined'=>__('Needs editorial evidence','astra-child'),'missing'=>__('Still missing','astra-child'),'errors'=>__('Errors','astra-child')) as$key=>$label) echo '<div style="background:#fff;border:1px solid #dcdcde;border-radius:10px;padding:14px"><strong style="font-size:22px">'.esc_html((string)$state[$key]).'</strong><br>'.esc_html($label).'</div>'; echo '</div>';
    echo '<p><strong>'.esc_html__('Status:','astra-child').'</strong> '.esc_html(ucfirst($state['status'])).' · '.esc_html__('Mode:','astra-child').' '.esc_html(ucfirst($state['mode'])).($state['updated']?' · '.esc_html(wp_date('Y-m-d H:i',(int)$state['updated'])):'').'</p><form method="post" action="'.esc_url(admin_url('admin-post.php')).'" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><input type="hidden" name="action" value="mirrortalk_rss_ingestion_start">'; wp_nonce_field('mirrortalk_rss_ingestion_start'); echo '<button class="button button-primary" name="mode" value="auto" onclick="return confirm(\''.esc_js(__('Reconcile the feed, enrich existing pipeline drafts and quarantined episodes, compose SEO and media, and publish only episodes that pass every factual and quality gate?','astra-child')).'\')">'.esc_html__('Enrich and publish ready episodes','astra-child').'</button><button class="button" name="mode" value="scan">'.esc_html__('Scan only','astra-child').'</button><button class="button" name="mode" value="draft">'.esc_html__('Create drafts only','astra-child').'</button></form><p class="description">'.esc_html__('The same guarded workflow runs daily. A concise source note is no longer rejected merely for its length; only missing identity, media, placeholder text, failed composition or protected editor changes remain quarantined.','astra-child').'</p>';
    echo '<h2>'.esc_html__('Episode inventory','astra-child').'</h2><table class="widefat striped"><thead><tr><th>'.esc_html__('Episode','astra-child').'</th><th>'.esc_html__('Source','astra-child').'</th><th>'.esc_html__('Editorial profile','astra-child').'</th><th>'.esc_html__('State','astra-child').'</th><th>'.esc_html__('Action','astra-child').'</th></tr></thead><tbody>';
    foreach(array_slice($inventory,0,100,true) as$key=>$episode){$post_id=(int)($episode['post_id']??0);$failed=(array)($episode['automation_review']['reasons']??array());echo '<tr><td><strong>'.esc_html($episode['title']??'').'</strong><br><small>'.esc_html($episode['duration']??'').'</small></td><td><a href="'.esc_url($episode['permalink']??'').'" target="_blank" rel="noopener">'.esc_html__('Official feed','astra-child').'</a>'.(!empty($episode['transcript'])?' · '.esc_html__('Transcript declared','astra-child'):'').'</td><td>'.esc_html(ucwords(str_replace('-',' ',(string)($episode['tier']??'editorial')))).'</td><td>'.esc_html(ucwords(str_replace('-',' ',(string)($episode['status']??'missing')))).($failed?'<br><small>'.esc_html(implode(' · ',array_map(function($reason){return str_replace('_',' ',$reason);},$failed))).'</small>':'').'</td><td>';if($post_id)echo '<a href="'.esc_url(get_edit_post_link($post_id,'url')).'">'.esc_html__('Review draft/article','astra-child').'</a>';else echo '<a href="'.esc_url(wp_nonce_url(add_query_arg(array('action'=>'mirrortalk_rss_ingestion_one','episode'=>$key),admin_url('admin-post.php')),'mirrortalk_rss_ingestion_one_'.$key)).'">'.esc_html__('Create review draft','astra-child').'</a>';echo '</td></tr>';}
    if(!$inventory)echo '<tr><td colspan="5">'.esc_html__('Run a scan to build the evidence inventory.','astra-child').'</td></tr>';echo '</tbody></table><p class="description">'.esc_html__('The table shows the latest 100 inventory records. The complete inventory remains available to the background pipeline.','astra-child').'</p></div>';
}
add_action('admin_menu', function(){ add_submenu_page('mirror-talk-intelligence',__('RSS Editorial Pipeline','astra-child'),__('RSS Editorial Pipeline','astra-child'),'edit_posts','mirror-talk-rss-ingestion','mirrortalk_rss_ingestion_admin_page'); }, 24);

/** Make exact ingested audio resolvable even when it has left the latest-12 cache. */
add_filter('mirrortalk_story_studio_episode', function($episode,$post_id){
    $audio=esc_url_raw((string)get_post_meta($post_id,'_mt_rss_audio_url',true)); if(!$audio)return $episode;
    $evidence=(array)get_post_meta($post_id,'_mt_rss_evidence',true);
    return array('title'=>get_the_title($post_id),'audio'=>$audio,'permalink'=>get_post_meta($post_id,'_mt_rss_source_url',true),'date'=>get_post_meta($post_id,'_mt_rss_published_gmt',true)?wp_date('M j',(int)get_post_meta($post_id,'_mt_rss_published_gmt',true)):'','duration'=>(string)($evidence['duration']??''));
},10,2);

