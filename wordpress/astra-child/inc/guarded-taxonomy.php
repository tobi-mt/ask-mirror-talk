<?php
/** Evidence-led category and tag governance for Composer v2. */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_TAXONOMY_VERSION', '1.0.0');

function mirrortalk_taxonomy_approved_category_ids() {
    $saved = get_option('mirrortalk_taxonomy_approved_categories', null);
    if (is_array($saved)) return array_values(array_unique(array_map('absint', $saved)));
    $approved = array();$map = function_exists('mirrortalk_topic_map') ? mirrortalk_topic_map() : array();
    foreach ($map as $slug=>$topic) {
        $term = get_term_by('slug', $slug, 'category');
        if (!$term) $term = get_term_by('name', $topic['label'], 'category');
        if ($term && !is_wp_error($term)) $approved[] = (int)$term->term_id;
    }
    return array_values(array_unique($approved));
}

function mirrortalk_taxonomy_source($post) {
    return strtolower(remove_accents(trim(preg_replace('/\s+/u',' ',wp_strip_all_tags(get_the_title($post).' '.$post->post_excerpt.' '.strip_shortcodes($post->post_content))))));
}

function mirrortalk_taxonomy_phrase_present($phrase,$source) {
    $phrase = strtolower(remove_accents(trim((string)$phrase)));
    return $phrase && preg_match('/(?<![\p{L}\p{N}])'.preg_quote($phrase,'/').'(?![\p{L}\p{N}])/u',$source);
}

function mirrortalk_taxonomy_clean_tag($value) {
    $value = trim(preg_replace('/\s+/u',' ',sanitize_text_field((string)$value)));
    $words = preg_split('/\s+/u',$value,-1,PREG_SPLIT_NO_EMPTY);
    $generic = array('podcast','episode','conversation','interview','mirror talk','personal growth','inspiration','life','success','motivation','reflection');
    if (!$value || strlen($value)<3 || strlen($value)>60 || count($words)>6 || in_array(strtolower($value),$generic,true) || preg_match('/https?:|@|\d{4,}/',$value)) return '';
    return $value;
}

function mirrortalk_taxonomy_distinct_tags($candidates,$limit=5) {
    $chosen=array();$slugs=array();
    foreach($candidates as$candidate){$candidate=mirrortalk_taxonomy_clean_tag($candidate);if(!$candidate)continue;$slug=sanitize_title($candidate);if(!$slug)continue;$duplicate=false;foreach($slugs as$prior){$max=max(strlen($slug),strlen($prior));$distance=levenshtein($slug,$prior);if($slug===$prior||strpos($slug,$prior)!==false||strpos($prior,$slug)!==false||($max&&$distance/$max<.22)){$duplicate=true;break;}}if($duplicate)continue;$chosen[]=$candidate;$slugs[]=$slug;if(count($chosen)>=$limit)break;}
    return $chosen;
}

function mirrortalk_taxonomy_candidates($post,$topic) {
    $source=mirrortalk_taxonomy_source($post);$candidates=array();
    $guest=trim((string)get_post_meta($post->ID,'_mt_guest_name',true));if($guest&&mirrortalk_taxonomy_phrase_present($guest,$source))$candidates[]=$guest;
    $expertise=preg_split('/\s*,\s*/',(string)get_post_meta($post->ID,'_mt_guest_expertise',true),-1,PREG_SPLIT_NO_EMPTY);foreach($expertise as$item)if(mirrortalk_taxonomy_phrase_present($item,$source))$candidates[]=$item;
    foreach(array('_mt_books_mentioned','_mt_named_concepts')as$key){$items=preg_split('/\r\n|\r|\n/',(string)get_post_meta($post->ID,$key,true),-1,PREG_SPLIT_NO_EMPTY);foreach($items as$item)if(mirrortalk_taxonomy_phrase_present($item,$source))$candidates[]=$item;}
    $existing=get_terms(array('taxonomy'=>'post_tag','hide_empty'=>false,'number'=>300));if(!is_wp_error($existing))foreach($existing as$term)if(mirrortalk_taxonomy_phrase_present($term->name,$source))$candidates[]=$term->name;
    $evidence=(array)get_post_meta($post->ID,'_mirrortalk_focus_keyword_evidence',true);$focus=trim((string)get_post_meta($post->ID,'_mirrortalk_focus_keyword',true));if($focus&&!empty($evidence['impressions'])&&(int)$evidence['impressions']>=5&&mirrortalk_taxonomy_phrase_present($focus,$source))$candidates[]=$focus;
    if(($topic['confidence']??'')==='high'&&!empty($topic['label'])&&mirrortalk_taxonomy_phrase_present($topic['label'],$source))$candidates[]=$topic['label'];
    return mirrortalk_taxonomy_distinct_tags($candidates,5);
}

function mirrortalk_taxonomy_verified_topic($post,$topic) {
    $evidence=(array)get_post_meta($post->ID,'_mirrortalk_focus_keyword_evidence',true);$focus=trim((string)get_post_meta($post->ID,'_mirrortalk_focus_keyword',true));
    if(!$focus||(int)($evidence['impressions']??0)<20||!mirrortalk_taxonomy_phrase_present($focus,mirrortalk_taxonomy_source($post)))return $topic;
    $matches=array();foreach((array)(function_exists('mirrortalk_topic_map')?mirrortalk_topic_map():array())as$slug=>$item)foreach((array)$item['keywords']as$keyword)if(mirrortalk_taxonomy_phrase_present($keyword,strtolower(remove_accents($focus)))){$matches[$slug]=$item;break;}
    if(count($matches)!==1)return $topic;$slug=array_key_first($matches);$item=$matches[$slug];return array('keyword'=>$focus,'hub'=>$slug,'label'=>$item['label'],'confidence'=>'high','score'=>max(20,(int)($topic['score']??0)),'evidence'=>array('verified-search-query'));
}

function mirrortalk_taxonomy_snapshot($post_id) {
    $history=(array)get_post_meta($post_id,'_mt_taxonomy_history',true);
    $history[]=array('time'=>time(),'user'=>get_current_user_id(),'categories'=>wp_get_post_categories($post_id),'tags'=>wp_get_post_tags($post_id,array('fields'=>'ids')),'owned_categories'=>(array)get_post_meta($post_id,'_mt_taxonomy_owned_categories',true),'owned_tags'=>(array)get_post_meta($post_id,'_mt_taxonomy_owned_tags',true),'exclusions'=>(array)get_post_meta($post_id,'_mt_taxonomy_exclusions',true));
    update_post_meta($post_id,'_mt_taxonomy_history',array_slice($history,-20));
}

function mirrortalk_guarded_taxonomy_run($post_id,$topic=array()) {
    $post=get_post($post_id);if(!$post||$post->post_type!=='post'||in_array($post->post_status,array('auto-draft','trash'),true))return array();
    if(!$topic)$topic=function_exists('mirrortalk_composer_v2_topic')?mirrortalk_composer_v2_topic($post):array();$topic=mirrortalk_taxonomy_verified_topic($post,$topic);
    $old_categories=array_values(array_filter(array_map('absint',(array)get_post_meta($post_id,'_mt_taxonomy_owned_categories',true))));$old_tags=array_values(array_filter(array_map('absint',(array)get_post_meta($post_id,'_mt_taxonomy_owned_tags',true))));
    $current_categories=wp_get_post_categories($post_id);$current_tags=wp_get_post_tags($post_id,array('fields'=>'ids'));$editor_categories=array_values(array_diff($current_categories,$old_categories));$editor_tags=array_values(array_diff($current_tags,$old_tags));
    $new_categories=array();
    if(($topic['confidence']??'')==='high'&&!empty($topic['hub']))foreach(mirrortalk_taxonomy_approved_category_ids() as$id){$term=get_term($id,'category');if($term&&!is_wp_error($term)&&($term->slug===$topic['hub']||strtolower($term->name)===strtolower((string)($topic['label']??'')))){$new_categories[]=$id;break;}}
    // Do not add an automatic category when an editor already selected a real one.
    $real_editor_categories=array_filter($editor_categories,function($id){$term=get_term($id,'category');return $term&&!is_wp_error($term)&&$term->slug!=='uncategorized';});if($real_editor_categories)$new_categories=array();elseif($new_categories)$editor_categories=array_values(array_filter($editor_categories,function($id){$term=get_term($id,'category');return !$term||is_wp_error($term)||$term->slug!=='uncategorized';}));
    $candidate_names=mirrortalk_taxonomy_candidates($post,$topic);$new_tags=array();foreach($candidate_names as$name){$term=term_exists($name,'post_tag');if(!$term)$term=wp_insert_term($name,'post_tag',array('slug'=>sanitize_title($name)));if(!is_wp_error($term))$new_tags[]=(int)(is_array($term)?$term['term_id']:$term);}
    $exclusions=(array)get_post_meta($post_id,'_mt_taxonomy_exclusions',true);$new_categories=array_values(array_filter($new_categories,function($id)use($exclusions){return !in_array('category:'.absint($id),$exclusions,true);}));$new_tags=array_values(array_filter(array_diff(array_unique($new_tags),$editor_tags),function($id)use($exclusions){return !in_array('post_tag:'.absint($id),$exclusions,true);}));$changed=array_values(array_unique(array_merge(array_diff($old_categories,$new_categories),array_diff($new_categories,$old_categories),array_diff($old_tags,$new_tags),array_diff($new_tags,$old_tags))));
    if($changed)mirrortalk_taxonomy_snapshot($post_id);
    wp_set_post_categories($post_id,array_values(array_unique(array_merge($editor_categories,$new_categories))),false);wp_set_post_tags($post_id,array_values(array_unique(array_merge($editor_tags,$new_tags))),false);
    update_post_meta($post_id,'_mt_taxonomy_owned_categories',$new_categories);update_post_meta($post_id,'_mt_taxonomy_owned_tags',$new_tags);
    $result=array('version'=>MIRRORTALK_TAXONOMY_VERSION,'time'=>time(),'category_ids'=>$new_categories,'tag_ids'=>$new_tags,'evidence'=>array('topic_confidence'=>$topic['confidence']??'rejected','topic_score'=>(int)($topic['score']??0),'verified_search'=>(bool)get_post_meta($post_id,'_mirrortalk_focus_keyword_evidence',true)));
    update_post_meta($post_id,'_mt_taxonomy_result',$result);
    if($changed&&function_exists('mirrortalk_composer_v2_log'))mirrortalk_composer_v2_log($post_id,'taxonomy_updated',array('categories'=>implode(',',$new_categories)?:'none','tags'=>implode(',',$new_tags)?:'none'));
    return $result;
}

function mirrortalk_taxonomy_term_name($id,$taxonomy){$term=get_term($id,$taxonomy);return $term&&!is_wp_error($term)?$term->name:'';}

add_action('mirrortalk_composer_v2_report_after_decisions',function($post){
    if($post->post_type!=='post')return;$result=(array)get_post_meta($post->ID,'_mt_taxonomy_result',true);$categories=(array)get_post_meta($post->ID,'_mt_taxonomy_owned_categories',true);$tags=(array)get_post_meta($post->ID,'_mt_taxonomy_owned_tags',true);
    echo '<section class="mt-taxonomy-report"><h3>'.esc_html__('Guarded taxonomy','astra-child').'</h3><p>'.esc_html__('Only Composer-owned terms appear here. Editor-owned categories and tags are preserved.','astra-child').'</p>';
    echo '<table class="widefat striped"><thead><tr><th>'.esc_html__('Term','astra-child').'</th><th>'.esc_html__('Evidence','astra-child').'</th><th>'.esc_html__('Control','astra-child').'</th></tr></thead><tbody>';
    foreach(array('category'=>$categories,'post_tag'=>$tags)as$taxonomy=>$ids)foreach($ids as$id){$name=mirrortalk_taxonomy_term_name($id,$taxonomy);if(!$name)continue;echo '<tr><td><strong>'.esc_html($name).'</strong><br><small>'.esc_html($taxonomy==='category'?__('Approved category','astra-child'):__('Evidence-backed tag','astra-child')).'</small></td><td>'.esc_html(sprintf(__('Topic confidence: %1$s · Search evidence: %2$s','astra-child'),$result['evidence']['topic_confidence']??'—',!empty($result['evidence']['verified_search'])?__('yes','astra-child'):__('no','astra-child'))).'</td><td><a class="button button-small" href="'.esc_url(wp_nonce_url(add_query_arg(array('action'=>'mirrortalk_taxonomy_remove','post_id'=>$post->ID,'taxonomy'=>$taxonomy,'term_id'=>$id),admin_url('admin-post.php')),'mirrortalk_taxonomy_remove_'.$post->ID)).'">'.esc_html__('Remove assignment','astra-child').'</a></td></tr>';}
    if(!$categories&&!$tags)echo '<tr><td colspan="3">'.esc_html__('No automatic taxonomy passed the evidence threshold.','astra-child').'</td></tr>';echo '</tbody></table>';
    $history=(array)get_post_meta($post->ID,'_mt_taxonomy_history',true);if($history)echo '<p><a href="'.esc_url(wp_nonce_url(add_query_arg(array('action'=>'mirrortalk_taxonomy_restore','post_id'=>$post->ID,'snapshot'=>count($history)-1),admin_url('admin-post.php')),'mirrortalk_taxonomy_restore_'.$post->ID)).'">'.esc_html__('Restore previous taxonomy state','astra-child').'</a></p>';echo '</section>';
});

add_action('admin_post_mirrortalk_taxonomy_remove',function(){
    $id=absint($_GET['post_id']??0);$term_id=absint($_GET['term_id']??0);$taxonomy=sanitize_key($_GET['taxonomy']??'');if(!$id||!$term_id||!in_array($taxonomy,array('category','post_tag'),true)||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot change this taxonomy.','astra-child'));check_admin_referer('mirrortalk_taxonomy_remove_'.$id);mirrortalk_taxonomy_snapshot($id);wp_remove_object_terms($id,$term_id,$taxonomy);$key=$taxonomy==='category'?'_mt_taxonomy_owned_categories':'_mt_taxonomy_owned_tags';$owned=array_values(array_diff(array_map('absint',(array)get_post_meta($id,$key,true)),array($term_id)));update_post_meta($id,$key,$owned);$exclusions=(array)get_post_meta($id,'_mt_taxonomy_exclusions',true);$exclusions[]=$taxonomy.':'.$term_id;update_post_meta($id,'_mt_taxonomy_exclusions',array_values(array_unique($exclusions)));mirrortalk_composer_v2_log($id,'taxonomy_assignment_removed',array('taxonomy'=>$taxonomy,'term'=>mirrortalk_taxonomy_term_name($term_id,$taxonomy)));wp_safe_redirect(wp_get_referer()?:get_edit_post_link($id,'url'));exit;
});

add_action('admin_post_mirrortalk_taxonomy_restore',function(){
    $id=absint($_GET['post_id']??0);$index=absint($_GET['snapshot']??-1);if(!$id||!current_user_can('edit_post',$id))wp_die(esc_html__('You cannot restore this taxonomy.','astra-child'));check_admin_referer('mirrortalk_taxonomy_restore_'.$id);$history=(array)get_post_meta($id,'_mt_taxonomy_history',true);if(isset($history[$index])){$snapshot=$history[$index];wp_set_post_categories($id,array_map('absint',(array)$snapshot['categories']),false);wp_set_post_tags($id,array_map('absint',(array)$snapshot['tags']),false);update_post_meta($id,'_mt_taxonomy_owned_categories',(array)$snapshot['owned_categories']);update_post_meta($id,'_mt_taxonomy_owned_tags',(array)$snapshot['owned_tags']);update_post_meta($id,'_mt_taxonomy_exclusions',(array)($snapshot['exclusions']??array()));mirrortalk_composer_v2_log($id,'taxonomy_restored',array('snapshot'=>$index));}wp_safe_redirect(wp_get_referer()?:get_edit_post_link($id,'url'));exit;
});

add_action('updated_post_meta',function($meta_id,$post_id,$key,$value){if($key!=='_mirrortalk_focus_keyword_evidence'||empty($value)||get_post_type($post_id)!=='post')return;$args=array((int)$post_id);if(!wp_next_scheduled('mirrortalk_taxonomy_recheck',$args))wp_schedule_single_event(time()+20,'mirrortalk_taxonomy_recheck',$args);},20,4);
add_action('mirrortalk_taxonomy_recheck',function($post_id){mirrortalk_guarded_taxonomy_run(absint($post_id));});

add_action('admin_menu',function(){add_submenu_page('mirror-talk-intelligence',__('Taxonomy governance','astra-child'),__('Taxonomy governance','astra-child'),'manage_mirrortalk_seo','mirror-talk-taxonomy','mirrortalk_taxonomy_settings_page');});
function mirrortalk_taxonomy_settings_page(){if(!current_user_can('manage_mirrortalk_seo'))return;if(isset($_POST['mt_taxonomy_nonce'])&&wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['mt_taxonomy_nonce'])),'mt_taxonomy_save')){update_option('mirrortalk_taxonomy_approved_categories',array_values(array_filter(array_map('absint',(array)($_POST['approved_categories']??array())))),false);echo '<div class="notice notice-success"><p>'.esc_html__('Approved category set saved.','astra-child').'</p></div>';}$approved=mirrortalk_taxonomy_approved_category_ids();$terms=get_terms(array('taxonomy'=>'category','hide_empty'=>false));echo '<div class="wrap"><h1>'.esc_html__('Taxonomy governance','astra-child').'</h1><p>'.esc_html__('Only checked, already-existing categories may be assigned automatically. The engine never creates categories.','astra-child').'</p><form method="post">';wp_nonce_field('mt_taxonomy_save','mt_taxonomy_nonce');if(!is_wp_error($terms))foreach($terms as$term)echo '<p><label><input type="checkbox" name="approved_categories[]" value="'.esc_attr($term->term_id).'" '.checked(in_array((int)$term->term_id,$approved,true),true,false).'> <strong>'.esc_html($term->name).'</strong> <code>'.esc_html($term->slug).'</code></label></p>';submit_button(__('Save approved categories','astra-child'));echo '</form></div>';}
