<?php
/**
 * Automatic Editorial Composer.
 *
 * Deterministic publishing work is automatic. Editorial assertions remain
 * review items. Stored body copy is never silently rewritten.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_COMPOSER_VERSION', '1.0.0');

function mirrortalk_composer_plain($post) {
    return trim(preg_replace('/\s+/u', ' ', wp_strip_all_tags(strip_shortcodes((string) $post->post_content))));
}

function mirrortalk_composer_strlen($value) {
    return function_exists('mb_strlen') ? mb_strlen((string) $value) : strlen((string) $value);
}

function mirrortalk_composer_detect_type($post) {
    $haystack = strtolower(get_the_title($post) . ' ' . $post->post_excerpt . ' ' . wp_trim_words(mirrortalk_composer_plain($post), 250, ''));
    if (preg_match('/\b(interview|q\s*&\s*a|conversation with|in conversation with)\b/i', $haystack)) return 'interview';
    if (preg_match('/\b(episode|podcast|listen now|show notes)\b/i', $haystack) || preg_match('/<(?:audio|iframe)[^>]+(?:spotify|apple|podbean|buzzsprout|audio)/i', $post->post_content)) return 'episode';
    if (preg_match('/\b(reflection|journal prompt|pause and reflect|reflective prompt)\b/i', $haystack)) return 'reflection';
    if (preg_match('/\b(resources?|reading list|recommended books?|toolkit|guide)\b/i', $haystack) || substr_count($post->post_content, '<a ') >= 8) return 'resource';
    return 'article';
}

function mirrortalk_composer_words($text) {
    $words = preg_split('/[^\p{L}\p{N}\']+/u', strtolower(remove_accents((string) $text)), -1, PREG_SPLIT_NO_EMPTY);
    $stop = array_flip(array('about','after','again','also','and','are','because','been','before','being','between','both','but','can','could','did','does','each','for','from','had','has','have','how','into','its','just','more','most','not','our','out','over','she','should','than','that','the','their','them','then','there','these','they','this','through','too','very','was','were','what','when','where','which','while','who','why','will','with','would','you','your','mirror','talk','podcast','episode'));
    return array_values(array_filter($words, function ($word) use ($stop) { return strlen($word) >= 4 && !isset($stop[$word]) && !is_numeric($word); }));
}

function mirrortalk_composer_provisional_topic($post) {
    $context = function_exists('mirrortalk_resolve_topic_context') ? mirrortalk_resolve_topic_context($post->ID) : array();
    if (!empty($context['slug']) && $context['slug'] !== 'reflection') return array('keyword' => strtolower($context['label']), 'hub' => $context['slug'], 'confidence' => 'high');
    $title_words = mirrortalk_composer_words(get_the_title($post));
    $body_words = mirrortalk_composer_words(wp_trim_words(mirrortalk_composer_plain($post), 500, ''));
    $scores = array(); foreach ($body_words as $word) $scores[$word] = ($scores[$word] ?? 0) + 1; foreach ($title_words as $word) $scores[$word] = ($scores[$word] ?? 0) + 5;
    arsort($scores); $keyword = ''; foreach ($scores as $word => $score) { $keyword = (string) $word; break; }
    return array('keyword' => $keyword, 'hub' => '', 'confidence' => $keyword && ($scores[$keyword] ?? 0) >= 5 ? 'medium' : 'low');
}

function mirrortalk_composer_search_title($post) {
    $title = trim(wp_strip_all_tags(get_the_title($post)));
    $suffix = ' | Mirror Talk';
    if (mirrortalk_composer_strlen($title . $suffix) <= 60) return $title . $suffix;
    $candidate = wp_trim_words($title, 10, '');
    while (mirrortalk_composer_strlen($candidate . $suffix) > 60 && substr_count($candidate, ' ')) $candidate = preg_replace('/\s+\S+$/u', '', $candidate);
    return trim($candidate) . $suffix;
}

function mirrortalk_composer_intro($post) {
    $excerpt = trim(wp_strip_all_tags((string) $post->post_excerpt));
    if ($excerpt) return wp_trim_words($excerpt, 42, '…');
    $plain = mirrortalk_composer_plain($post); if (!$plain) return '';
    $sentences = preg_split('/(?<=[.!?])\s+/u', $plain, -1, PREG_SPLIT_NO_EMPTY);
    return wp_trim_words(implode(' ', array_slice($sentences, 0, 2)), 42, '…');
}

function mirrortalk_composer_takeaways($post) {
    if (!preg_match_all('/<h[2-4][^>]*>(.*?)<\/h[2-4]>/is', $post->post_content, $matches)) return array();
    $items = array_values(array_filter(array_map(function ($heading) { return trim(sanitize_text_field(wp_strip_all_tags($heading))); }, $matches[1])));
    return array_slice($items, 0, 5);
}

function mirrortalk_composer_language_checks($post) {
    $plain = mirrortalk_composer_plain($post); $checks = array();
    if (preg_match('/\b([a-z]{3,})\s+\1\b/i', $plain, $match)) $checks[] = sprintf(__('Repeated word: “%s”.', 'astra-child'), $match[1]);
    if (preg_match('/\s+[,.!?;]/', $plain)) $checks[] = __('Review spacing before punctuation.', 'astra-child');
    if (preg_match('/[!?]{3,}/', $plain)) $checks[] = __('Review repeated punctuation.', 'astra-child');
    if(function_exists('pspell_new')){$dictionary=pspell_new('en');if($dictionary){$unknown=array();foreach(array_unique(mirrortalk_composer_words($plain))as$word)if(strlen($word)>=5&&!pspell_check($dictionary,$word)){$suggestions=pspell_suggest($dictionary,$word);if($suggestions)$unknown[]=$word.' → '.$suggestions[0];if(count($unknown)>=5)break;}if($unknown)$checks[]=__('Possible spelling checks: ','astra-child').implode(', ',$unknown);}}
    return $checks;
}

function mirrortalk_composer_internal_links($post_id, $topic) {
    $suggestions = array();
    if ($topic && function_exists('mirrortalk_learning_internal_link_suggestion')) {
        $candidate = mirrortalk_learning_internal_link_suggestion($post_id, $topic);
        if ($candidate) $suggestions[] = $candidate;
    }
    $related = function_exists('mirrortalk_related_posts') ? mirrortalk_related_posts($post_id, 3) : array();
    $source = (string) get_post_field('post_content', $post_id);
    foreach ($related as $item) { $url = get_permalink($item); if ($url && strpos($source, $url) === false) $suggestions[] = get_the_title($item) . ' — ' . $url; }
    return array_slice(array_values(array_unique($suggestions)), 0, 3);
}

function mirrortalk_composer_snapshot($post_id) {
    $keys = array('_mt_composer_type','_mt_composer_intro','_mt_composer_takeaways','_mt_composer_topic','_mt_composer_hub','_mt_composer_score','_mt_composer_review','_mt_composer_links','_mirrortalk_meta_title','_mirrortalk_meta_description','_mirrortalk_focus_keyword','_mirrortalk_focus_keyword_source');
    $snapshot = array('time'=>time(),'user'=>get_current_user_id(),'meta'=>array(),'categories'=>wp_get_post_categories($post_id),'tags'=>wp_get_post_tags($post_id,array('fields'=>'ids')));
    foreach($keys as $key)$snapshot['meta'][$key]=get_post_meta($post_id,$key,true);
    $history=(array)get_post_meta($post_id,'_mt_composer_history',true);$history[]=$snapshot;update_post_meta($post_id,'_mt_composer_history',array_slice($history,-20));
}

function mirrortalk_composer_assign_taxonomy($post, $topic) {
    if ($post->post_type !== 'post' || empty($topic['hub']) || !function_exists('mirrortalk_topic_map')) return;
    $map = mirrortalk_topic_map(); if (empty($map[$topic['hub']])) return;
    $categories = wp_get_post_categories($post->ID); $real = array_filter($categories, function ($id) { $term=get_term($id,'category'); return $term && !is_wp_error($term) && $term->slug !== 'uncategorized'; });
    if (!$real) { $term=term_exists($map[$topic['hub']]['label'],'category'); if (!$term) $term=wp_insert_term($map[$topic['hub']]['label'],'category',array('slug'=>$topic['hub'])); if (!is_wp_error($term)) wp_set_post_categories($post->ID,array((int)(is_array($term)?$term['term_id']:$term)),false); }
    $existing=get_terms(array('taxonomy'=>'post_tag','hide_empty'=>false)); if(is_wp_error($existing))return; $plain=strtolower(mirrortalk_composer_plain($post)); $matched=array(); foreach($existing as $term)if(strlen($term->name)>=4&&strpos($plain,strtolower($term->name))!==false)$matched[]=$term->term_id; if($matched)wp_set_post_tags($post->ID,array_slice($matched,0,5),true);
}

function mirrortalk_composer_run($post_id, $post = null, $force = false) {
    $post=$post?:get_post($post_id); if(!$post||!in_array($post->post_type,array('post','page'),true)||in_array($post->post_status,array('auto-draft','trash'),true))return array();
    $fingerprint=hash('sha256',$post->post_title.'|'.$post->post_excerpt.'|'.$post->post_content.'|'.get_post_thumbnail_id($post_id));
    if(!$force&&get_post_meta($post_id,'_mt_composer_fingerprint',true)===$fingerprint)return (array)get_post_meta($post_id,'_mt_composer_result',true);
    mirrortalk_composer_snapshot($post_id); if(function_exists('mirrortalk_seo_snapshot'))mirrortalk_seo_snapshot($post_id);
    $type=mirrortalk_composer_detect_type($post);$topic=mirrortalk_composer_provisional_topic($post);$intro=mirrortalk_composer_intro($post);$takeaways=mirrortalk_composer_takeaways($post);$plain=mirrortalk_composer_plain($post);$words=str_word_count($plain);$analysis=function_exists('mirrortalk_seo_editorial_analysis')?mirrortalk_seo_editorial_analysis($post):array('score'=>0,'issues'=>array());$review=array_merge((array)($analysis['issues']??array()),mirrortalk_composer_language_checks($post));
    $links=mirrortalk_composer_internal_links($post_id,$topic['keyword']);$score=(int)($analysis['score']??0);$result=array('version'=>MIRRORTALK_COMPOSER_VERSION,'time'=>time(),'type'=>$type,'topic'=>$topic,'words'=>$words,'reading_minutes'=>max(1,(int)ceil($words/220)),'score'=>$score,'review'=>$review,'links'=>$links);
    foreach(array('type'=>$type,'intro'=>$intro,'takeaways'=>$takeaways,'topic'=>$topic['keyword'],'hub'=>$topic['hub'],'score'=>$score,'review'=>$review,'links'=>$links)as$key=>$value)update_post_meta($post_id,'_mt_composer_'.$key,$value);
    if(!get_post_meta($post_id,'_mirrortalk_meta_title',true)){update_post_meta($post_id,'_mirrortalk_meta_title',mirrortalk_composer_search_title($post));}
    if(!get_post_meta($post_id,'_mirrortalk_meta_description',true)&&function_exists('mirrortalk_seo_description_candidate')){$description=mirrortalk_seo_description_candidate($post);if($description)update_post_meta($post_id,'_mirrortalk_meta_description',$description);}
    $evidence=get_post_meta($post_id,'_mirrortalk_focus_keyword_evidence',true);if($evidence)update_post_meta($post_id,'_mirrortalk_focus_keyword_source','verified-search-data');elseif(!get_post_meta($post_id,'_mirrortalk_focus_keyword',true)&&$topic['keyword']){update_post_meta($post_id,'_mirrortalk_focus_keyword',$topic['keyword']);update_post_meta($post_id,'_mirrortalk_focus_keyword_source','provisional-content');}
    if(has_post_thumbnail($post_id)&&function_exists('mirrortalk_repair_media_alt'))mirrortalk_repair_media_alt(get_post_thumbnail_id($post_id));
    mirrortalk_composer_assign_taxonomy($post,$topic);update_post_meta($post_id,'_mt_composer_result',$result);update_post_meta($post_id,'_mt_composer_fingerprint',$fingerprint);
    if($post->post_status==='publish'&&function_exists('mirrortalk_indexnow_queue_url'))mirrortalk_indexnow_queue_url(get_permalink($post_id));
    if(function_exists('mirrortalk_seo_snapshot'))mirrortalk_seo_snapshot($post_id);delete_transient('mirrortalk_command_centre');return $result;
}

add_action('save_post',function($post_id,$post){if(wp_is_post_revision($post_id)||wp_is_post_autosave($post_id)||defined('DOING_AUTOSAVE')&&DOING_AUTOSAVE||!current_user_can('edit_post',$post_id))return;mirrortalk_composer_run($post_id,$post);},70,2);

function mirrortalk_composer_backfill() {
    $ids=get_posts(array('post_type'=>array('post','page'),'post_status'=>'publish','numberposts'=>25,'fields'=>'ids','orderby'=>'ID','order'=>'ASC','meta_query'=>array(array('key'=>'_mt_composer_fingerprint','compare'=>'NOT EXISTS'))));
    foreach($ids as$id)mirrortalk_composer_run($id);
    if(count($ids)===25&&!wp_next_scheduled('mirrortalk_composer_backfill'))wp_schedule_single_event(time()+5*MINUTE_IN_SECONDS,'mirrortalk_composer_backfill');
    if(count($ids)<25)update_option('mirrortalk_composer_backfill_version',MIRRORTALK_COMPOSER_VERSION,false);
}
add_action('mirrortalk_composer_backfill','mirrortalk_composer_backfill');
add_action('init',function(){if(get_option('mirrortalk_composer_backfill_version')!==MIRRORTALK_COMPOSER_VERSION&&!wp_next_scheduled('mirrortalk_composer_backfill'))wp_schedule_single_event(time()+2*MINUTE_IN_SECONDS,'mirrortalk_composer_backfill');},125);
add_action('switch_theme',function(){wp_clear_scheduled_hook('mirrortalk_composer_backfill');});

// Some managed and staging hosts disable loopback WP-Cron. Compose the current
// public document on its first real visit and advance a small, locked batch
// whenever an editor enters wp-admin, so coverage does not depend on cron alone.
add_action('wp', function () {
    if (!is_singular(array('post', 'page')) || is_preview()) return;
    $post_id = get_queried_object_id();
    if ($post_id && !get_post_meta($post_id, '_mt_composer_fingerprint', true)) {
        mirrortalk_composer_run($post_id);
    }
}, 30);

add_action('admin_init', function () {
    if (!current_user_can('edit_posts') || get_option('mirrortalk_composer_backfill_version') === MIRRORTALK_COMPOSER_VERSION || get_transient('mirrortalk_composer_admin_backfill_lock')) return;
    set_transient('mirrortalk_composer_admin_backfill_lock', 1, MINUTE_IN_SECONDS);
    $ids = get_posts(array('post_type'=>array('post','page'),'post_status'=>'publish','numberposts'=>5,'fields'=>'ids','orderby'=>'ID','order'=>'ASC','meta_query'=>array(array('key'=>'_mt_composer_fingerprint','compare'=>'NOT EXISTS'))));
    foreach ($ids as $id) mirrortalk_composer_run($id);
    if (count($ids) < 5) update_option('mirrortalk_composer_backfill_version', MIRRORTALK_COMPOSER_VERSION, false);
}, 90);

function mirrortalk_composer_coverage() {
    $total=(int)(new WP_Query(array('post_type'=>array('post','page'),'post_status'=>'publish','posts_per_page'=>1,'fields'=>'ids')))->found_posts;$composed=(int)(new WP_Query(array('post_type'=>array('post','page'),'post_status'=>'publish','posts_per_page'=>1,'fields'=>'ids','meta_key'=>'_mt_composer_fingerprint')))->found_posts;
    return array('composed'=>$composed,'total'=>$total,'complete'=>get_option('mirrortalk_composer_backfill_version')===MIRRORTALK_COMPOSER_VERSION);
}

function mirrortalk_composer_render_enhancements($content) {
    if(is_admin()||!is_singular()||!in_the_loop()||!is_main_query()||strpos($content,'mirror-talk:preserve-format')!==false)return $content;$post_id=get_the_ID();$intro=trim((string)get_post_meta($post_id,'_mt_composer_intro',true));$takeaways=(array)get_post_meta($post_id,'_mt_composer_takeaways',true);$plain=mirrortalk_composer_plain(get_post($post_id));
    $starts_with_context=(bool)preg_match('/^\s*(?:<!--.*?-->\s*)*<(?:p|ul|ol|blockquote)\b/is',$content);if(!$starts_with_context&&$intro)$content='<p class="mt-composer-intro">'.esc_html($intro).'</p>'.$content;
    if(str_word_count($plain)>=900&&count($takeaways)>=3&&!preg_match('/(?:key takeaways|what you.ll learn|in this article)/i',$content)){$box='<aside class="mt-composer-takeaways" aria-labelledby="mt-composer-takeaways"><h2 id="mt-composer-takeaways">'.esc_html__('What you will explore','astra-child').'</h2><ul>';foreach($takeaways as$item)$box.='<li>'.esc_html($item).'</li>';$box.='</ul></aside>';$content=$box.$content;}
    return $content;
}
add_filter('the_content','mirrortalk_composer_render_enhancements',25);

function mirrortalk_composer_meta_box() { foreach(array('post','page')as$type)add_meta_box('mirrortalk-composer',__('Automatic Editorial Composer','astra-child'),'mirrortalk_composer_meta_box_html',$type,'side','high'); }
add_action('add_meta_boxes','mirrortalk_composer_meta_box');
function mirrortalk_composer_meta_box_html($post){$result=(array)get_post_meta($post->ID,'_mt_composer_result',true);$source=get_post_meta($post->ID,'_mirrortalk_focus_keyword_source',true)?:'verified search data or editorial';echo '<p><strong>'.esc_html(ucfirst($result['type']??'Not analysed')).'</strong> · '.esc_html(($result['reading_minutes']??'—').' min').' · '.esc_html(($result['score']??'—').'/100').'</p><p>'.esc_html__('Focus topic:','astra-child').' <strong>'.esc_html(get_post_meta($post->ID,'_mirrortalk_focus_keyword',true)?:'—').'</strong><br><small>'.esc_html($source).'</small></p>';$review=(array)($result['review']??array());if($review){echo '<strong>'.esc_html__('Editor review','astra-child').'</strong><ul>';foreach(array_slice($review,0,5)as$item)echo '<li>'.esc_html($item).'</li>';echo '</ul>';}$links=(array)($result['links']??array());if($links){echo '<strong>'.esc_html__('Internal-link opportunities','astra-child').'</strong><ul>';foreach($links as$item)echo '<li>'.esc_html($item).'</li>';echo '</ul>';}echo '<p><a class="button" href="'.esc_url(wp_nonce_url(admin_url('admin-post.php?action=mirrortalk_composer_run&post_id='.$post->ID),'mirrortalk_composer_run_'.$post->ID)).'">'.esc_html__('Recompose now','astra-child').'</a></p>';$history=(array)get_post_meta($post->ID,'_mt_composer_history',true);if($history){$index=count($history)-1;echo '<p><a href="'.esc_url(wp_nonce_url(admin_url('admin-post.php?action=mirrortalk_composer_rollback&post_id='.$post->ID.'&snapshot='.$index),'mirrortalk_composer_rollback_'.$post->ID)).'">'.esc_html__('Restore previous composition','astra-child').'</a></p>';}}

add_action('admin_post_mirrortalk_composer_run',function(){$id=absint($_GET['post_id']??0);if(!$id||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot compose this content.','astra-child'));check_admin_referer('mirrortalk_composer_run_'.$id);mirrortalk_composer_run($id,null,true);wp_safe_redirect(get_edit_post_link($id,'url'));exit;});
add_action('admin_post_mirrortalk_composer_rollback',function(){$id=absint($_GET['post_id']??0);$index=absint($_GET['snapshot']??-1);if(!$id||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot restore this composition.','astra-child'));check_admin_referer('mirrortalk_composer_rollback_'.$id);$history=(array)get_post_meta($id,'_mt_composer_history',true);if(isset($history[$index])){$snapshot=$history[$index];foreach((array)$snapshot['meta']as$key=>$value){if($value===''||$value===array())delete_post_meta($id,$key);else update_post_meta($id,$key,$value);}if(get_post_type($id)==='post'){wp_set_post_categories($id,(array)$snapshot['categories'],false);wp_set_post_tags($id,(array)$snapshot['tags'],false);}update_post_meta($id,'_mt_composer_fingerprint','');if(function_exists('mirrortalk_indexnow_queue_url'))mirrortalk_indexnow_queue_url(get_permalink($id));}wp_safe_redirect(get_edit_post_link($id,'url'));exit;});

add_filter('mirrortalk_schema_graph',function($schema){if(!is_singular())return $schema;$id=get_queried_object_id();$type=get_post_meta($id,'_mt_composer_type',true);$topic=get_post_meta($id,'_mt_composer_topic',true);$result=(array)get_post_meta($id,'_mt_composer_result',true);foreach($schema['@graph']as&$node)if(in_array('Article',(array)($node['@type']??array()),true)){if($type)$node['genre']=ucfirst($type);if($topic)$node['about'][]=array('@type'=>'Thing','name'=>$topic);$node['timeRequired']='PT'.max(1,(int)($result['reading_minutes']??1)).'M';}unset($node);return $schema;},40);

add_action('rest_api_init',function(){foreach(array('post','page')as$type)register_rest_field($type,'mirror_talk_composer',array('get_callback'=>function($object){return get_post_meta($object['id'],'_mt_composer_result',true);},'schema'=>array('type'=>'object','context'=>array('view','edit'))));});

// Verified Google/Bing evidence supersedes provisional content language.
add_action('updated_post_meta',function($meta_id,$post_id,$key,$value){if($key==='_mirrortalk_focus_keyword_evidence'&&!empty($value))update_post_meta($post_id,'_mirrortalk_focus_keyword_source','verified-search-data');},10,4);
