<?php
/**
 * Mirror Talk Elementor Migration Centre.
 *
 * Converts fully supported Elementor documents into semantic WordPress content.
 * Every mutation is preceded by a complete, checksum-protected snapshot.
 */
if (!defined('ABSPATH')) exit;

const MIRRORTALK_ELEMENTOR_MIGRATION_VERSION = '1.1.0';

function mirrortalk_elementor_supported_widgets() {
    return array('heading','text-editor','image','video','button','shortcode','divider','spacer','icon-list','social-icons','image-box','icon-box','testimonial','accordion','toggle','tabs','image-carousel','gallery','menu-anchor','counter','progress','star-rating','google_maps','form','wpforms','contact-form-7','mailchimp','subscribe','slides','media-carousel','testimonial-carousel','loop-carousel','posts','html');
}

function mirrortalk_elementor_inventory($limit = 50, $offset = 0, $include_migrated = true) {
    $meta_query = array('relation'=>'OR',
        array('key'=>'_elementor_edit_mode','value'=>'builder'),
        array('key'=>'_elementor_data','value'=>array('','[]'),'compare'=>'NOT IN'),
    );
    if ($include_migrated) $meta_query[] = array('key'=>'_mirrortalk_elementor_migrated','compare'=>'EXISTS');
    $query = new WP_Query(array(
        'post_type' => array('post','page'), 'post_status' => array('publish','future','draft','pending','private'),
        'posts_per_page' => min(100, max(1, absint($limit))), 'offset' => max(0, absint($offset)), 'orderby' => 'ID', 'order' => 'ASC',
        'meta_query' => $meta_query, 'no_found_rows' => true, 'update_post_term_cache' => false,
    ));
    $items = array();
    foreach ($query->posts as $post) {
        $data = (string) get_post_meta($post->ID, '_elementor_data', true);
        if (($data === '' || $data === '[]') && !get_post_meta($post->ID,'_mirrortalk_elementor_migrated',true)) continue;
        $items[] = mirrortalk_elementor_analyse($post, $data);
    }
    return $items;
}

/** Fast aggregate counts that never load or decode Elementor JSON. */
function mirrortalk_elementor_migration_counts($force = false) {
    global $wpdb;
    $cached = get_transient('mirrortalk_elementor_migration_counts');
    if (!$force && is_array($cached)) return $cached;
    if (!$force) {
        mirrortalk_runtime_queue('mirrortalk_elementor_count_scan');
        $last = get_option('mirrortalk_elementor_migration_counts_last', array());
        return is_array($last) && isset($last['total']) ? array_merge($last, array('pending_scan'=>true)) : array('pending'=>0,'migrated'=>0,'total'=>0,'pending_scan'=>true);
    }
    $eligible = "p.post_type IN ('post','page') AND p.post_status IN ('publish','future','draft','pending','private')";
    $pending = (int) $wpdb->get_var(
        "SELECT COUNT(DISTINCT p.ID) FROM {$wpdb->posts} p
         INNER JOIN {$wpdb->postmeta} source ON source.post_id=p.ID AND source.meta_key IN ('_elementor_edit_mode','_elementor_data')
         LEFT JOIN {$wpdb->postmeta} migrated ON migrated.post_id=p.ID AND migrated.meta_key='_mirrortalk_elementor_migrated'
         WHERE {$eligible} AND migrated.post_id IS NULL
           AND source.meta_key IN ('_elementor_edit_mode','_elementor_data')"
    );
    $migrated = (int) $wpdb->get_var(
        "SELECT COUNT(DISTINCT p.ID) FROM {$wpdb->posts} p
         INNER JOIN {$wpdb->postmeta} migrated ON migrated.post_id=p.ID AND migrated.meta_key='_mirrortalk_elementor_migrated'
         WHERE {$eligible}"
    );
    $result = array('pending'=>$pending, 'migrated'=>$migrated, 'total'=>$pending+$migrated, 'pending_scan'=>false);
    set_transient('mirrortalk_elementor_migration_counts', $result, HOUR_IN_SECONDS);
    update_option('mirrortalk_elementor_migration_counts_last', $result, false);
    return $result;
}
add_action('mirrortalk_elementor_count_scan',function(){mirrortalk_runtime_run('elementor_count_scan',function(){return mirrortalk_elementor_migration_counts(true);},10*MINUTE_IN_SECONDS);});

/** Dashboard rows intentionally never load the potentially huge JSON payload. */
function mirrortalk_elementor_dashboard_items($limit = 12, $offset = 0) {
    global $wpdb;
    $limit=min(25,max(1,absint($limit)));$offset=max(0,absint($offset));
    // EXISTS can use post_id/meta_key indexes and avoids WP_Query's expensive
    // OR-meta JOIN/GROUP BY construction on large postmeta tables.
    $ids=$wpdb->get_col($wpdb->prepare(
        "SELECT p.ID FROM {$wpdb->posts} p
         WHERE p.post_type IN ('post','page')
           AND p.post_status IN ('publish','future','draft','pending','private')
           AND EXISTS (SELECT 1 FROM {$wpdb->postmeta} pm WHERE pm.post_id=p.ID AND pm.meta_key IN ('_elementor_edit_mode','_elementor_data','_mirrortalk_elementor_migrated'))
         ORDER BY p.ID ASC LIMIT %d OFFSET %d",
        $limit,$offset
    ));
    $items=array();foreach((array)$ids as$id){$id=absint($id);$state=get_post_meta($id,'_mirrortalk_elementor_migrated',true);$verification=(array)get_post_meta($id,'_mirrortalk_elementor_verification',true);$migrated=is_array($state)&&!empty($state);$items[]=array('id'=>$id,'title'=>get_the_title($id),'type'=>get_post_type($id),'url'=>get_permalink($id),'widgets'=>array(),'unsupported'=>array(),'migrated'=>$migrated,'migration_state'=>$migrated?$state:array(),'verification'=>$verification,'readiness'=>$migrated?'migrated':'pending');}return$items;
}

function mirrortalk_elementor_walk($elements, &$widgets, &$unsupported) {
    foreach ((array) $elements as $element) {
        if (!is_array($element)) continue;
        $type = sanitize_key((string) ($element['widgetType'] ?? ''));
        if ($type) {
            $widgets[$type] = ($widgets[$type] ?? 0) + 1;
            if (!in_array($type, mirrortalk_elementor_supported_widgets(), true)) $unsupported[$type] = ($unsupported[$type] ?? 0) + 1;
        }
        if (!empty($element['elements'])) mirrortalk_elementor_walk($element['elements'], $widgets, $unsupported);
    }
}

function mirrortalk_elementor_analyse($post, $raw_data = null) {
    $post = is_object($post) ? $post : get_post(absint($post));
    if (!$post) return array();
    $raw = $raw_data === null ? (string) get_post_meta($post->ID, '_elementor_data', true) : (string) $raw_data;
    $data = json_decode($raw, true); $widgets = array(); $unsupported = array();
    if (is_array($data)) mirrortalk_elementor_walk($data, $widgets, $unsupported);
    $template = (string) get_post_meta($post->ID, '_wp_page_template', true);
    $has_form = (bool) array_intersect(array_keys($widgets), array('form','wpforms','shortcode','contact-form-7'));
    $migration_state = get_post_meta($post->ID, '_mirrortalk_elementor_migrated', true);$is_migrated=(bool)$migration_state;$verification=(array)get_post_meta($post->ID,'_mirrortalk_elementor_verification',true);
    $valid = is_array($data) && !empty($data);
    return array(
        'id'=>(int)$post->ID, 'title'=>get_the_title($post), 'type'=>$post->post_type, 'status'=>$post->post_status,
        'url'=>get_permalink($post), 'widgets'=>$widgets, 'unsupported'=>$unsupported, 'template'=>$template,
        'has_form'=>$has_form, 'migrated'=>$is_migrated, 'valid'=>$valid,'migration_state'=>is_array($migration_state)?$migration_state:array(),'verification'=>$verification,
        'readiness'=>$is_migrated ? 'migrated' : (!$valid || $unsupported ? 'adaptable' : 'ready'),
    );
}

function mirrortalk_elementor_setting($settings, $key, $default = '') {
    $value = $settings[$key] ?? $default;
    return is_scalar($value) ? (string) $value : $default;
}

function mirrortalk_elementor_youtube_id($url) {
    return function_exists('mirrortalk_youtube_video_id') ? mirrortalk_youtube_video_id($url) : '';
}

function mirrortalk_elementor_convert_widget($type, $settings, &$report) {
    $type = sanitize_key((string) $type); $settings = is_array($settings) ? $settings : array();
    if ($type === 'heading') {
        $text = trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings, 'title')));
        if ($text === '') return '';
        $tag = strtolower(mirrortalk_elementor_setting($settings, 'header_size', 'h2'));
        $level = preg_match('/^h([2-6])$/', $tag, $m) ? (int)$m[1] : 2;
        $report[] = 'heading'; return '<!-- wp:heading {"level":'.$level.'} --><h'.$level.'>'.esc_html($text).'</h'.$level.'><!-- /wp:heading -->';
    }
    if ($type === 'text-editor') {
        $html = wp_kses_post(mirrortalk_elementor_setting($settings, 'editor'));
        if (trim(wp_strip_all_tags($html)) === '') return '';
        $report[] = 'text'; return '<!-- wp:html -->'.$html.'<!-- /wp:html -->';
    }
    if ($type === 'image') {
        $image = is_array($settings['image'] ?? null) ? $settings['image'] : array();
        $id = absint($image['id'] ?? 0); $url = $id ? wp_get_attachment_image_url($id, 'large') : esc_url_raw($image['url'] ?? '');
        if (!$url) return '';
        $alt = $id ? (string) get_post_meta($id, '_wp_attachment_image_alt', true) : '';
        $caption = trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings, 'caption')));
        $report[] = 'image';
        return '<!-- wp:image {"sizeSlug":"large"} --><figure class="wp-block-image size-large"><img src="'.esc_url($url).'" alt="'.esc_attr($alt).'">'.($caption ? '<figcaption>'.esc_html($caption).'</figcaption>' : '').'</figure><!-- /wp:image -->';
    }
    if ($type === 'video') {
        $id = mirrortalk_elementor_youtube_id(mirrortalk_elementor_setting($settings, 'youtube_url'));
        if (!$id) return '';
        $report[] = 'privacy_video'; return '<!-- wp:shortcode -->[mirror_talk_video id="'.esc_attr($id).'"]<!-- /wp:shortcode -->';
    }
    if ($type === 'button') {
        $label = trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings, 'text', __('Continue', 'astra-child'))));
        $link = is_array($settings['link'] ?? null) ? esc_url_raw($settings['link']['url'] ?? '') : '';
        if (!$link) return '';
        $report[] = 'button'; return '<!-- wp:buttons --><div class="wp-block-buttons"><!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="'.esc_url($link).'">'.esc_html($label).'</a></div><!-- /wp:button --></div><!-- /wp:buttons -->';
    }
    if ($type === 'shortcode') {
        $shortcode = trim(mirrortalk_elementor_setting($settings, 'shortcode'));
        if ($shortcode === '') return '';
        $report[] = 'shortcode'; return '<!-- wp:shortcode -->'.wp_kses_post($shortcode).'<!-- /wp:shortcode -->';
    }
    if ($type === 'divider') { $report[] = 'divider'; return '<!-- wp:separator --><hr class="wp-block-separator has-alpha-channel-opacity"><!-- /wp:separator -->'; }
    if ($type === 'spacer') return '';
    if ($type === 'icon-list') {
        $items = array(); foreach ((array)($settings['icon_list'] ?? array()) as $item) { $text=trim(wp_strip_all_tags((string)($item['text']??''))); if($text)$items[]='<li>'.esc_html($text).'</li>'; }
        if (!$items) return ''; $report[]='list'; return '<!-- wp:list --><ul>'.implode('', $items).'</ul><!-- /wp:list -->';
    }
    if ($type === 'social-icons') {
        $links=array(); foreach((array)($settings['social_icon_list']??array())as$item){$link=is_array($item['link']??null)?esc_url_raw($item['link']['url']??''):'';$label=trim(wp_strip_all_tags((string)($item['social_icon']['value']??__('Social profile','astra-child'))));if($link)$links[]='<a href="'.esc_url($link).'" rel="noopener">'.esc_html($label?:__('Social profile','astra-child')).'</a>';}
        if(!$links)return'';$report[]='social_links';return'<!-- wp:paragraph --><p class="mt-migrated-social-links">'.implode(' · ',$links).'</p><!-- /wp:paragraph -->';
    }
    if (in_array($type,array('form','wpforms','contact-form-7'),true)) return mirrortalk_elementor_form_adapter($type,$settings,$report);
    if (in_array($type,array('mailchimp','subscribe'),true)) {$report[]='owned_newsletter_form';return'<!-- wp:shortcode -->[mirror_talk_newsletter]<!-- /wp:shortcode -->';}
    if ($type === 'image-box' || $type === 'icon-box') {
        $title=trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings,'title_text')));$description=wp_kses_post(mirrortalk_elementor_setting($settings,'description_text'));$parts=array();
        if($type==='image-box'&&!empty($settings['image'])&&is_array($settings['image']))$parts[]=mirrortalk_elementor_convert_widget('image',array('image'=>$settings['image']),$report);
        if($title)$parts[]='<!-- wp:heading {"level":3} --><h3>'.esc_html($title).'</h3><!-- /wp:heading -->';if(trim(wp_strip_all_tags($description)))$parts[]='<!-- wp:html -->'.$description.'<!-- /wp:html -->';
        if(!$parts)return'';$report[]=$type;return'<!-- wp:group {"className":"mt-migrated-feature"} --><div class="wp-block-group mt-migrated-feature">'.implode("\n",$parts).'</div><!-- /wp:group -->';
    }
    if ($type === 'testimonial') {
        $content=trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings,'testimonial_content')));$name=trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings,'testimonial_name')));$job=trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings,'testimonial_job')));if(!$content)return'';
        $report[]='testimonial';return'<!-- wp:quote --><blockquote class="wp-block-quote"><p>'.esc_html($content).'</p>'.($name?'<cite>'.esc_html($name.($job?' — '.$job:'')).'</cite>':'').'</blockquote><!-- /wp:quote -->';
    }
    if (in_array($type,array('accordion','toggle'),true)) {
        $items=array();foreach((array)($settings['tabs']??array())as$item){$title=trim(wp_strip_all_tags((string)($item['tab_title']??'')));$content=wp_kses_post((string)($item['tab_content']??''));if($title||trim(wp_strip_all_tags($content)))$items[]='<details class="mt-migrated-disclosure"><summary>'.esc_html($title?:__('Read more','astra-child')).'</summary><div>'.$content.'</div></details>';}
        if(!$items)return'';$report[]='disclosures';return'<!-- wp:html -->'.implode("\n",$items).'<!-- /wp:html -->';
    }
    if ($type === 'tabs') {
        $parts=array();foreach((array)($settings['tabs']??array())as$item){$title=trim(wp_strip_all_tags((string)($item['tab_title']??'')));$content=wp_kses_post((string)($item['tab_content']??''));if($title)$parts[]='<h3>'.esc_html($title).'</h3>';if(trim(wp_strip_all_tags($content)))$parts[]=$content;}
        if(!$parts)return'';$report[]='tabs_to_sections';return'<!-- wp:html --><section class="mt-migrated-tabs">'.implode("\n",$parts).'</section><!-- /wp:html -->';
    }
    if ($type === 'image-carousel' || $type === 'gallery' || $type === 'media-carousel') {
        $source=(array)($settings['carousel']??$settings['gallery']??array());$images=array();foreach($source as$image){if(!is_array($image))continue;$id=absint($image['id']??0);$url=$id?wp_get_attachment_image_url($id,'large'):esc_url_raw($image['url']??'');if(!$url)continue;$alt=$id?(string)get_post_meta($id,'_wp_attachment_image_alt',true):'';$images[]='<figure class="wp-block-image"><img src="'.esc_url($url).'" alt="'.esc_attr($alt).'"></figure>';}
        if(!$images)return'';$report[]='owned_slider';return'<!-- wp:html --><section class="mt-owned-slider" data-mt-owned-slider aria-label="'.esc_attr__('Image highlights','astra-child').'"><div class="mt-owned-slider__track">'.implode('',$images).'</div></section><!-- /wp:html -->';
    }
    if ($type === 'slides') {
        $slides=array();foreach((array)($settings['slides']??array())as$item){$heading=trim(wp_strip_all_tags((string)($item['heading']??'')));$description=wp_kses_post((string)($item['description']??''));$button=trim(wp_strip_all_tags((string)($item['button_text']??'')));$url=is_array($item['link']??null)?esc_url_raw($item['link']['url']??''):'';$bg=is_array($item['background_image']??null)?esc_url_raw($item['background_image']['url']??''):'';$slides[]='<article class="mt-owned-slider__slide"'.($bg?' style="--mt-slide-image:url('.esc_url($bg).')"':'').'>'.($heading?'<h3>'.esc_html($heading).'</h3>':'').$description.($url?'<a class="mt-button" href="'.esc_url($url).'">'.esc_html($button?:__('Explore','astra-child')).'</a>':'').'</article>';}
        if(!$slides)return'';$report[]='owned_slider';return'<!-- wp:html --><section class="mt-owned-slider" data-mt-owned-slider aria-roledescription="carousel" aria-label="'.esc_attr__('Featured reflections','astra-child').'"><div class="mt-owned-slider__track">'.implode('',$slides).'</div><button class="mt-owned-slider__pause" type="button" data-mt-slider-pause>'.esc_html__('Pause','astra-child').'</button></section><!-- /wp:html -->';
    }
    if ($type === 'testimonial-carousel') {
        $slides=array();foreach((array)($settings['slides']??array())as$item){$content=trim(wp_strip_all_tags((string)($item['content']??$item['testimonial_content']??'')));$name=trim(wp_strip_all_tags((string)($item['name']??$item['testimonial_name']??'')));if($content)$slides[]='<blockquote class="mt-owned-slider__slide"><p>'.esc_html($content).'</p>'.($name?'<cite>'.esc_html($name).'</cite>':'').'</blockquote>';}
        if(!$slides)return'';$report[]='owned_slider';return'<!-- wp:html --><section class="mt-owned-slider" data-mt-owned-slider aria-label="'.esc_attr__('Community reflections','astra-child').'"><div class="mt-owned-slider__track">'.implode('',$slides).'</div><button class="mt-owned-slider__pause" type="button" data-mt-slider-pause>'.esc_html__('Pause','astra-child').'</button></section><!-- /wp:html -->';
    }
    if (in_array($type,array('posts','loop-carousel'),true)) {$report[]='dynamic_archive_link';return'<!-- wp:group {"className":"mt-migrated-feature"} --><div class="wp-block-group mt-migrated-feature"><h3>'.esc_html__('Continue exploring Mirror Talk','astra-child').'</h3><p>'.esc_html__('Discover the latest conversations, reflections and practical wisdom from the archive.','astra-child').'</p><p><a class="mt-button" href="'.esc_url(home_url('/blog/')).'">'.esc_html__('Explore recent conversations','astra-child').'</a></p></div><!-- /wp:group -->';}
    if ($type === 'html') return mirrortalk_elementor_convert_custom_html(mirrortalk_elementor_setting($settings,'html'),$report);
    if ($type === 'menu-anchor') {$id=sanitize_title(mirrortalk_elementor_setting($settings,'anchor'));if(!$id)return'';$report[]='anchor';return'<!-- wp:html --><span id="'.esc_attr($id).'" class="mt-migrated-anchor" aria-hidden="true"></span><!-- /wp:html -->';}
    if (in_array($type,array('counter','progress','star-rating'),true)) {
        $title=trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings,'title')));$value=$type==='counter'?mirrortalk_elementor_setting($settings,'ending_number'):($type==='progress'?mirrortalk_elementor_setting($settings,'percent'):mirrortalk_elementor_setting($settings,'rating'));
        if($title===''&&$value==='')return'';$report[]='metric';return'<!-- wp:paragraph --><p class="mt-migrated-metric"><strong>'.esc_html($value).'</strong>'.($title?' '.esc_html($title):'').'</p><!-- /wp:paragraph -->';
    }
    if ($type === 'google_maps') {$address=trim(wp_strip_all_tags(mirrortalk_elementor_setting($settings,'address')));if(!$address)return'';$report[]='map_link';return'<!-- wp:paragraph --><p><a href="'.esc_url('https://www.google.com/maps/search/?api=1&query='.rawurlencode($address)).'">'.esc_html(sprintf(__('View %s on the map','astra-child'),$address)).'</a></p><!-- /wp:paragraph -->';}
    return mirrortalk_elementor_generic_fallback($type,$settings,$report);
}

function mirrortalk_elementor_form_adapter($type,$settings,&$report){
    $signal=strtolower(wp_json_encode($settings));
    if(preg_match('/paypal|stripe|payment|donat(?:e|ion)|checkout|credit.?card/',$signal)){$report[]='payment_form_to_verified_destination';return'<!-- wp:group {"className":"mt-migrated-feature"} --><div class="wp-block-group mt-migrated-feature"><h3>'.esc_html__('Support Mirror Talk safely','astra-child').'</h3><p>'.esc_html__('Financial details are never collected by this website. Continue through the verified Mirror Talk Patreon page.','astra-child').'</p><p><a class="mt-button" href="https://www.patreon.com/MirrorTalk" target="_blank" rel="noopener">'.esc_html__('Visit Mirror Talk on Patreon','astra-child').'</a></p></div><!-- /wp:group -->';}
    if(preg_match('/newsletter|subscribe|mailing.?list|weekly.?note|email.?updates/',$signal)){$report[]='owned_newsletter_form';return'<!-- wp:shortcode -->[mirror_talk_newsletter]<!-- /wp:shortcode -->';}
    $report[]=preg_match('/guest|partnership|collaborat|press|speaker/',$signal)?'owned_contact_form_routed':'owned_contact_form';return'<!-- wp:shortcode -->[mirror_talk_contact]<!-- /wp:shortcode -->';
}

function mirrortalk_elementor_convert_custom_html($html,&$report){
    $html=(string)$html;if(trim($html)==='')return'';
    if(preg_match('~(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})~i',$html,$m)){$report[]='html_to_privacy_video';return'<!-- wp:shortcode -->[mirror_talk_video id="'.esc_attr($m[1]).'"]<!-- /wp:shortcode -->';}
    if(preg_match('/<(?:form|input|textarea|select)\b/i',$html)){$newsletter=(bool)preg_match('/newsletter|subscribe|mailchimp/i',$html);$report[]=$newsletter?'html_to_newsletter':'html_to_contact';return'<!-- wp:shortcode -->['.($newsletter?'mirror_talk_newsletter':'mirror_talk_contact').']<!-- /wp:shortcode -->';}
    if(preg_match('/<iframe\b[^>]*\bsrc=["\']([^"\']+)["\']/i',$html,$m)){$url=esc_url_raw(html_entity_decode($m[1]));if($url){$host=(string)wp_parse_url($url,PHP_URL_HOST);$report[]='iframe_to_safe_link';return'<!-- wp:group {"className":"mt-migrated-feature"} --><div class="wp-block-group mt-migrated-feature"><h3>'.esc_html__('Continue with this trusted resource','astra-child').'</h3><p>'.esc_html(sprintf(__('This embedded experience is provided by %s and now opens only when you choose it.','astra-child'),$host?:__('an external service','astra-child'))).'</p><p><a class="mt-button" href="'.esc_url($url).'" target="_blank" rel="noopener">'.esc_html__('Open resource','astra-child').'</a></p></div><!-- /wp:group -->';}}
    $had_script=(bool)preg_match('/<(?:script|object|embed)\b/i',$html);$safe=wp_kses_post($html);if(trim(wp_strip_all_tags($safe))!==''||preg_match('/<a\b/i',$safe)){$report[]=$had_script?'script_removed_content_preserved':'safe_html';return'<!-- wp:html -->'.$safe.'<!-- /wp:html -->';}
    $report[]='unsafe_html_archived';return'<!-- wp:group {"className":"mt-migrated-feature"} --><div class="wp-block-group mt-migrated-feature"><p>'.esc_html__('An obsolete external component was safely removed during the site migration.','astra-child').'</p></div><!-- /wp:group -->';
}

function mirrortalk_elementor_generic_fallback($type,$settings,&$report){
    $texts=array();$links=array();$images=array();$walk=function($value,$key='')use(&$walk,&$texts,&$links,&$images){if(is_array($value)){foreach($value as$k=>$v)$walk($v,(string)$k);return;}if(!is_scalar($value))return;$value=trim((string)$value);if($value===''||strlen($value)>5000)return;if(filter_var($value,FILTER_VALIDATE_URL)){if(preg_match('/\.(?:jpe?g|png|webp|gif)(?:\?.*)?$/i',$value))$images[]=$value;else$links[]=$value;return;}if(preg_match('/(?:title|text|description|content|caption|name|heading)/i',$key)){ $plain=trim(wp_strip_all_tags($value));if(strlen($plain)>=2)$texts[]=$plain;}};$walk($settings);
    $texts=array_slice(array_values(array_unique($texts)),0,8);$links=array_slice(array_values(array_unique($links)),0,5);$images=array_slice(array_values(array_unique($images)),0,6);$body='';foreach($images as$image)$body.='<figure class="wp-block-image"><img src="'.esc_url($image).'" alt=""></figure>';foreach($texts as$i=>$text)$body.=($i===0?'<h3>'.esc_html($text).'</h3>':'<p>'.esc_html($text).'</p>');foreach($links as$link)$body.='<p><a href="'.esc_url($link).'">'.esc_html__('Open the referenced resource','astra-child').'</a></p>';
    if($body==='')$body='<p>'.esc_html__('A retired presentation component contained no public editorial content.','astra-child').'</p>';$report[]='fallback:'.sanitize_key($type);return'<!-- wp:group {"className":"mt-migrated-feature"} --><div class="wp-block-group mt-migrated-feature">'.$body.'</div><!-- /wp:group -->';
}

function mirrortalk_elementor_convert_elements($elements, &$report) {
    $output = '';
    foreach ((array)$elements as $element) {
        if (!is_array($element)) continue;
        $type = sanitize_key((string)($element['widgetType'] ?? ''));
        if ($type) $output .= mirrortalk_elementor_convert_widget($type, $element['settings'] ?? array(), $report)."\n";
        if (!empty($element['elements'])) $output .= mirrortalk_elementor_convert_elements($element['elements'], $report);
    }
    return trim($output);
}

function mirrortalk_elementor_conversion($post_id) {
    $raw = (string)get_post_meta($post_id, '_elementor_data', true); $data=json_decode($raw, true); $report=array();
    if (!is_array($data)) {
        $existing=(string)get_post_field('post_content',$post_id);$report[]='invalid_elementor_data_recovered';
        $content=trim($existing)!==''?$existing:'<!-- wp:paragraph --><p>'.esc_html__('This archived page contained no recoverable public editorial content.','astra-child').'</p><!-- /wp:paragraph -->';
        return array('content'=>$content,'report'=>$report,'hash'=>hash('sha256',$raw));
    }
    $content = mirrortalk_elementor_convert_elements($data, $report);
    if (trim(wp_strip_all_tags(strip_shortcodes($content))) === '' && strpos($content, '[mirror_talk_video') === false) return new WP_Error('empty_conversion', __('The conversion produced no meaningful content.', 'astra-child'));
    return array('content'=>$content, 'report'=>array_values(array_unique($report)), 'hash'=>hash('sha256',$raw));
}

function mirrortalk_elementor_source_text($value,$key=''){
    $parts=array();if(is_array($value)){foreach($value as$k=>$v)$parts=array_merge($parts,mirrortalk_elementor_source_text($v,(string)$k));return$parts;}
    if(!is_scalar($value)||!preg_match('/(?:title|text|description|content|caption|name|heading|editor|tab_)/i',$key))return$parts;$plain=trim(wp_strip_all_tags((string)$value));if(strlen($plain)>=2)$parts[]=$plain;return$parts;
}

function mirrortalk_elementor_conversion_quality($post_id,$conversion){
    $raw=(string)get_post_meta($post_id,'_elementor_data',true);$data=json_decode($raw,true);$source_parts=is_array($data)?array_values(array_unique(mirrortalk_elementor_source_text($data))):array();$source=implode(' ',$source_parts);$source_words=str_word_count(wp_strip_all_tags($source));$converted_words=str_word_count(wp_strip_all_tags(strip_shortcodes((string)($conversion['content']??''))));
    $ratio=$source_words>0?min(1,$converted_words/$source_words):1;$issues=array();if(trim((string)($conversion['content']??''))==='')$issues[]='empty_content';if($source_words>=20&&$ratio<.4)$issues[]='low_text_retention';if(strpos((string)($conversion['content']??''),'elementor-widget')!==false)$issues[]='elementor_markup_remaining';
    $recovery='';if(in_array('low_text_retention',$issues,true)){foreach($source_parts as$part)$recovery.='<p>'.esc_html($part).'</p>';}
    return array('source_words'=>$source_words,'converted_words'=>$converted_words,'retention'=>round($ratio,3),'issues'=>$issues,'passed'=>empty($issues),'recovery_html'=>$recovery);
}

function mirrortalk_elementor_snapshot($post_id) {
    $post = get_post($post_id); if (!$post) return new WP_Error('missing_post', __('Content not found.', 'astra-child'));
    $snapshot = array('version'=>MIRRORTALK_ELEMENTOR_MIGRATION_VERSION,'created'=>time(),'content'=>$post->post_content,
        'elementor_data'=>(string)get_post_meta($post_id,'_elementor_data',true),
        'edit_mode'=>(string)get_post_meta($post_id,'_elementor_edit_mode',true),
        'template'=>(string)get_post_meta($post_id,'_wp_page_template',true),
        'page_settings'=>get_post_meta($post_id,'_elementor_page_settings',true));
    $snapshot['checksum']=hash('sha256', wp_json_encode($snapshot));
    update_post_meta($post_id, '_mirrortalk_elementor_snapshot', $snapshot);
    return $snapshot;
}

function mirrortalk_elementor_migrate($post_id) {
    $lock='mt_elementor_migrating_'.$post_id;if(get_transient($lock))return new WP_Error('migration_locked',__('This document is already being migrated.','astra-child'));set_transient($lock,1,5*MINUTE_IN_SECONDS);
    $analysis=mirrortalk_elementor_analyse($post_id); if (!in_array(($analysis['readiness']??''),array('ready','adaptable'),true)){delete_transient($lock);return new WP_Error('review_required', __('This document is not currently eligible for migration.', 'astra-child'));}
    $conversion=mirrortalk_elementor_conversion($post_id); if(is_wp_error($conversion)){delete_transient($lock);return $conversion;}$quality=mirrortalk_elementor_conversion_quality($post_id,$conversion);if(!$quality['passed']){$recovered=(string)($quality['recovery_html']??'');$conversion['content'].='<!-- wp:group {"className":"mt-migrated-feature mt-migrated-recovery"} --><div class="wp-block-group mt-migrated-feature mt-migrated-recovery"><h2>'.esc_html__('Recovered from the original page','astra-child').'</h2>'.($recovered?:'<p>'.esc_html__('Additional legacy presentation data was archived safely during migration.','astra-child').'</p>').'</div><!-- /wp:group -->';$conversion['report'][]='retention_guard';}
    $snapshot=mirrortalk_elementor_snapshot($post_id); if(is_wp_error($snapshot)){delete_transient($lock);return $snapshot;}
    $before_url=get_permalink($post_id);$result=wp_update_post(array('ID'=>$post_id,'post_content'=>$conversion['content']),true); if(is_wp_error($result)){delete_transient($lock);return $result;}
    delete_post_meta($post_id,'_elementor_edit_mode'); delete_post_meta($post_id,'_elementor_css');delete_post_meta($post_id,'_elementor_data');
    $template=(string)get_post_meta($post_id,'_wp_page_template',true); if(strpos($template,'elementor_')===0)update_post_meta($post_id,'_wp_page_template','default');
    update_post_meta($post_id,'_mirrortalk_elementor_migrated',array('time'=>time(),'source_hash'=>$conversion['hash'],'report'=>$conversion['report'],'quality'=>$quality,'protected_url'=>$before_url));
    if(in_array('privacy_video',$conversion['report'],true)&&function_exists('mirrortalk_composer_v2_decisions')){$decisions=mirrortalk_composer_v2_decisions($post_id);$decisions['youtube_player']['enabled']=false;$decisions['youtube_player']['status']='disabled';$decisions['youtube_player']['updated_at']=time();update_post_meta($post_id,'_mt_composer_decisions',$decisions);}
    if(function_exists('mirrortalk_composer_v2_run'))mirrortalk_composer_v2_run($post_id,true);
    if(function_exists('mirrortalk_indexnow_queue_url'))mirrortalk_indexnow_queue_url(get_permalink($post_id));
    clean_post_cache($post_id); do_action('litespeed_purge_url',get_permalink($post_id));if(!wp_next_scheduled('mirrortalk_elementor_verify_migration',array($post_id)))wp_schedule_single_event(time()+MINUTE_IN_SECONDS,'mirrortalk_elementor_verify_migration',array($post_id));delete_transient($lock);
    return $conversion;
}

function mirrortalk_elementor_restore($post_id) {
    $snapshot=get_post_meta($post_id,'_mirrortalk_elementor_snapshot',true); if(!is_array($snapshot))return new WP_Error('missing_snapshot',__('No migration snapshot exists.','astra-child'));
    $check=$snapshot; unset($check['checksum']); if(!hash_equals((string)($snapshot['checksum']??''),hash('sha256',wp_json_encode($check))))return new WP_Error('snapshot_mismatch',__('The migration snapshot failed its integrity check.','astra-child'));
    $result=wp_update_post(array('ID'=>$post_id,'post_content'=>(string)$snapshot['content']),true); if(is_wp_error($result))return $result;
    update_post_meta($post_id,'_elementor_data',(string)$snapshot['elementor_data']);
    if($snapshot['edit_mode']!=='')update_post_meta($post_id,'_elementor_edit_mode',$snapshot['edit_mode']); else delete_post_meta($post_id,'_elementor_edit_mode');
    if($snapshot['template']!=='')update_post_meta($post_id,'_wp_page_template',$snapshot['template']);
    update_post_meta($post_id,'_elementor_page_settings',$snapshot['page_settings']); delete_post_meta($post_id,'_mirrortalk_elementor_migrated');
    clean_post_cache($post_id); do_action('litespeed_purge_url',get_permalink($post_id)); return true;
}

function mirrortalk_elementor_verify_migration($post_id){
    $post_id=absint($post_id);$state=(array)get_post_meta($post_id,'_mirrortalk_elementor_migrated',true);if(!$state)return;
    $url=get_permalink($post_id);$critical=array();if(!hash_equals((string)($state['protected_url']??$url),(string)$url))$critical[]='url_changed';if(trim((string)get_post_field('post_content',$post_id))==='')$critical[]='empty_content';
    $response=wp_remote_get($url,array('timeout'=>5,'redirection'=>2,'limit_response_size'=>262144,'user-agent'=>'MirrorTalkMigrationVerifier/'.MIRRORTALK_ELEMENTOR_MIGRATION_VERSION));if(is_wp_error($response))$status='unverified';else{$code=(int)wp_remote_retrieve_response_code($response);$body=(string)wp_remote_retrieve_body($response);$status=(string)$code;if($code>=500||preg_match('/critical error|fatal error/i',$body))$critical[]='public_render_failure';}
    if($critical){$restored=mirrortalk_elementor_restore($post_id);$result=is_wp_error($restored)?'rollback_failed':'rolled_back';}else$result='passed';
    update_post_meta($post_id,'_mirrortalk_elementor_verification',array('time'=>time(),'status'=>$status,'result'=>$result,'issues'=>$critical));$log=(array)get_option('mirrortalk_elementor_verification_log',array());$log[]=array('time'=>time(),'post_id'=>$post_id,'status'=>$status,'result'=>$result,'issues'=>$critical);update_option('mirrortalk_elementor_verification_log',array_slice($log,-200),false);
}
add_action('mirrortalk_elementor_verify_migration',function($post_id){mirrortalk_runtime_run('elementor_verify_'.absint($post_id),function()use($post_id){return mirrortalk_elementor_verify_migration($post_id);},5*MINUTE_IN_SECONDS);},10,1);
add_action('mirrortalk_elementor_migrate_async',function($post_id){$post_id=absint($post_id);if(!$post_id)return;$result=mirrortalk_runtime_run('elementor_migrate_'.$post_id,function()use($post_id){return mirrortalk_elementor_migrate($post_id);},10*MINUTE_IN_SECONDS);update_post_meta($post_id,'_mirrortalk_elementor_async_result',array('time'=>time(),'status'=>is_wp_error($result)?'failed':'migrated','message'=>is_wp_error($result)?$result->get_error_message():''));},10,1);

add_shortcode('mirror_talk_video', function($atts){
    $atts=shortcode_atts(array('id'=>''),$atts,'mirror_talk_video'); $id=preg_replace('/[^A-Za-z0-9_-]/','',(string)$atts['id']); if(strlen($id)!==11)return '';
    $video=array('id'=>$id,'title'=>__('Mirror Talk video','astra-child'),'thumbnail'=>'https://i.ytimg.com/vi/'.$id.'/hqdefault.jpg');
    return function_exists('mirrortalk_story_studio_video') ? mirrortalk_story_studio_video($video, get_the_ID()) : '<p><a href="'.esc_url('https://www.youtube.com/watch?v='.$id).'">'.esc_html__('Watch this conversation on YouTube','astra-child').'</a></p>';
});

function mirrortalk_elementor_migration_actions() {
    if(!current_user_can('manage_options'))return;
    $action=sanitize_key((string)($_REQUEST['mt_elementor_action']??'')); if(!$action)return;
    check_admin_referer('mirrortalk_elementor_migration'); $post_id=absint($_REQUEST['post_id']??0); $message='';
    if($action==='migrate'&&current_user_can('edit_post',$post_id)){if(!wp_next_scheduled('mirrortalk_elementor_migrate_async',array($post_id)))wp_schedule_single_event(time()+5,'mirrortalk_elementor_migrate_async',array($post_id));$message='document-migration-queued';}
    elseif($action==='restore'&&current_user_can('edit_post',$post_id)){$result=mirrortalk_elementor_restore($post_id);$message=is_wp_error($result)?'error:'.$result->get_error_message():'restored';}
    elseif($action==='batch'){update_option('mirrortalk_elementor_auto_migration',1,false);if(!wp_next_scheduled('mirrortalk_elementor_auto_batch'))wp_schedule_single_event(time()+5,'mirrortalk_elementor_auto_batch');$message='migration-batch-queued';}
    elseif($action==='resolve_residuals'){if(!wp_next_scheduled('mirrortalk_elementor_resolve_residuals_async'))wp_schedule_single_event(time()+5,'mirrortalk_elementor_resolve_residuals_async');$message='residual-cleanup-queued';}
    elseif($action==='restore_templates'){if(!wp_next_scheduled('mirrortalk_elementor_restore_templates_async'))wp_schedule_single_event(time()+5,'mirrortalk_elementor_restore_templates_async');$message='template-restore-queued';}
    elseif($action==='auto_start'){update_option('mirrortalk_elementor_auto_migration',1,false);if(!wp_next_scheduled('mirrortalk_elementor_auto_batch'))wp_schedule_single_event(time()+30,'mirrortalk_elementor_auto_batch');$message='automatic-migration-started';}
    elseif($action==='auto_stop'){update_option('mirrortalk_elementor_auto_migration',0,false);wp_clear_scheduled_hook('mirrortalk_elementor_auto_batch');$message='automatic-migration-paused';}
    elseif($action==='refresh_status'){mirrortalk_runtime_queue('mirrortalk_elementor_dashboard_refresh');$message='status-refresh-queued';}
    wp_safe_redirect(add_query_arg(array('page'=>'mirror-talk-elementor-migration','mt_notice'=>rawurlencode($message)),admin_url('admin.php')));exit;
}
add_action('admin_init','mirrortalk_elementor_migration_actions',30);

function mirrortalk_elementor_migration_menu(){add_submenu_page('mirror-talk-intelligence',__('Elementor Migration','astra-child'),__('Elementor Migration','astra-child'),'manage_options','mirror-talk-elementor-migration','mirrortalk_elementor_migration_page');}
add_action('admin_menu','mirrortalk_elementor_migration_menu',20);

function mirrortalk_elementor_action_url($action,$post_id=0){return wp_nonce_url(add_query_arg(array('page'=>'mirror-talk-elementor-migration','mt_elementor_action'=>$action,'post_id'=>$post_id),admin_url('admin.php')),'mirrortalk_elementor_migration');}

function mirrortalk_elementor_residual_dependencies($force=false){
    global $wpdb;
    $cached=get_transient('mirrortalk_elementor_residual_dependencies');if(!$force&&is_array($cached))return$cached;
    if(!$force){mirrortalk_runtime_queue('mirrortalk_elementor_residual_scan');return array('templates'=>0,'shortcodes'=>0,'pending'=>true);}
    $templates=(int)$wpdb->get_var("SELECT COUNT(ID) FROM {$wpdb->posts} WHERE post_type='elementor_library' AND post_status IN ('publish','future','private')");
    $shortcodes=(int)$wpdb->get_var("SELECT COUNT(ID) FROM {$wpdb->posts} WHERE post_type IN ('post','page') AND post_status NOT IN ('trash','auto-draft') AND post_content LIKE '%[elementor-template%'");
    $result=array('templates'=>$templates,'shortcodes'=>$shortcodes,'pending'=>false);set_transient('mirrortalk_elementor_residual_dependencies',$result,6*HOUR_IN_SECONDS);return$result;
}
add_action('mirrortalk_elementor_residual_scan',function(){
    $result=mirrortalk_runtime_run('elementor_residual_scan',function(){return mirrortalk_elementor_residual_dependencies(true);},10*MINUTE_IN_SECONDS);
    if(is_wp_error($result)||!is_array($result))return;
    $snapshot=(array)get_option('mirrortalk_elementor_dashboard_snapshot',array());
    $snapshot['residual']=$result;$snapshot['time']=time();
    update_option('mirrortalk_elementor_dashboard_snapshot',$snapshot,false);
});

/** Build the dashboard data away from the browser request. */
function mirrortalk_elementor_refresh_dashboard_snapshot(){
    $previous=(array)get_option('mirrortalk_elementor_dashboard_snapshot',array());
    $snapshot=array('time'=>time(),'status'=>'running','summary'=>$previous['summary']??array('pending'=>0,'migrated'=>0,'total'=>0,'pending_scan'=>true),'residual'=>$previous['residual']??array('templates'=>0,'shortcodes'=>0,'pending'=>true),'items'=>$previous['items']??array());
    update_option('mirrortalk_elementor_dashboard_snapshot',$snapshot,false);
    $snapshot['summary']=mirrortalk_elementor_migration_counts(true);
    update_option('mirrortalk_elementor_dashboard_snapshot',$snapshot,false);
    $snapshot['items']=mirrortalk_elementor_dashboard_items(12,0);
    update_option('mirrortalk_elementor_dashboard_snapshot',$snapshot,false);
    // The unindexed legacy-shortcode scan is isolated from the useful counts
    // and rows so even a host-level termination cannot erase their progress.
    $cached=get_transient('mirrortalk_elementor_residual_dependencies');
    $snapshot['residual']=is_array($cached)?$cached:array('templates'=>0,'shortcodes'=>0,'pending'=>true);
    $snapshot['status']='complete';
    update_option('mirrortalk_elementor_dashboard_snapshot',$snapshot,false);
    if(!is_array($cached))mirrortalk_runtime_queue('mirrortalk_elementor_residual_scan',array(),30);
    return $snapshot;
}
add_action('mirrortalk_elementor_dashboard_refresh',function(){mirrortalk_runtime_run('elementor_dashboard_refresh','mirrortalk_elementor_refresh_dashboard_snapshot',3*MINUTE_IN_SECONDS);});

function mirrortalk_elementor_expand_template_shortcodes(){
    global $wpdb;$posts=$wpdb->get_results("SELECT ID,post_content FROM {$wpdb->posts} WHERE post_type IN ('post','page') AND post_status NOT IN ('trash','auto-draft') AND post_content LIKE '%[elementor-template%'");$changed=0;
    foreach((array)$posts as$post){$original=(string)$post->post_content;$content=preg_replace_callback('/\[elementor-template\s+[^\]]*id=["\']?(\d+)["\']?[^\]]*\]/i',function($m){$conversion=mirrortalk_elementor_conversion(absint($m[1]));return is_wp_error($conversion)?'<div class="mt-migrated-feature"><p>'.esc_html__('An obsolete reusable layout was safely retired.','astra-child').'</p></div>':$conversion['content'];},$original);if($content===$original)continue;update_post_meta($post->ID,'_mirrortalk_elementor_shortcode_snapshot',array('time'=>time(),'content'=>$original,'checksum'=>hash('sha256',$original)));$result=wp_update_post(array('ID'=>$post->ID,'post_content'=>$content),true);if(!is_wp_error($result))$changed++;}
    return $changed;
}

function mirrortalk_elementor_retire_templates(){
    $templates=get_posts(array('post_type'=>'elementor_library','post_status'=>array('publish','future','private'),'numberposts'=>-1));$snapshots=(array)get_option('mirrortalk_elementor_template_snapshots',array());$retired=0;
    foreach($templates as$template){if(!isset($snapshots[$template->ID]))$snapshots[$template->ID]=array('status'=>$template->post_status,'content'=>$template->post_content,'data'=>get_post_meta($template->ID,'_elementor_data',true),'time'=>time());$result=wp_update_post(array('ID'=>$template->ID,'post_status'=>'draft'),true);if(!is_wp_error($result))$retired++;}
    update_option('mirrortalk_elementor_template_snapshots',$snapshots,false);return$retired;
}

function mirrortalk_elementor_restore_templates(){
    $snapshots=(array)get_option('mirrortalk_elementor_template_snapshots',array());$restored=0;foreach($snapshots as$id=>$snapshot){$result=wp_update_post(array('ID'=>absint($id),'post_status'=>sanitize_key($snapshot['status']??'draft'),'post_content'=>(string)($snapshot['content']??'')),true);if(is_wp_error($result))continue;update_post_meta(absint($id),'_elementor_data',$snapshot['data']??'');$restored++;}if($restored)delete_option('mirrortalk_elementor_template_snapshots');return$restored;
}

function mirrortalk_elementor_resolve_residuals(){
    return array('expanded'=>mirrortalk_elementor_expand_template_shortcodes(),'retired'=>mirrortalk_elementor_retire_templates());
}
add_action('mirrortalk_elementor_resolve_residuals_async',function(){$result=mirrortalk_runtime_run('elementor_residuals','mirrortalk_elementor_resolve_residuals',20*MINUTE_IN_SECONDS);update_option('mirrortalk_elementor_last_residual_result',array('time'=>time(),'result'=>$result),false);});
add_action('mirrortalk_elementor_restore_templates_async',function(){$restored=mirrortalk_runtime_run('elementor_template_restore','mirrortalk_elementor_restore_templates',20*MINUTE_IN_SECONDS);update_option('mirrortalk_elementor_last_template_restore',array('time'=>time(),'restored'=>$restored),false);});

function mirrortalk_elementor_auto_batch(){
    if(!get_option('mirrortalk_elementor_auto_migration')||get_transient('mt_elementor_auto_lock'))return;set_transient('mt_elementor_auto_lock',1,10*MINUTE_IN_SECONDS);$processed=0;$failed=0;
    foreach(mirrortalk_elementor_inventory(1,0,false)as$item){if($processed>=1)break;if(!in_array($item['readiness'],array('ready','adaptable'),true))continue;$result=mirrortalk_elementor_migrate($item['id']);is_wp_error($result)?$failed++:$processed++;}
    $log=(array)get_option('mirrortalk_elementor_migration_log',array());$log[]=array('time'=>time(),'processed'=>$processed,'failed'=>$failed);update_option('mirrortalk_elementor_migration_log',array_slice($log,-100),false);
    $remaining=mirrortalk_elementor_migration_counts(true)['pending']>0;
    delete_transient('mt_elementor_auto_lock');if($remaining&&$processed===0&&$failed>0){update_option('mirrortalk_elementor_auto_migration',0,false);update_option('mirrortalk_elementor_auto_attention',array('time'=>time(),'reason'=>'batch_failed','failed'=>$failed),false);return;}if($remaining){wp_schedule_single_event(time()+5*MINUTE_IN_SECONDS,'mirrortalk_elementor_auto_batch');return;}
    mirrortalk_elementor_resolve_residuals();update_option('mirrortalk_elementor_auto_migration',0,false);update_option('mirrortalk_elementor_auto_completed',time(),false);
}
add_action('mirrortalk_elementor_auto_batch',function(){mirrortalk_runtime_run('elementor_auto_batch','mirrortalk_elementor_auto_batch',15*MINUTE_IN_SECONDS);});

function mirrortalk_elementor_recover_schedule(){if(get_option('mirrortalk_elementor_auto_migration')&&!wp_next_scheduled('mirrortalk_elementor_auto_batch'))wp_schedule_single_event(time()+MINUTE_IN_SECONDS,'mirrortalk_elementor_auto_batch');}
add_action('admin_init','mirrortalk_elementor_recover_schedule',80);

function mirrortalk_elementor_migration_page(){
    if(!current_user_can('manage_options'))return;
    // Guaranteed-fast shell: no content queries, JSON decoding, scans, remote
    // requests or cron loopbacks are permitted during this page request.
    $snapshot=(array)get_option('mirrortalk_elementor_dashboard_snapshot',array());
    $summary=is_array($snapshot['summary']??null)?$snapshot['summary']:array('pending'=>0,'migrated'=>0,'total'=>0,'pending_scan'=>true);
    $residual=is_array($snapshot['residual']??null)?$snapshot['residual']:array('templates'=>0,'shortcodes'=>0,'pending'=>true);
    $items=is_array($snapshot['items']??null)?$snapshot['items']:array();
    $safe=!empty($snapshot['time'])&&empty($summary['pending_scan'])&&$summary['pending']===0&&empty($residual['pending'])&&$residual['templates']===0&&$residual['shortcodes']===0;
    $notice=sanitize_text_field(rawurldecode((string)($_GET['mt_notice']??'')));
    echo '<div class="wrap"><h1>'.esc_html__('Elementor Migration Centre','astra-child').'</h1><p>'.esc_html__('Convert Elementor documents into fast, semantic and fully owned Mirror Talk content. Every migration creates a checksum-protected snapshot and remains individually reversible.','astra-child').'</p>';
    if($notice)echo '<div class="notice '.(strpos($notice,'error:')===0?'notice-error':'notice-success').' is-dismissible"><p>'.esc_html($notice).'</p></div>';
    echo '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:24px 0">';foreach(array(array(__('Pending documents','astra-child'),!empty($summary['pending_scan'])?__('Refreshing…','astra-child'):$summary['pending']),array(__('Migrated','astra-child'),!empty($summary['pending_scan'])?__('Refreshing…','astra-child'):$summary['migrated']),array(__('Showing now','astra-child'),count($items)))as$card)echo'<div class="card"><h2>'.esc_html($card[0]).'</h2><p style="font-size:28px;margin:8px 0">'.esc_html((string)$card[1]).'</p></div>';echo'</div>';
    echo '<div class="card" style="max-width:none"><h2>'.esc_html__('Elementor deactivation gate','astra-child').'</h2><p><strong>'.esc_html($safe?__('SAFE TO DEACTIVATE','astra-child'):__('NOT YET SAFE','astra-child')).'</strong></p><p>'.esc_html($safe?__('No active documents, templates or template shortcodes depend on Elementor. Complete visual and form checks before uninstalling the plugin.','astra-child'):(!empty($summary['pending_scan'])||!empty($residual['pending'])?__('Dependency counts and residual template checks are refreshing safely in the background. Keep Elementor active until the gate has complete results.','astra-child'):sprintf(__('%1$d documents, %2$d Elementor templates and %3$d template shortcodes still require attention. Keep the plugin active.','astra-child'),$summary['pending'],$residual['templates'],$residual['shortcodes']))).'</p></div>';
    echo '<p><a class="button button-secondary" href="'.esc_url(mirrortalk_elementor_action_url('refresh_status')).'">'.esc_html__('Refresh migration status safely','astra-child').'</a> <span class="description">'.esc_html__('The scan runs after this page responds. Reload later to see its cached result.','astra-child').'</span></p>';
    $automatic=(bool)get_option('mirrortalk_elementor_auto_migration');echo'<div class="card" style="max-width:none"><h2>'.esc_html__('Automatic migration','astra-child').'</h2><p>'.esc_html($automatic?__('Running one document per guarded background batch to protect production performance.','astra-child'):__('Paused. Start it when the staging snapshot and backup are ready.','astra-child')).'</p><p><a class="button '.($automatic?'':'button-primary').'" href="'.esc_url(mirrortalk_elementor_action_url($automatic?'auto_stop':'auto_start')).'">'.esc_html($automatic?__('Pause automatic migration','astra-child'):__('Start automatic owned-content migration','astra-child')).'</a></p></div>';
    if($summary['pending']===0&&($residual['templates']||$residual['shortcodes']))echo'<p><a class="button button-secondary" href="'.esc_url(mirrortalk_elementor_action_url('resolve_residuals')).'">'.esc_html__('Queue template-shortcode conversion and template retirement','astra-child').'</a></p>';
    if(get_option('mirrortalk_elementor_template_snapshots'))echo'<p><a href="'.esc_url(mirrortalk_elementor_action_url('restore_templates')).'">'.esc_html__('Restore retired Elementor templates','astra-child').'</a></p>';
    if($summary['pending'])echo'<p><a class="button button-primary" href="'.esc_url(mirrortalk_elementor_action_url('batch')).'">'.esc_html__('Queue the next safe migration batch','astra-child').'</a> <span class="description">'.esc_html__('Work runs outside this browser request in small resumable batches.','astra-child').'</span></p>';
    echo '<table class="widefat striped"><thead><tr><th>'.esc_html__('Content','astra-child').'</th><th>'.esc_html__('Status','astra-child').'</th><th>'.esc_html__('Widgets','astra-child').'</th><th>'.esc_html__('Fallback adapters','astra-child').'</th><th>'.esc_html__('Actions','astra-child').'</th></tr></thead><tbody>';
    foreach($items as$item){$widgets=array();$bad=$item['migrated']?(array)($item['migration_state']['report']??array()):array();$status=$item['readiness'];if($item['migrated']&&!empty($item['verification']['result']))$status.=' · '.$item['verification']['result'];echo'<tr><td><strong>'.esc_html($item['title']).'</strong><br><small>'.esc_html($item['type'].' #'.$item['id']).'</small></td><td>'.esc_html($status).'</td><td>'.esc_html($item['migrated']?__('Converted','astra-child'):__('Analysed in background','astra-child')).'</td><td>'.esc_html($bad?implode(', ',$bad):'—').'</td><td><a href="'.esc_url($item['url']).'" target="_blank" rel="noopener">'.esc_html__('View','astra-child').'</a>';
        if($item['readiness']==='pending')echo' · <a href="'.esc_url(mirrortalk_elementor_action_url('migrate',$item['id'])).'">'.esc_html__('Queue migration','astra-child').'</a>';
        if($item['readiness']==='migrated')echo' · <a href="'.esc_url(mirrortalk_elementor_action_url('restore',$item['id'])).'">'.esc_html__('Restore','astra-child').'</a>';echo'</td></tr>';}
    if(!$items)echo'<tr><td colspan="5">'.esc_html__('No Elementor-authored posts or pages were found on this page.','astra-child').'</td></tr>';echo'</tbody></table>';
    echo'</div>';
}
