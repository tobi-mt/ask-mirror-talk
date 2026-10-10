<?php
/**
 * Automatic Editorial Composer 2 — reversible, visible, server-rendered.
 *
 * The canonical post_content is never rewritten. Composer decisions are stored
 * separately and applied to the public HTML, so readers and crawlers receive
 * the same enhanced document while an editor can disable any decision.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_COMPOSER_V2_VERSION', '2.1.1');

function mirrortalk_composer_v2_defaults() {
    return array(
        'intro' => array('enabled'=>true,'status'=>'automatic','label'=>__('Extractive introduction','astra-child')),
        'takeaways' => array('enabled'=>true,'status'=>'automatic','label'=>__('Key takeaways','astra-child')),
        'sections' => array('enabled'=>true,'status'=>'automatic','label'=>__('Accessible section structure','astra-child')),
        'internal_links' => array('enabled'=>true,'status'=>'automatic','label'=>__('Contextual internal links','astra-child')),
        'topic' => array('enabled'=>true,'status'=>'automatic','label'=>__('Content topic','astra-child')),
        'search_title' => array('enabled'=>true,'status'=>'automatic','label'=>__('Search title','astra-child')),
        'description' => array('enabled'=>true,'status'=>'automatic','label'=>__('Search description','astra-child')),
        'podcast_player' => array('enabled'=>true,'status'=>'automatic','label'=>__('Inline podcast moment','astra-child')),
        'youtube_player' => array('enabled'=>true,'status'=>'automatic','label'=>__('Inline YouTube moment','astra-child')),
        'follow_cta' => array('enabled'=>true,'status'=>'automatic','label'=>__('Podcast follow invitation','astra-child')),
        'newsletter_cta' => array('enabled'=>true,'status'=>'automatic','label'=>__('Newsletter invitation','astra-child')),
    );
}

function mirrortalk_composer_v2_decisions($post_id) {
    $saved=(array)get_post_meta($post_id,'_mt_composer_decisions',true);$defaults=mirrortalk_composer_v2_defaults();$decisions=array();
    foreach($defaults as$key=>$decision){$stored=is_array($saved[$key]??null)?$saved[$key]:array();$merged=array_merge($decision,$stored);$merged['enabled']=!empty($merged['enabled']);$merged['status']=sanitize_key(is_scalar($merged['status']??'')?(string)$merged['status']:'automatic')?:'automatic';$merged['label']=is_scalar($merged['label']??'')?(string)$merged['label']:(string)$decision['label'];$decisions[$key]=$merged;}
    return $decisions;
}

function mirrortalk_composer_v2_focus_phrase($title) {
    $title = strtolower(remove_accents(wp_strip_all_tags((string) $title)));
    $clauses = preg_split('/\s*(?::|\||—|–)\s*/u', $title, 2, PREG_SPLIT_NO_EMPTY);
    $phrase = trim((string) ($clauses[0] ?? $title));
    $phrase = preg_replace('/^(?:why|how|what|when|where|who)\s+/u', '', $phrase);
    $phrase = preg_replace('/^(?:from|the|a|an)\s+/u', '', $phrase);
    $phrase = preg_replace('/\s+(?:isn[\'’]?t|isnt|is|are|was|were|working|works|explained)(?:\s+.*)?$/u', '', $phrase);
    $phrase = preg_replace('/[^\p{L}\p{N}\s\-\']/u', ' ', $phrase);
    $words = preg_split('/\s+/u', trim($phrase), -1, PREG_SPLIT_NO_EMPTY);
    $words = array_slice($words, 0, 5);
    return trim(implode(' ', $words), " \t\n\r\0\x0B-' ");
}

function mirrortalk_composer_v2_topic($post) {
    $map=function_exists('mirrortalk_topic_map')?mirrortalk_topic_map():array();
    $title=strtolower(remove_accents(wp_strip_all_tags(get_the_title($post))));
    $excerpt=strtolower(remove_accents(wp_strip_all_tags((string)$post->post_excerpt)));
    $body=strtolower(remove_accents(wp_trim_words(mirrortalk_composer_plain($post),500,'')));
    $taxonomy='';foreach(get_the_category($post->ID)as$term)$taxonomy.=' '.strtolower(remove_accents($term->name.' '.$term->slug));foreach(wp_get_post_tags($post->ID)as$term)$taxonomy.=' '.strtolower(remove_accents($term->name.' '.$term->slug));
    $scores=array();$evidence=array();
    $generic=array_flip(array('love','success','work','change','meaning','strength','hope'));
    foreach($map as$slug=>$topic){$score=0;$hits=array();foreach((array)$topic['keywords']as$keyword){$needle=strtolower(remove_accents($keyword));$pattern='/\b'.preg_quote($needle,'/').'\w*\b/u';$title_hits=preg_match_all($pattern,$title);$excerpt_hits=preg_match_all($pattern,$excerpt);$body_hits=min(3,preg_match_all($pattern,$body));$tax_hits=preg_match_all($pattern,$taxonomy);$weight=isset($generic[$needle])?0.3:1;$points=(int)round(($title_hits*8+$excerpt_hits*4+$body_hits*2+$tax_hits*7)*$weight);if($points){$score+=$points;$hits[]=$keyword;}}$scores[$slug]=$score;$evidence[$slug]=$hits;}
    arsort($scores);$slugs=array_keys($scores);$winner=$slugs[0]??'';$first=$winner?(int)$scores[$winner]:0;$second=isset($slugs[1])?(int)$scores[$slugs[1]]:0;
    // Reject a weak or ambiguous topic instead of publishing a confident error.
    if(!$winner||$first<8||($second>0&&$first-$second<3))return array('keyword'=>'','hub'=>'','label'=>__('General reflection','astra-child'),'confidence'=>'rejected','score'=>$first,'evidence'=>array());
    $focus=mirrortalk_composer_v2_focus_phrase(get_the_title($post));if(!$focus)$focus=strtolower($map[$winner]['label']);
    return array('keyword'=>$focus,'hub'=>$winner,'label'=>$map[$winner]['label'],'confidence'=>$first>=16?'high':'medium','score'=>$first,'evidence'=>array_values(array_unique($evidence[$winner])));
}

function mirrortalk_composer_v2_search_title($post) {
    $title=trim(preg_replace('/\s+/u',' ',wp_strip_all_tags(get_the_title($post))));$suffix=' | Mirror Talk';$limit=60-mirrortalk_composer_strlen($suffix);
    if(mirrortalk_composer_strlen($title)<=$limit)return rtrim($title," \t\n\r\0\x0B,;:—–-").$suffix;
    $clauses=preg_split('/\s*:\s*/u',$title,2,PREG_SPLIT_NO_EMPTY);$first_clause=trim((string)($clauses[0]??''));
    if(count($clauses)>1&&mirrortalk_composer_strlen($first_clause)>=24&&mirrortalk_composer_strlen($first_clause)<=$limit)return rtrim($first_clause," \t\n\r\0\x0B,;:—–-").$suffix;
    $candidate=wp_html_excerpt($title,$limit,'');
    if(mirrortalk_composer_strlen($candidate)<mirrortalk_composer_strlen($title))$candidate=preg_replace('/\s+\S*$/u','',$candidate);
    $candidate=rtrim(trim($candidate)," \t\n\r\0\x0B,;:—–-");
    // Prefer a complete clause when truncation leaves a dangling connector.
    $candidate=preg_replace('/\s+\b(and|or|with|for|to|of|the|a|an|in|on|at|by)\b$/iu','',$candidate);
    if(mirrortalk_composer_strlen($candidate)<24){$candidate=wp_trim_words($title,8,'');$candidate=rtrim($candidate," \t\n\r\0\x0B,;:—–-");}
    return trim($candidate).$suffix;
}

function mirrortalk_composer_v2_sentences($post) {
    $content=(string)$post->post_content;
    $content=preg_replace('/<(blockquote|figure|pre|code|script|style|iframe|audio|video)\b[^>]*>.*?<\/\1>/is',' ',$content);
    $plain=trim(preg_replace('/\s+/u',' ',wp_strip_all_tags(strip_shortcodes($content))));
    $sentences=preg_split('/(?<=[.!?])\s+/u',$plain,-1,PREG_SPLIT_NO_EMPTY);$safe=array();
    foreach($sentences as$sentence){$sentence=trim($sentence);$words=str_word_count($sentence);if($words>=7&&$words<=40&&!preg_match('/^(subscribe|share this|like this|click here)/i',$sentence))$safe[]=$sentence;if(count($safe)>=8)break;}
    return $safe;
}

function mirrortalk_composer_v2_intro($post) {
    $excerpt=trim(preg_replace('/\s+/u',' ',wp_strip_all_tags((string)$post->post_excerpt)));
    if($excerpt&&str_word_count($excerpt)<=60)return $excerpt;
    $sentences=mirrortalk_composer_v2_sentences($post);
    if($sentences){$intro=$sentences[0];if(isset($sentences[1])&&str_word_count($intro.' '.$sentences[1])<=60)$intro.=' '.$sentences[1];return $intro;}
    $plain=mirrortalk_composer_plain($post);$fallback=preg_split('/(?<=[.!?])\s+/u',$plain,2,PREG_SPLIT_NO_EMPTY);return trim((string)($fallback[0]??$plain));
}

function mirrortalk_composer_v2_takeaways($post) {
    $items=mirrortalk_composer_takeaways($post);if(count($items)>=2)return array_slice($items,0,4);
    $sentences = mirrortalk_composer_v2_sentences($post);
    $items = array();
    foreach (array_slice($sentences, 1, 5) as $sentence) {
        $item = trim($sentence);
        if ($item && !in_array($item, $items, true)) $items[] = $item;
        if (count($items) >= 3) break;
    }
    if (!$items) {
        $paragraphs = preg_split('/\n\s*\n|<\/p>/i', (string) $post->post_content, -1, PREG_SPLIT_NO_EMPTY);
        foreach ($paragraphs as $paragraph) {
            $plain = trim(wp_strip_all_tags(strip_shortcodes($paragraph)));
            $item = wp_trim_words($plain, 28, '…');
            if (str_word_count($item) >= 5) $items[] = $item;
            if (count($items) >= 3) break;
        }
    }
    return $items;
}

function mirrortalk_composer_v2_links($post_id) {
    $links=array();$related=function_exists('mirrortalk_related_posts')?mirrortalk_related_posts($post_id,3):array();
    foreach($related as$item){$url=get_permalink($item);if($url)$links[]=array('post_id'=>(int)$item->ID,'title'=>wp_strip_all_tags(get_the_title($item)),'url'=>$url,'reason'=>__('A related conversation from the Mirror Talk archive.','astra-child'));}
    return $links;
}

function mirrortalk_composer_v2_snapshot($post_id) {
    $keys=array('_mt_composer_decisions','_mt_composer_v2_result','_mt_composer_version','_mt_composer_v2_fingerprint','_mt_composer_generated_title','_mt_composer_generated_description','_mirrortalk_meta_title','_mirrortalk_meta_description','_mirrortalk_focus_keyword','_mirrortalk_focus_keyword_source','_mt_story_studio');$snapshot=array('time'=>time(),'user'=>get_current_user_id(),'meta'=>array());foreach($keys as$key)$snapshot['meta'][$key]=get_post_meta($post_id,$key,true);$history=(array)get_post_meta($post_id,'_mt_composer_v2_history',true);$history[]=$snapshot;update_post_meta($post_id,'_mt_composer_v2_history',array_slice($history,-20));
}

function mirrortalk_composer_v2_log($post_id,$action,$details=array()) {
    $events=(array)get_post_meta($post_id,'_mt_composer_v2_events',true);
    $events[]=array('time'=>time(),'user'=>get_current_user_id(),'action'=>sanitize_key($action),'details'=>array_map('sanitize_text_field',(array)$details));
    update_post_meta($post_id,'_mt_composer_v2_events',array_slice($events,-100));
}

function mirrortalk_composer_v2_run($post_id,$force=false) {
    $post=get_post($post_id);if(!$post||!in_array($post->post_type,array('post','page'),true)||in_array($post->post_status,array('auto-draft','trash'),true))return array();
    $fingerprint=hash('sha256',MIRRORTALK_COMPOSER_V2_VERSION.'|'.$post->post_title.'|'.$post->post_excerpt.'|'.$post->post_content.'|'.get_post_thumbnail_id($post_id));if(!$force&&get_post_meta($post_id,'_mt_composer_v2_fingerprint',true)===$fingerprint)return (array)get_post_meta($post_id,'_mt_composer_v2_result',true);
    mirrortalk_composer_v2_snapshot($post_id);$topic=mirrortalk_composer_v2_topic($post);$intro=mirrortalk_composer_v2_intro($post);$takeaways=mirrortalk_composer_v2_takeaways($post);$links=mirrortalk_composer_v2_links($post_id);$plain=mirrortalk_composer_plain($post);$analysis=function_exists('mirrortalk_seo_editorial_analysis')?mirrortalk_seo_editorial_analysis($post):array('score'=>0,'issues'=>array());$decisions=mirrortalk_composer_v2_decisions($post_id);
    foreach(array_keys(mirrortalk_composer_v2_defaults())as$key){$decisions[$key]['status']=$decisions[$key]['status']==='disabled'?'disabled':'automatic';$decisions[$key]['updated_at']=time();}
    $generated_title=mirrortalk_composer_v2_search_title($post);$generated_description=function_exists('mirrortalk_seo_description_candidate')?mirrortalk_seo_description_candidate($post):$intro;$current_title=(string)get_post_meta($post_id,'_mirrortalk_meta_title',true);$current_description=(string)get_post_meta($post_id,'_mirrortalk_meta_description',true);$previous_generated_title=(string)get_post_meta($post_id,'_mt_composer_generated_title',true);$previous_generated_description=(string)get_post_meta($post_id,'_mt_composer_generated_description',true);$legacy_generated_title=function_exists('mirrortalk_composer_search_title')?mirrortalk_composer_search_title($post):'';$legacy_generated_description=function_exists('mirrortalk_seo_description_candidate')?mirrortalk_seo_description_candidate($post):'';
    $title_is_editorial=$current_title&&$current_title!==$previous_generated_title&&$current_title!==$legacy_generated_title;$description_is_editorial=$current_description&&$current_description!==$previous_generated_description&&$current_description!==$legacy_generated_description;$search_title=$title_is_editorial?$current_title:$generated_title;$description=$description_is_editorial?$current_description:$generated_description;if($title_is_editorial)$decisions['search_title']['status']='editorial';if($description_is_editorial)$decisions['description']['status']='editorial';
    $source_hash=hash('sha256',(string)$post->post_content);$source_words=str_word_count($plain);$changes=array('intro'=>!empty($intro),'takeaways'=>count($takeaways),'sections'=>substr_count(strtolower((string)$post->post_content),'<h2')<2,'internal_links'=>count($links),'search_title'=>$search_title,'description'=>$description,'topic'=>$topic['keyword']??'','podcast_player'=>true,'youtube_player'=>true,'follow_cta'=>true,'newsletter_cta'=>true);
    $result=array('version'=>MIRRORTALK_COMPOSER_V2_VERSION,'time'=>time(),'type'=>mirrortalk_composer_detect_type($post),'topic'=>$topic,'words'=>$source_words,'reading_minutes'=>max(1,(int)ceil($source_words/220)),'score'=>(int)($analysis['score']??0),'review'=>array_values(array_unique(array_merge((array)($analysis['issues']??array()),mirrortalk_composer_language_checks($post)))),'intro'=>$intro,'takeaways'=>$takeaways,'links'=>$links,'search_title'=>$search_title,'description'=>$description,'source_hash'=>$source_hash,'source_words'=>$source_words,'source_preserved'=>true,'url_locked'=>get_permalink($post_id),'changes'=>$changes);
    update_post_meta($post_id,'_mt_composer_decisions',$decisions);update_post_meta($post_id,'_mt_composer_v2_result',$result);update_post_meta($post_id,'_mt_composer_version',MIRRORTALK_COMPOSER_V2_VERSION);update_post_meta($post_id,'_mt_composer_v2_fingerprint',$fingerprint);
    foreach(array('type'=>$result['type'],'intro'=>$intro,'takeaways'=>$takeaways,'topic'=>$topic['keyword'],'hub'=>$topic['hub'],'score'=>$result['score'],'review'=>$result['review'],'links'=>array_map(function($link){return $link['title'].' — '.$link['url'];},$links))as$key=>$value)update_post_meta($post_id,'_mt_composer_'.$key,$value);
    if(!empty($decisions['search_title']['enabled'])&&!$title_is_editorial){update_post_meta($post_id,'_mirrortalk_meta_title',$generated_title);update_post_meta($post_id,'_mt_composer_generated_title',$generated_title);}if(!empty($decisions['description']['enabled'])&&$generated_description&&!$description_is_editorial){update_post_meta($post_id,'_mirrortalk_meta_description',$generated_description);update_post_meta($post_id,'_mt_composer_generated_description',$generated_description);}
    $verified=get_post_meta($post_id,'_mirrortalk_focus_keyword_evidence',true);if($verified)update_post_meta($post_id,'_mirrortalk_focus_keyword_source','verified-search-data');elseif(!empty($decisions['topic']['enabled'])&&$topic['confidence']!=='rejected'){update_post_meta($post_id,'_mirrortalk_focus_keyword',$topic['keyword']);update_post_meta($post_id,'_mirrortalk_focus_keyword_source','provisional-content-v2');}else{delete_post_meta($post_id,'_mirrortalk_focus_keyword');update_post_meta($post_id,'_mirrortalk_focus_keyword_source','topic-rejected');}
    if(function_exists('mirrortalk_guarded_taxonomy_run'))mirrortalk_guarded_taxonomy_run($post_id,$topic);
    mirrortalk_composer_v2_log($post_id,'composed',array('version'=>MIRRORTALK_COMPOSER_V2_VERSION,'source_hash'=>$source_hash,'url'=>get_permalink($post_id),'decisions'=>count(array_filter($changes))));
    if($post->post_status==='publish'&&function_exists('mirrortalk_indexnow_queue_url'))mirrortalk_indexnow_queue_url(get_permalink($post_id));return $result;
}

function mirrortalk_composer_v2_queue_saved_content($post_id,$post) {
    if(wp_is_post_revision($post_id)||wp_is_post_autosave($post_id)||(defined('DOING_AUTOSAVE')&&DOING_AUTOSAVE)||!$post||!in_array($post->post_type,array('post','page'),true)||in_array($post->post_status,array('auto-draft','trash'),true)||!current_user_can('edit_post',$post_id))return;
    update_post_meta($post_id,'_mt_composer_v2_pending',time());
    $args=array((int)$post_id);
    if(!wp_next_scheduled('mirrortalk_compose_saved_content',$args))wp_schedule_single_event(time()+10,'mirrortalk_compose_saved_content',$args);
}
add_action('save_post','mirrortalk_composer_v2_queue_saved_content',75,2);

function mirrortalk_composer_v2_process_saved_content($post_id) {
    $post_id=absint($post_id);if(!$post_id)return;
    delete_post_meta($post_id,'_mt_composer_v2_pending');
    mirrortalk_composer_v2_run($post_id,true);
}
add_action('mirrortalk_compose_saved_content','mirrortalk_composer_v2_process_saved_content',10,1);

function mirrortalk_composer_v2_backfill() {
    $ids=get_posts(array('post_type'=>array('post','page'),'post_status'=>'publish','numberposts'=>10,'fields'=>'ids','orderby'=>'ID','order'=>'ASC','meta_query'=>array('relation'=>'OR',array('key'=>'_mt_composer_version','compare'=>'NOT EXISTS'),array('key'=>'_mt_composer_version','value'=>MIRRORTALK_COMPOSER_V2_VERSION,'compare'=>'!='))));foreach($ids as$id)mirrortalk_composer_v2_run($id,true);if(count($ids)===10&&!wp_next_scheduled('mirrortalk_composer_v2_backfill'))wp_schedule_single_event(time()+5*MINUTE_IN_SECONDS,'mirrortalk_composer_v2_backfill');if(count($ids)<10)update_option('mirrortalk_composer_v2_backfill_version',MIRRORTALK_COMPOSER_V2_VERSION,false);
}
add_action('mirrortalk_composer_v2_backfill','mirrortalk_composer_v2_backfill');add_action('init',function(){if(get_option('mirrortalk_composer_v2_backfill_version')!==MIRRORTALK_COMPOSER_V2_VERSION&&!wp_next_scheduled('mirrortalk_composer_v2_backfill'))wp_schedule_single_event(time()+MINUTE_IN_SECONDS,'mirrortalk_composer_v2_backfill');},130);

function mirrortalk_composer_v2_should_render($post_id) {
    if(is_admin()||!is_singular(array('post','page'))||!in_the_loop()||!is_main_query()||is_front_page()||is_page(array('ask-mirror-talk','contact','join-us','insights'))||strpos((string)get_post_field('post_content',$post_id),'mirror-talk:preserve-format')!==false)return false;return true;
}

function mirrortalk_composer_v2_add_sections($content,$topic_label) {
    if(substr_count(strtolower($content),'<h2')>=2||substr_count(strtolower($content),'<p')<6||preg_match('/(?:elementor|wp:columns|transcript)/i',$content))return $content;
    $headings=array(__('Understanding the conversation','astra-child'),$topic_label?sprintf(__('%s in practice','astra-child'),$topic_label):__('Ideas to carry forward','astra-child'));$total=substr_count(strtolower($content),'</p>');$targets=array(max(2,(int)floor($total/3)),max(4,(int)floor($total*2/3)));$index=0;$inserted=0;
    return preg_replace_callback('/<\/p>/i',function($match)use(&$index,&$inserted,$targets,$headings){$index++;$extra='';if(isset($targets[$inserted])&&$index===$targets[$inserted]){$extra='<h2 class="mt-composer-section">'.esc_html($headings[$inserted]).'</h2>';$inserted++;}return $match[0].$extra;},$content);
}

function mirrortalk_composer_v2_render($content) {
    $post_id=get_the_ID();if(!mirrortalk_composer_v2_should_render($post_id))return $content;$result=(array)get_post_meta($post_id,'_mt_composer_v2_result',true);if(!$result)return $content;$decisions=mirrortalk_composer_v2_decisions($post_id);
    $bridge='';$marker='<aside class="mt-reflection-bridge"';$position=strpos($content,$marker);if($position!==false){$bridge=substr($content,$position);$content=substr($content,0,$position);}
    if(!empty($decisions['sections']['enabled']))$content=mirrortalk_composer_v2_add_sections($content,$result['topic']['label']??'');
    $lead='';if(!empty($decisions['intro']['enabled'])&&!empty($result['intro'])){$lead='<section class="mt-composer-lead" aria-label="'.esc_attr__('Editorial introduction','astra-child').'"><div class="mt-composer-lead__context"><span>'.esc_html(ucfirst($result['type']??'article')).'</span>';if(!empty($result['topic']['label'])&&($result['topic']['confidence']??'')!=='rejected')$lead.='<span>'.esc_html($result['topic']['label']).'</span>';$lead.='<span>'.esc_html(sprintf(__('%d min read','astra-child'),(int)($result['reading_minutes']??1))).'</span></div><p>'.esc_html($result['intro']).'</p></section>';}
    $takeaways='';if(!empty($decisions['takeaways']['enabled'])&&!empty($result['takeaways'])){$takeaways='<aside class="mt-composer-takeaways" aria-labelledby="mt-composer-takeaways-'.$post_id.'"><p class="mt-section-kicker">'.esc_html__('At a glance','astra-child').'</p><h2 id="mt-composer-takeaways-'.$post_id.'">'.esc_html__('What this conversation explores','astra-child').'</h2><ul>';foreach(array_slice((array)$result['takeaways'],0,4)as$item)$takeaways.='<li>'.esc_html($item).'</li>';$takeaways.='</ul></aside>';}
    $links='';if(!empty($decisions['internal_links']['enabled'])&&!empty($result['links'])){$links='<aside class="mt-composer-links" aria-labelledby="mt-composer-links-'.$post_id.'"><p class="mt-section-kicker">'.esc_html__('Continue exploring','astra-child').'</p><h2 id="mt-composer-links-'.$post_id.'">'.esc_html__('Related conversations for your next step','astra-child').'</h2><div>';foreach((array)$result['links']as$link)$links.='<a href="'.esc_url($link['url']).'"><strong>'.esc_html($link['title']).'</strong><span>'.esc_html__('Read the conversation','astra-child').' →</span></a>';$links.='</div></aside>';}
    return '<div class="mt-composer-document" data-composer-version="'.esc_attr(MIRRORTALK_COMPOSER_V2_VERSION).'">'.$lead.$takeaways.$content.$links.'</div>'.$bridge;
}
remove_filter('the_content','mirrortalk_composer_render_enhancements',25);add_filter('the_content','mirrortalk_composer_v2_render',25);

function mirrortalk_composer_v2_action_url($action,$post_id,$extra=array()) {return wp_nonce_url(add_query_arg(array_merge(array('action'=>$action,'post_id'=>$post_id),$extra),admin_url('admin-post.php')),$action.'_'.$post_id);}

function mirrortalk_composer_v2_report($post) {
    $result=(array)get_post_meta($post->ID,'_mt_composer_v2_result',true);$topic_result=is_array($result['topic']??null)?$result['topic']:array('keyword'=>is_scalar($result['topic']??'')?(string)$result['topic']:'','label'=>'','confidence'=>'legacy');$decisions=mirrortalk_composer_v2_decisions($post->ID);$current_hash=hash('sha256',(string)$post->post_content);$source_preserved=!empty($result['source_hash'])&&hash_equals((string)$result['source_hash'],$current_hash);echo '<div class="mt-composer-admin"><p><strong>'.esc_html(ucfirst((string)($result['type']??__('Not analysed','astra-child')))).'</strong> · '.esc_html(($result['reading_minutes']??'—').' min').' · '.esc_html(($result['score']??'—').'/100').' · <strong>'.esc_html($source_preserved?__('Source preserved','astra-child'):__('Source changed since composition','astra-child')).'</strong></p><p><span class="dashicons dashicons-lock" aria-hidden="true"></span> '.esc_html__('Protected URL:','astra-child').' <code>'.esc_html($result['url_locked']??get_permalink($post->ID)).'</code></p><table class="widefat striped"><thead><tr><th>'.esc_html__('Decision','astra-child').'</th><th>'.esc_html__('State','astra-child').'</th><th>'.esc_html__('Result','astra-child').'</th><th>'.esc_html__('Control','astra-child').'</th></tr></thead><tbody>';
    foreach($decisions as$key=>$decision){$value='';if($key==='topic')$value=(string)($topic_result['label']?:__('Rejected as weak or ambiguous','astra-child')).' · '.(string)($topic_result['confidence']??'');elseif($key==='search_title')$value=(string)($result['search_title']??'');elseif($key==='description')$value=(string)($result['description']??'');elseif($key==='intro')$value=(string)($result['intro']??'');elseif($key==='takeaways')$value=sprintf(__('%d extractive points','astra-child'),count((array)($result['takeaways']??array())));elseif($key==='internal_links')$value=sprintf(__('%d contextual links','astra-child'),count((array)($result['links']??array())));elseif($key==='podcast_player')$value=__('Selected RSS episode, falling back to the latest available episode.','astra-child');elseif($key==='youtube_player')$value=__('Selected YouTube URL, falling back to the latest channel video.','astra-child');elseif($key==='follow_cta')$value=__('Apple Podcasts, Spotify and YouTube follow choices.','astra-child');elseif($key==='newsletter_cta')$value=__('Direct newsletter modal after the reader receives value.','astra-child');else$value=__('Neutral headings are inserted only when structure is missing.','astra-child');$enabled=!empty($decision['enabled']);$label=(string)($decision['label']??$key);$status=(string)($decision['status']??'automatic');echo '<tr><td><strong>'.esc_html($label).'</strong></td><td>'.esc_html($enabled?ucfirst($status):__('Disabled','astra-child')).'</td><td>'.esc_html(wp_trim_words($value,24,'…')).'</td><td><a class="button button-small" href="'.esc_url(mirrortalk_composer_v2_action_url('mirrortalk_composer_v2_toggle',$post->ID,array('decision'=>$key))).'">'.esc_html($enabled?__('Revert','astra-child'):__('Enable','astra-child')).'</a></td></tr>';}
    echo '</tbody></table><p><a class="button button-primary" href="'.esc_url(mirrortalk_composer_v2_action_url('mirrortalk_composer_v2_approve',$post->ID)).'">'.esc_html__('Approve current decisions','astra-child').'</a> <a class="button" href="'.esc_url(mirrortalk_composer_v2_action_url('mirrortalk_composer_v2_run',$post->ID)).'">'.esc_html__('Recompose','astra-child').'</a> <a class="button" target="_blank" href="'.esc_url(add_query_arg('mt_composer_preview','1',get_permalink($post->ID))).'">'.esc_html__('Preview composed page','astra-child').'</a></p>';do_action('mirrortalk_composer_v2_report_after_decisions',$post);
    echo '<details><summary><strong>'.esc_html__('Correct generated decisions','astra-child').'</strong></summary><form method="post" action="'.esc_url(admin_url('admin-post.php')).'" class="mt-composer-corrections"><input type="hidden" name="action" value="mirrortalk_composer_v2_correct"><input type="hidden" name="post_id" value="'.esc_attr($post->ID).'">';wp_nonce_field('mirrortalk_composer_v2_correct_'.$post->ID);echo '<p><label><strong>'.esc_html__('Search title','astra-child').'</strong><br><input class="widefat" name="search_title" maxlength="70" value="'.esc_attr($result['search_title']??'').'"></label></p><p><label><strong>'.esc_html__('Meta description','astra-child').'</strong><br><textarea class="widefat" name="description" rows="3" maxlength="320">'.esc_textarea($result['description']??'').'</textarea></label></p><p><label><strong>'.esc_html__('Visible introduction','astra-child').'</strong><br><textarea class="widefat" name="intro" rows="4">'.esc_textarea($result['intro']??'').'</textarea></label></p><p><label><strong>'.esc_html__('Takeaways — one complete point per line','astra-child').'</strong><br><textarea class="widefat" name="takeaways" rows="5">'.esc_textarea(implode("\n",(array)($result['takeaways']??array()))).'</textarea></label></p><p><label><strong>'.esc_html__('Focus phrase','astra-child').'</strong><br><input class="regular-text" name="focus_keyword" value="'.esc_attr($topic_result['keyword']??'').'"></label></p><p><button class="button button-primary" type="submit">'.esc_html__('Save corrections and record change','astra-child').'</button></p></form></details>';
    $history=(array)get_post_meta($post->ID,'_mt_composer_v2_history',true);if($history)echo '<p><a href="'.esc_url(mirrortalk_composer_v2_action_url('mirrortalk_composer_v2_restore',$post->ID,array('snapshot'=>count($history)-1))).'">'.esc_html__('Restore previous Composer state','astra-child').'</a></p>';
    if(!empty($result['review'])){echo '<h3>'.esc_html__('Editorial review','astra-child').'</h3><ul>';foreach(array_slice($result['review'],0,8)as$item)echo '<li>'.esc_html($item).'</li>';echo '</ul>';}$events=array_reverse((array)get_post_meta($post->ID,'_mt_composer_v2_events',true));if($events){echo '<h3>'.esc_html__('Change ledger','astra-child').'</h3><table class="widefat striped"><thead><tr><th>'.esc_html__('When','astra-child').'</th><th>'.esc_html__('Action','astra-child').'</th><th>'.esc_html__('Details','astra-child').'</th></tr></thead><tbody>';foreach(array_slice($events,0,20)as$event)echo '<tr><td>'.esc_html(wp_date('Y-m-d H:i',(int)($event['time']??0))).'</td><td>'.esc_html(ucwords(str_replace('_',' ',(string)($event['action']??'')))).'</td><td>'.esc_html(implode(' · ',array_map(function($key,$value){return $key.': '.$value;},array_keys((array)($event['details']??array())),array_values((array)($event['details']??array()))))).'</td></tr>';echo '</tbody></table>';}echo '</div>';
}

add_action('add_meta_boxes',function(){foreach(array('post','page')as$type){remove_meta_box('mirrortalk-composer',$type,'side');add_meta_box('mirrortalk-composer-v2',__('Mirror Talk Editorial Composer','astra-child'),function($post){mirrortalk_composer_v2_report($post);},$type,'normal','high');}},30);
add_action('admin_menu',function(){add_submenu_page('mirror-talk-intelligence',__('Editorial Composer','astra-child'),__('Editorial Composer','astra-child'),'manage_mirrortalk_seo','mirror-talk-composer','mirrortalk_composer_v2_admin_page');add_management_page(__('Mirror Talk Editorial Composer','astra-child'),__('Mirror Talk Composer','astra-child'),'edit_posts','mirror-talk-composer-editor','mirrortalk_composer_v2_admin_page');});
function mirrortalk_composer_v2_admin_page(){if(!current_user_can('edit_posts'))return;$post_id=absint($_GET['post_id']??0);echo '<div class="wrap"><h1>'.esc_html__('Mirror Talk Editorial Composer','astra-child').'</h1>';if($post_id&&($post=get_post($post_id))){echo '<h2>'.esc_html(get_the_title($post)).'</h2>';mirrortalk_composer_v2_report($post);}else{$paged=max(1,absint($_GET['paged']??1));$type=in_array(($_GET['content_type']??''),array('post','page'),true)?sanitize_key($_GET['content_type']):array('post','page');$query=new WP_Query(array('post_type'=>$type,'post_status'=>'publish','posts_per_page'=>50,'paged'=>$paged,'orderby'=>'modified','order'=>'DESC','meta_query'=>array(array('key'=>'_mt_composer_version','compare'=>'EXISTS'))));$done=(int)(new WP_Query(array('post_type'=>array('post','page'),'post_status'=>'publish','posts_per_page'=>1,'fields'=>'ids','meta_key'=>'_mt_composer_version','meta_value'=>MIRRORTALK_COMPOSER_V2_VERSION)))->found_posts;$total=(int)(new WP_Query(array('post_type'=>array('post','page'),'post_status'=>'publish','posts_per_page'=>1,'fields'=>'ids')))->found_posts;echo '<p>'.esc_html(sprintf(__('%1$d of %2$d published posts and pages currently use Composer %3$s.','astra-child'),$done,$total,MIRRORTALK_COMPOSER_V2_VERSION)).'</p><form method="get"><input type="hidden" name="page" value="mirror-talk-composer"><label>'.esc_html__('Content type','astra-child').' <select name="content_type"><option value="">'.esc_html__('Posts and pages','astra-child').'</option><option value="post">'.esc_html__('Posts','astra-child').'</option><option value="page">'.esc_html__('Pages','astra-child').'</option></select></label> <button class="button">'.esc_html__('Filter','astra-child').'</button></form><table class="widefat striped"><thead><tr><th>'.esc_html__('Content','astra-child').'</th><th>'.esc_html__('Work completed','astra-child').'</th><th>'.esc_html__('Topic','astra-child').'</th><th>'.esc_html__('Score','astra-child').'</th><th>'.esc_html__('Protected URL','astra-child').'</th><th>'.esc_html__('Report','astra-child').'</th></tr></thead><tbody>';foreach($query->posts as$post){$result=(array)get_post_meta($post->ID,'_mt_composer_v2_result',true);$completed=count(array_filter((array)($result['changes']??array())));echo '<tr><td><strong>'.esc_html(get_the_title($post)).'</strong><br><small>'.esc_html(get_post_type_object($post->post_type)->labels->singular_name).' · '.esc_html(get_the_modified_date('', $post)).'</small></td><td>'.esc_html(sprintf(__('%d governed decisions','astra-child'),$completed)).'</td><td>'.esc_html($result['topic']['label']??'—').'</td><td>'.esc_html(isset($result['score'])?$result['score'].'/100':'—').'</td><td><span class="dashicons dashicons-lock" aria-hidden="true"></span> '.esc_html(wp_parse_url(get_permalink($post),PHP_URL_PATH)).'</td><td><a href="'.esc_url(add_query_arg(array('page'=>'mirror-talk-composer','post_id'=>$post->ID),admin_url('admin.php'))).'">'.esc_html__('Review, correct or restore','astra-child').'</a></td></tr>';}echo '</tbody></table>';echo '<div class="tablenav"><div class="tablenav-pages">'.wp_kses_post(paginate_links(array('base'=>add_query_arg('paged','%#%'),'format'=>'','current'=>$paged,'total'=>max(1,(int)$query->max_num_pages)))).'</div></div>';}echo '</div>';}

function mirrortalk_composer_v2_row_action($actions,$post){if(current_user_can('edit_post',$post->ID))$actions['mirrortalk_composer']='<a href="'.esc_url(add_query_arg(array('page'=>'mirror-talk-composer-editor','post_id'=>$post->ID),admin_url('tools.php'))).'">'.esc_html__('Composer decisions','astra-child').'</a>';return $actions;}
add_filter('post_row_actions','mirrortalk_composer_v2_row_action',20,2);add_filter('page_row_actions','mirrortalk_composer_v2_row_action',20,2);

add_action('admin_post_mirrortalk_composer_v2_correct',function(){
    $id=absint($_POST['post_id']??0);if(!$id||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot correct this composition.','astra-child'));check_admin_referer('mirrortalk_composer_v2_correct_'.$id);
    mirrortalk_composer_v2_snapshot($id);$result=(array)get_post_meta($id,'_mt_composer_v2_result',true);$decisions=mirrortalk_composer_v2_decisions($id);$changed=array();
    $fields=array('search_title','description','intro','focus_keyword');foreach($fields as$field){$value=sanitize_text_field(wp_unslash($_POST[$field]??''));if($field==='search_title')$value=rtrim($value," \t\n\r\0\x0B,;:—–-");if($field==='focus_keyword'){if($value!==($result['topic']['keyword']??''))$changed[]='topic';$result['topic']['keyword']=$value;$decisions['topic']['status']='editorial';update_post_meta($id,'_mirrortalk_focus_keyword',$value);update_post_meta($id,'_mirrortalk_focus_keyword_source','editorial');continue;}if($value!==($result[$field]??''))$changed[]=$field;$result[$field]=$value;$decisions[$field]['status']='editorial';if($field==='search_title')update_post_meta($id,'_mirrortalk_meta_title',$value);if($field==='description')update_post_meta($id,'_mirrortalk_meta_description',$value);}
    $takeaways=array_values(array_filter(array_map('sanitize_text_field',preg_split('/\r\n|\r|\n/',wp_unslash($_POST['takeaways']??'')))));if($takeaways!==(array)($result['takeaways']??array()))$changed[]='takeaways';$result['takeaways']=array_slice($takeaways,0,6);$decisions['takeaways']['status']='editorial';$result['time']=time();$result['changes']['editorial_corrections']=count($changed);update_post_meta($id,'_mt_composer_v2_result',$result);update_post_meta($id,'_mt_composer_decisions',$decisions);mirrortalk_composer_v2_log($id,'editorial_correction',array('fields'=>implode(', ',array_unique($changed))?:'reviewed','url'=>get_permalink($id)));if(function_exists('mirrortalk_indexnow_queue_url'))mirrortalk_indexnow_queue_url(get_permalink($id));wp_safe_redirect(wp_get_referer()?:get_edit_post_link($id,'url'));exit;
});

add_action('admin_post_mirrortalk_composer_v2_toggle',function(){$id=absint($_GET['post_id']??0);$key=sanitize_key($_GET['decision']??'');if(!$id||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot change this composition.','astra-child'));check_admin_referer('mirrortalk_composer_v2_toggle_'.$id);$decisions=mirrortalk_composer_v2_decisions($id);if(isset($decisions[$key])){$was_editorial=($decisions[$key]['status']??'')==='editorial';$decisions[$key]['enabled']=empty($decisions[$key]['enabled']);$decisions[$key]['status']=$decisions[$key]['enabled']?'automatic':'disabled';update_post_meta($id,'_mt_composer_decisions',$decisions);if($key==='search_title'&&!$decisions[$key]['enabled']&&!$was_editorial)delete_post_meta($id,'_mirrortalk_meta_title');if($key==='description'&&!$decisions[$key]['enabled']&&!$was_editorial)delete_post_meta($id,'_mirrortalk_meta_description');if($key==='topic'&&!$decisions[$key]['enabled']){delete_post_meta($id,'_mirrortalk_focus_keyword');update_post_meta($id,'_mirrortalk_focus_keyword_source','disabled');}mirrortalk_composer_v2_log($id,$decisions[$key]['enabled']?'decision_enabled':'decision_reverted',array('decision'=>$key,'url'=>get_permalink($id)));if($decisions[$key]['enabled']&&in_array($key,array('search_title','description','topic'),true))mirrortalk_composer_v2_run($id,true);}wp_safe_redirect(wp_get_referer()?:get_edit_post_link($id,'url'));exit;});
add_action('admin_post_mirrortalk_composer_v2_approve',function(){$id=absint($_GET['post_id']??0);if(!$id||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot approve this composition.','astra-child'));check_admin_referer('mirrortalk_composer_v2_approve_'.$id);$decisions=mirrortalk_composer_v2_decisions($id);foreach($decisions as&$decision)if(!empty($decision['enabled']))$decision['status']='approved';unset($decision);update_post_meta($id,'_mt_composer_decisions',$decisions);mirrortalk_composer_v2_log($id,'approved',array('url'=>get_permalink($id)));wp_safe_redirect(wp_get_referer()?:get_edit_post_link($id,'url'));exit;});
add_action('admin_post_mirrortalk_composer_v2_run',function(){$id=absint($_GET['post_id']??0);if(!$id||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot compose this content.','astra-child'));check_admin_referer('mirrortalk_composer_v2_run_'.$id);mirrortalk_composer_v2_run($id,true);wp_safe_redirect(wp_get_referer()?:get_edit_post_link($id,'url'));exit;});
add_action('admin_post_mirrortalk_composer_v2_restore',function(){$id=absint($_GET['post_id']??0);$index=absint($_GET['snapshot']??-1);if(!$id||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot restore this composition.','astra-child'));check_admin_referer('mirrortalk_composer_v2_restore_'.$id);$history=(array)get_post_meta($id,'_mt_composer_v2_history',true);if(isset($history[$index])){foreach((array)$history[$index]['meta']as$key=>$value){if($value===''||$value===array())delete_post_meta($id,$key);else update_post_meta($id,$key,$value);}mirrortalk_composer_v2_log($id,'restored',array('snapshot'=>$index,'url'=>get_permalink($id)));}wp_safe_redirect(wp_get_referer()?:get_edit_post_link($id,'url'));exit;});

add_filter('mirrortalk_schema_graph',function($schema){if(!is_singular()||empty($schema['@graph']))return $schema;foreach($schema['@graph']as&$node){if(!in_array('Article',(array)($node['@type']??array()),true))continue;$seen=array();$unique=array();foreach((array)($node['about']??array())as$item){$name=strtolower(trim((string)($item['name']??'')));if(!$name||isset($seen[$name]))continue;$seen[$name]=true;$unique[]=$item;}$node['about']=$unique;}unset($node);return $schema;},60);
add_action('rest_api_init',function(){foreach(array('post','page')as$type)register_rest_field($type,'mirror_talk_composer_v2',array('get_callback'=>function($object){return get_post_meta($object['id'],'_mt_composer_v2_result',true)?:null;},'schema'=>array('type'=>array('object','null'),'context'=>array('view','edit'))));});
