<?php
/**
 * Mirror Talk Elementor Migration Centre.
 *
 * Converts fully supported Elementor documents into semantic WordPress content.
 * Every mutation is preceded by a complete, checksum-protected snapshot.
 */
if (!defined('ABSPATH')) exit;

const MIRRORTALK_ELEMENTOR_MIGRATION_VERSION = '2.1.0';
const MIRRORTALK_ELEMENTOR_MAX_RETRIES = 3;

function mirrortalk_elementor_supported_widgets() {
    return array('heading','text-editor','image','video','button','shortcode','divider','spacer','icon-list','social-icons','image-box','icon-box','testimonial','accordion','toggle','tabs','image-carousel','gallery','menu-anchor','counter','progress','star-rating','google_maps','form','wpforms','contact-form-7','mailchimp','subscribe','slides','media-carousel','testimonial-carousel','loop-carousel','posts','html');
}

function mirrortalk_elementor_inventory($limit = 50, $offset = 0, $include_migrated = true) {
    global $wpdb;$limit=min(100,max(1,absint($limit)));$offset=max(0,absint($offset));
    $migrated_sql=$include_migrated?" OR EXISTS (SELECT 1 FROM {$wpdb->postmeta} mm WHERE mm.post_id=p.ID AND mm.meta_key='_mirrortalk_elementor_migrated')":'';
    $ids=$wpdb->get_col($wpdb->prepare(
        "SELECT p.ID FROM {$wpdb->posts} p WHERE p.post_type IN ('post','page') AND p.post_status IN ('publish','future','draft','pending','private') AND (EXISTS (SELECT 1 FROM {$wpdb->postmeta} d WHERE d.post_id=p.ID AND d.meta_key='_elementor_data' AND LENGTH(TRIM(d.meta_value))>4 AND TRIM(d.meta_value) NOT IN ('[]','null','{}')){$migrated_sql}) ORDER BY p.ID ASC LIMIT %d OFFSET %d",
        $limit,$offset
    ));
    $items = array();
    foreach ((array)$ids as $id) {$post=get_post((int)$id);if(!$post)continue;
        $data = (string) get_post_meta($post->ID, '_elementor_data', true);
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
    // Include jobs whose Elementor source was removed during a provisional
    // commit. Otherwise a failed live verification disappears from the
    // summary even though it remains quarantined in the exact queue.
    $active_ids=$wpdb->get_col("SELECT DISTINCT p.ID FROM {$wpdb->posts} p WHERE {$eligible} AND (EXISTS (SELECT 1 FROM {$wpdb->postmeta} source WHERE source.post_id=p.ID AND source.meta_key='_elementor_data' AND LENGTH(TRIM(source.meta_value))>4 AND TRIM(source.meta_value) NOT IN ('[]','null','{}')) OR EXISTS (SELECT 1 FROM {$wpdb->postmeta} job WHERE job.post_id=p.ID AND job.meta_key='_mirrortalk_elementor_job'))");
    $pending=0;$quarantined=0;$queued=0;
    foreach((array)$active_ids as$id){
        if(get_post_meta($id,'_mirrortalk_elementor_migrated',true))continue;
        $job=(array)get_post_meta($id,'_mirrortalk_elementor_job',true);$status=(string)($job['status']??'pending');
        if($status==='quarantined')$quarantined++;elseif(in_array($status,array('queued','preparing','preview_ready','preview_verifying','committing','live_verifying','retry_wait'),true))$queued++;else$pending++;
    }
    $migrated = (int) $wpdb->get_var(
        "SELECT COUNT(DISTINCT p.ID) FROM {$wpdb->posts} p
         INNER JOIN {$wpdb->postmeta} migrated ON migrated.post_id=p.ID AND migrated.meta_key='_mirrortalk_elementor_migrated'
         WHERE {$eligible}"
    );
    $stale=(int)$wpdb->get_var("SELECT COUNT(DISTINCT p.ID) FROM {$wpdb->posts} p INNER JOIN {$wpdb->postmeta} mode ON mode.post_id=p.ID AND mode.meta_key='_elementor_edit_mode' LEFT JOIN {$wpdb->postmeta} data ON data.post_id=p.ID AND data.meta_key='_elementor_data' AND LENGTH(TRIM(data.meta_value))>4 AND TRIM(data.meta_value) NOT IN ('[]','null','{}') WHERE {$eligible} AND data.post_id IS NULL");
    $result = array('pending'=>$pending,'queued'=>$queued,'quarantined'=>$quarantined,'stale'=>$stale,'migrated'=>$migrated,'total'=>$pending+$queued+$quarantined+$migrated,'pending_scan'=>false);
    set_transient('mirrortalk_elementor_migration_counts', $result, HOUR_IN_SECONDS);
    update_option('mirrortalk_elementor_migration_counts_last', $result, false);
    return $result;
}
add_action('mirrortalk_elementor_count_scan',function(){mirrortalk_runtime_run('elementor_count_scan',function(){return mirrortalk_elementor_migration_counts(true);},10*MINUTE_IN_SECONDS);});

/** Dashboard rows intentionally never load the potentially huge JSON payload. */
function mirrortalk_elementor_dashboard_items($limit = 100, $offset = 0) {
    global $wpdb;
    $limit=min(100,max(1,absint($limit)));$offset=max(0,absint($offset));
    // EXISTS can use post_id/meta_key indexes and avoids WP_Query's expensive
    // OR-meta JOIN/GROUP BY construction on large postmeta tables.
    $ids=$wpdb->get_col($wpdb->prepare(
        "SELECT p.ID FROM {$wpdb->posts} p
         WHERE p.post_type IN ('post','page')
           AND p.post_status IN ('publish','future','draft','pending','private')
           AND (EXISTS (SELECT 1 FROM {$wpdb->postmeta} pm WHERE pm.post_id=p.ID AND pm.meta_key='_elementor_data' AND LENGTH(TRIM(pm.meta_value))>4 AND TRIM(pm.meta_value) NOT IN ('[]','null','{}')) OR EXISTS (SELECT 1 FROM {$wpdb->postmeta} mm WHERE mm.post_id=p.ID AND mm.meta_key IN ('_mirrortalk_elementor_migrated','_mirrortalk_elementor_job')))
         ORDER BY p.ID ASC LIMIT %d OFFSET %d",
        $limit,$offset
    ));
    $items=array();foreach((array)$ids as$id){$id=absint($id);$state=get_post_meta($id,'_mirrortalk_elementor_migrated',true);$verification=(array)get_post_meta($id,'_mirrortalk_elementor_verification',true);$job=(array)get_post_meta($id,'_mirrortalk_elementor_job',true);$migrated=is_array($state)&&!empty($state);$status=$migrated?'migrated':(string)($job['status']??'pending');$items[]=array('id'=>$id,'title'=>get_the_title($id),'type'=>get_post_type($id),'url'=>get_permalink($id),'widgets'=>(array)($job['widgets']??array()),'unsupported'=>(array)($job['unsupported']??array()),'migrated'=>$migrated,'migration_state'=>$migrated?$state:array(),'verification'=>$verification,'job'=>$job,'readiness'=>$status);}return$items;
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
    $migration_state = get_post_meta($post->ID, '_mirrortalk_elementor_migrated', true);$is_migrated=(bool)$migration_state;$verification=(array)get_post_meta($post->ID,'_mirrortalk_elementor_verification',true);$job=(array)get_post_meta($post->ID,'_mirrortalk_elementor_job',true);
    $valid = is_array($data) && !empty($data);
    return array(
        'id'=>(int)$post->ID, 'title'=>get_the_title($post), 'type'=>$post->post_type, 'status'=>$post->post_status,
        'url'=>get_permalink($post), 'widgets'=>$widgets, 'unsupported'=>$unsupported, 'template'=>$template,
        'has_form'=>$has_form, 'migrated'=>$is_migrated, 'valid'=>$valid,'migration_state'=>is_array($migration_state)?$migration_state:array(),'verification'=>$verification,'job'=>$job,
        'readiness'=>$is_migrated?'migrated':(($job['status']??'')==='quarantined'?'quarantined':(!$valid?'stale':($unsupported?'adaptable':'ready'))),
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

function mirrortalk_elementor_audit($post_id,$event,$details=array()){
    $entry=array('time'=>time(),'post_id'=>absint($post_id),'event'=>sanitize_key($event),'details'=>array());
    foreach((array)$details as$key=>$value)$entry['details'][sanitize_key((string)$key)]=is_scalar($value)?sanitize_text_field((string)$value):wp_json_encode($value);
    $local=(array)get_post_meta($post_id,'_mirrortalk_elementor_audit',true);$local[]=$entry;update_post_meta($post_id,'_mirrortalk_elementor_audit',array_slice($local,-100));
    $global=(array)get_option('mirrortalk_elementor_audit_log',array());$global[]=$entry;update_option('mirrortalk_elementor_audit_log',array_slice($global,-2000),false);
    return $entry;
}

function mirrortalk_elementor_job_update($post_id,$status,$details=array()){
    $job=(array)get_post_meta($post_id,'_mirrortalk_elementor_job',true);
    $job=array_merge($job,(array)$details,array('version'=>MIRRORTALK_ELEMENTOR_MIGRATION_VERSION,'status'=>sanitize_key($status),'updated'=>time()));
    if(empty($job['created']))$job['created']=time();update_post_meta($post_id,'_mirrortalk_elementor_job',$job);
    mirrortalk_elementor_audit($post_id,$status,$details);delete_transient('mirrortalk_elementor_migration_counts');
    // Keep the cached, fast dashboard current without making an admin request
    // perform the scan. Debouncing makes rapid stage transitions inexpensive.
    if(!wp_next_scheduled('mirrortalk_elementor_dashboard_refresh'))wp_schedule_single_event(time()+15,'mirrortalk_elementor_dashboard_refresh');return$job;
}

/** Remove duplicate H1s, constrain heading jumps and apply owned formatting. */
function mirrortalk_elementor_normalize_candidate($post_id,$content){
    $title=mirrortalk_elementor_normalize_title(get_the_title($post_id));$seen_heading=false;$last_level=1;
    $content=preg_replace_callback('#<h([1-6])([^>]*)>(.*?)</h\1>#is',function($match)use(&$seen_heading,&$last_level,$title){
        $text = trim(wp_strip_all_tags($match[3]));
        if (!$seen_heading && $title && mirrortalk_elementor_normalize_title($text) === $title) {
            $seen_heading = true;
            return '';
        }
        $level=max(2,(int)$match[1]);if($level>$last_level+1)$level=$last_level+1;$last_level=$level;$seen_heading=true;
        return '<h'.$level.$match[2].'>'.$match[3].'</h'.$level.'>';
    },(string)$content);
    if(function_exists('mirrortalk_semantic_repair_content'))$content=mirrortalk_semantic_repair_content($content);
    if(function_exists('mirrortalk_autolink_plain_urls'))$content=mirrortalk_autolink_plain_urls($content);
    // Semantic repair can add headings after the first normalization pass.
    // Constrain the final document too, so a repair never creates an H2→H4
    // jump that would needlessly quarantine an otherwise sound conversion.
    $last_level=1;
    $content=preg_replace_callback('#<h([1-6])([^>]*)>(.*?)</h\1>#is',function($match)use(&$last_level){
        $level=max(2,(int)$match[1]);if($level>$last_level+1)$level=$last_level+1;$last_level=$level;
        return '<h'.$level.$match[2].'>'.$match[3].'</h'.$level.'>';
    },(string)$content);
    return '<!-- wp:group {"className":"mt-migrated-document"} --><div class="wp-block-group mt-migrated-document" data-mt-owned-migration="'.esc_attr((string)$post_id).'">'.trim($content).'</div><!-- /wp:group -->';
}

function mirrortalk_elementor_normalize_title($value){return trim(preg_replace('/\s+/u',' ',strtolower(remove_accents(wp_strip_all_tags((string)$value)))));}

function mirrortalk_elementor_candidate($post_id){$candidate=get_post_meta($post_id,'_mirrortalk_elementor_candidate',true);return is_array($candidate)?$candidate:array();}

function mirrortalk_elementor_prepare_candidate($post_id){
    $analysis=mirrortalk_elementor_analyse($post_id);if(empty($analysis['valid']))return new WP_Error('stale_elementor_metadata',__('No active Elementor document data remains.','astra-child'));
    $conversion=mirrortalk_elementor_conversion($post_id);if(is_wp_error($conversion))return$conversion;
    $conversion['content']=mirrortalk_elementor_normalize_candidate($post_id,$conversion['content']);
    $quality=mirrortalk_elementor_conversion_quality($post_id,$conversion);
    if(in_array('low_text_retention',(array)$quality['issues'],true)&&!empty($quality['recovery_html'])){
        $conversion['content'].='<!-- wp:group {"className":"mt-migrated-feature mt-migrated-recovery"} --><div class="wp-block-group mt-migrated-feature mt-migrated-recovery"><h2>'.esc_html__('More from the original page','astra-child').'</h2>'.$quality['recovery_html'].'</div><!-- /wp:group -->';
        $conversion['report'][]='retention_guard';$quality=mirrortalk_elementor_conversion_quality($post_id,$conversion);
    }
    if(trim(wp_strip_all_tags(strip_shortcodes($conversion['content'])))==='')return new WP_Error('empty_conversion',__('The conversion produced no meaningful content.','astra-child'));
    $token=wp_generate_password(40,false,false);$candidate=array('version'=>MIRRORTALK_ELEMENTOR_MIGRATION_VERSION,'created'=>time(),'content'=>$conversion['content'],'report'=>array_values(array_unique($conversion['report'])),'source_hash'=>$conversion['hash'],'content_hash'=>hash('sha256',$conversion['content']),'quality'=>$quality,'token_hash'=>wp_hash_password($token));
    update_post_meta($post_id,'_mirrortalk_elementor_candidate',$candidate);set_transient('mirrortalk_elementor_preview_'.$post_id,$token,30*MINUTE_IN_SECONDS);
    mirrortalk_elementor_job_update($post_id,'preview_ready',array('widgets'=>$analysis['widgets'],'unsupported'=>$analysis['unsupported'],'report'=>$candidate['report'],'quality'=>$quality));return$candidate;
}

function mirrortalk_elementor_preview_token($post_id){return(string)get_transient('mirrortalk_elementor_preview_'.absint($post_id));}
function mirrortalk_elementor_preview_url($post_id){$token=mirrortalk_elementor_preview_token($post_id);return$token?add_query_arg(array('mt_elementor_preview'=>$token,'mt_preview_post'=>absint($post_id)),get_permalink($post_id)):'';}
function mirrortalk_elementor_preview_request(){
    $post_id=absint($_GET['mt_preview_post']??0);$token=sanitize_text_field(wp_unslash($_GET['mt_elementor_preview']??''));$stored=mirrortalk_elementor_preview_token($post_id);
    return$post_id&&$token&&$stored&&hash_equals($stored,$token)?$post_id:0;
}
add_filter('the_content',function($content){$post_id=mirrortalk_elementor_preview_request();if(!$post_id||get_the_ID()!==$post_id)return$content;$candidate=mirrortalk_elementor_candidate($post_id);return'<div data-mt-migration-preview="'.esc_attr((string)$post_id).'">'.($candidate['content']??'').'</div>';},PHP_INT_MAX);
add_filter('wp_robots',function($robots){if(mirrortalk_elementor_preview_request()){$robots['noindex']=true;$robots['nofollow']=true;$robots['noarchive']=true;}return$robots;});
add_action('send_headers',function(){if(mirrortalk_elementor_preview_request()){nocache_headers();header('X-Robots-Tag: noindex, nofollow, noarchive',true);}});

function mirrortalk_elementor_markup_checks($post_id,$content){
    $issues=array();if(stripos($content,'data-mt-owned-migration=')===false)$issues[]='owned_marker_missing';if(preg_match('/<h1\b/i',$content))$issues[]='duplicate_h1';
    preg_match_all('/<h([2-6])\b/i',$content,$headings);$last=1;foreach((array)($headings[1]??array())as$level){$level=(int)$level;if($level>$last+1)$issues[]='heading_level_jump';$last=$level;}
    if(preg_match('/(?:elementor-widget|elementor-section|data-elementor)/i',$content))$issues[]='elementor_markup_remaining';
    if(preg_match('/<img\b(?![^>]*\balt=)[^>]*>/i',$content))$issues[]='image_alt_missing';
    if(strlen(wp_strip_all_tags($content))<40)$issues[]='content_too_short';return array_values(array_unique($issues));
}

function mirrortalk_elementor_remote_render($post_id,$url,$profile,$expect_preview=false){
    $agents=array('desktop'=>'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36','mobile'=>'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1');
    // The URL is generated from this site's permalink, never supplied by a visitor.
    // wp_remote_get is intentional: some hosts reject their own loopback as an SSRF
    // when wp_safe_remote_get is used, which would quarantine every valid document.
    $response=wp_remote_get($url,array('timeout'=>12,'redirection'=>2,'limit_response_size'=>1048576,'user-agent'=>$agents[$profile]??$agents['desktop'],'headers'=>array('Cache-Control'=>'no-cache','X-Mirror-Talk-Migration'=>'verify')));
    if(is_wp_error($response))return array('passed'=>false,'recoverable'=>true,'profile'=>$profile,'status'=>'transport_error','issues'=>array($response->get_error_code()));
    $code=(int)wp_remote_retrieve_response_code($response);$body=(string)wp_remote_retrieve_body($response);$issues=array();
    if($code<200||$code>=400)$issues[]='http_'.$code;if(preg_match('/critical error|fatal error|gateway time-out|maximum execution time/i',$body))$issues[]='render_failure';
    if(stripos($body,'data-mt-owned-migration="'.absint($post_id).'"')===false)$issues[]='candidate_not_rendered';
    if($expect_preview&&stripos($body,'data-mt-migration-preview="'.absint($post_id).'"')===false)$issues[]='preview_not_rendered';
    if(stripos($body,'name="viewport"')===false)$issues[]='responsive_viewport_missing';
    return array('passed'=>empty($issues),'recoverable'=>(bool)array_filter($issues,function($issue){return strpos($issue,'http_5')===0||in_array($issue,array('render_failure','candidate_not_rendered'),true); }),'profile'=>$profile,'status'=>$code,'bytes'=>strlen($body),'issues'=>$issues);
}

function mirrortalk_elementor_render_validation($post_id,$preview=true){
    $candidate=mirrortalk_elementor_candidate($post_id);$content=$preview?(string)($candidate['content']??''):(string)get_post_field('post_content',$post_id);$issues=mirrortalk_elementor_markup_checks($post_id,$content);
    $url=$preview?mirrortalk_elementor_preview_url($post_id):get_permalink($post_id);$profiles=array();$recoverable=false;
    if(!$url)$issues[]='preview_token_missing';else foreach(array('desktop','mobile')as$profile){$check=mirrortalk_elementor_remote_render($post_id,$url,$profile,$preview);$profiles[$profile]=$check;if(empty($check['passed']))$issues=array_merge($issues,$check['issues']);if(!empty($check['recoverable']))$recoverable=true;}
    return array('time'=>time(),'stage'=>$preview?'preview':'live','passed'=>empty($issues),'recoverable'=>$recoverable,'profiles'=>$profiles,'issues'=>array_values(array_unique($issues)));
}

function mirrortalk_elementor_snapshot($post_id) {
    $post = get_post($post_id); if (!$post) return new WP_Error('missing_post', __('Content not found.', 'astra-child'));
    $snapshot = array('version'=>MIRRORTALK_ELEMENTOR_MIGRATION_VERSION,'created'=>time(),'content'=>$post->post_content,
        'elementor_data'=>(string)get_post_meta($post_id,'_elementor_data',true),
        'edit_mode'=>(string)get_post_meta($post_id,'_elementor_edit_mode',true),
        'template'=>(string)get_post_meta($post_id,'_wp_page_template',true),
        'page_settings'=>get_post_meta($post_id,'_elementor_page_settings',true));
    $snapshot['checksum']=hash('sha256', wp_json_encode($snapshot));
    // Metadata APIs unslash input. Preserve JSON and embedded markup exactly;
    // otherwise their backslashes change after storage and invalidate the
    // rollback checksum created moments earlier.
    update_post_meta($post_id, '_mirrortalk_elementor_snapshot', wp_slash($snapshot));
    return $snapshot;
}

function mirrortalk_elementor_schedule_stage($post_id,$stage,$delay=5){
    $args=array(absint($post_id),sanitize_key($stage));if(!wp_next_scheduled('mirrortalk_elementor_process_stage',$args))wp_schedule_single_event(time()+max(1,absint($delay)),'mirrortalk_elementor_process_stage',$args);
}

function mirrortalk_elementor_queue_document($post_id,$source='automatic'){
    $analysis=mirrortalk_elementor_analyse($post_id);if(empty($analysis['valid']))return new WP_Error('stale_elementor_metadata',__('No active Elementor content needs migration.','astra-child'));
    if($analysis['migrated'])return new WP_Error('already_migrated',__('This document is already verified as migrated.','astra-child'));
    mirrortalk_elementor_job_update($post_id,'queued',array('source'=>$source,'attempts'=>0,'last_error'=>'','next_stage'=>'prepare','widgets'=>$analysis['widgets'],'unsupported'=>$analysis['unsupported']));
    mirrortalk_elementor_schedule_stage($post_id,'prepare',2);return true;
}

function mirrortalk_elementor_fail_stage($post_id,$stage,$error,$recoverable=false,$retry_stage=''){
    $job=(array)get_post_meta($post_id,'_mirrortalk_elementor_job',true);$attempts=(int)($job['attempts']??0)+1;$message=is_wp_error($error)?$error->get_error_message():(is_array($error)?implode(', ',(array)($error['issues']??array())):(string)$error);
    $retry_stage=$retry_stage?:$stage;if($recoverable&&$attempts<MIRRORTALK_ELEMENTOR_MAX_RETRIES){$delay=min(15*MINUTE_IN_SECONDS,$attempts*2*MINUTE_IN_SECONDS);mirrortalk_elementor_job_update($post_id,'retry_wait',array('attempts'=>$attempts,'last_error'=>$message,'failed_stage'=>$stage,'next_stage'=>$retry_stage,'retry_at'=>time()+$delay));mirrortalk_elementor_schedule_stage($post_id,$retry_stage,$delay);return'retrying';}
    mirrortalk_elementor_job_update($post_id,'quarantined',array('attempts'=>$attempts,'last_error'=>$message,'failed_stage'=>$stage,'next_stage'=>'','quarantined_at'=>time()));return'quarantined';
}

function mirrortalk_elementor_process_stage($post_id,$stage){
    $post_id=absint($post_id);$stage=sanitize_key($stage);$lock='mt_elementor_stage_'.$post_id;if(!$post_id||get_transient($lock))return;set_transient($lock,1,3*MINUTE_IN_SECONDS);
    try{
        if($stage==='prepare'){
            mirrortalk_elementor_job_update($post_id,'preparing',array('next_stage'=>'preview'));
            $candidate=mirrortalk_elementor_prepare_candidate($post_id);if(is_wp_error($candidate)){mirrortalk_elementor_fail_stage($post_id,$stage,$candidate,false);return;}
            mirrortalk_elementor_schedule_stage($post_id,'preview',3);return;
        }
        if($stage==='preview'){
            mirrortalk_elementor_job_update($post_id,'preview_verifying',array('next_stage'=>'commit'));
            $validation=mirrortalk_elementor_render_validation($post_id,true);update_post_meta($post_id,'_mirrortalk_elementor_preview_validation',$validation);
            if(empty($validation['passed'])){mirrortalk_elementor_fail_stage($post_id,$stage,$validation,!empty($validation['recoverable']));return;}
            mirrortalk_elementor_job_update($post_id,'preview_verified',array('preview_validation'=>$validation,'next_stage'=>'commit'));mirrortalk_elementor_schedule_stage($post_id,'commit',3);return;
        }
        if($stage==='commit'){
            $candidate=mirrortalk_elementor_candidate($post_id);if(empty($candidate['content'])){mirrortalk_elementor_fail_stage($post_id,$stage,new WP_Error('candidate_missing',__('The verified candidate is missing.','astra-child')),false);return;}
            mirrortalk_elementor_job_update($post_id,'committing',array('next_stage'=>'live'));
            $snapshot=mirrortalk_elementor_snapshot($post_id);if(is_wp_error($snapshot)){mirrortalk_elementor_fail_stage($post_id,$stage,$snapshot,false);return;}
            // WordPress validates the stored page-template value during a post
            // update. Elementor templates become invalid as soon as ownership
            // moves to this theme, so normalize them before that validation.
            $template=(string)get_post_meta($post_id,'_wp_page_template',true);if(strpos($template,'elementor_')===0)update_post_meta($post_id,'_wp_page_template','default');
            $before_url=get_permalink($post_id);$result=wp_update_post(array('ID'=>$post_id,'post_content'=>$candidate['content']),true);if(is_wp_error($result)){mirrortalk_elementor_restore($post_id,true);mirrortalk_elementor_fail_stage($post_id,$stage,$result,true);return;}
            delete_post_meta($post_id,'_elementor_edit_mode');delete_post_meta($post_id,'_elementor_css');delete_post_meta($post_id,'_elementor_data');
            update_post_meta($post_id,'_mirrortalk_elementor_provisional',array('time'=>time(),'source_hash'=>$candidate['source_hash'],'content_hash'=>$candidate['content_hash'],'report'=>$candidate['report'],'quality'=>$candidate['quality'],'protected_url'=>$before_url));
            if(function_exists('mirrortalk_composer_v2_run'))mirrortalk_composer_v2_run($post_id,true);clean_post_cache($post_id);do_action('litespeed_purge_url',$before_url);
            mirrortalk_elementor_job_update($post_id,'live_verifying',array('next_stage'=>'live'));mirrortalk_elementor_schedule_stage($post_id,'live',5);return;
        }
        if($stage==='live'){
            $provisional=(array)get_post_meta($post_id,'_mirrortalk_elementor_provisional',true);if(!$provisional){mirrortalk_elementor_fail_stage($post_id,$stage,new WP_Error('provisional_state_missing',__('The provisional migration state is missing.','astra-child')),false);return;}
            $validation=mirrortalk_elementor_render_validation($post_id,false);update_post_meta($post_id,'_mirrortalk_elementor_verification',$validation);
            if(empty($validation['passed'])){
                $restored=mirrortalk_elementor_restore($post_id,true);$error=is_wp_error($restored)?$restored:$validation;mirrortalk_elementor_fail_stage($post_id,'live',$error,!empty($validation['recoverable'])&&!is_wp_error($restored),'prepare');return;
            }
            update_post_meta($post_id,'_mirrortalk_elementor_migrated',array_merge($provisional,array('time'=>time(),'verification'=>$validation,'version'=>MIRRORTALK_ELEMENTOR_MIGRATION_VERSION)));delete_post_meta($post_id,'_mirrortalk_elementor_provisional');delete_post_meta($post_id,'_mirrortalk_elementor_candidate');delete_transient('mirrortalk_elementor_preview_'.$post_id);
            mirrortalk_elementor_job_update($post_id,'migrated',array('verified_at'=>time(),'next_stage'=>'','last_error'=>'','verification'=>$validation));
            if(function_exists('mirrortalk_indexnow_queue_url'))mirrortalk_indexnow_queue_url(get_permalink($post_id));mirrortalk_elementor_migration_counts(true);return;
        }
        mirrortalk_elementor_fail_stage($post_id,$stage,new WP_Error('unknown_stage',__('Unknown migration stage.','astra-child')),false);
    }finally{delete_transient($lock);}
}
add_action('mirrortalk_elementor_process_stage','mirrortalk_elementor_process_stage',10,2);

function mirrortalk_elementor_migrate($post_id){return mirrortalk_elementor_queue_document($post_id,'manual');
}

function mirrortalk_elementor_restore($post_id,$internal=false) {
    $snapshot=get_post_meta($post_id,'_mirrortalk_elementor_snapshot',true); if(!is_array($snapshot))return new WP_Error('missing_snapshot',__('No migration snapshot exists.','astra-child'));
    $check=$snapshot; unset($check['checksum']);$expected=(string)($snapshot['checksum']??'');$direct=hash('sha256',wp_json_encode($check));$legacy=hash('sha256',wp_json_encode(wp_slash($check)));
    // Releases before migration engine 2.1 stored the snapshot without
    // wp_slash(), so WordPress changed JSON escaping before retrieval. Accept
    // that exact reversible legacy transformation, but no arbitrary mismatch.
    $valid=$expected&&(hash_equals($expected,$direct)||hash_equals($expected,$legacy));
    if(!$valid){
        // The 2.0.x writer allowed WordPress to unslash nested JSON before it
        // was persisted, so its original checksum cannot always be recreated.
        // Recovery is permitted only for that known release family when the
        // snapshot is structurally complete and its Elementor source remains
        // valid JSON. This is private post metadata created by this engine,
        // never request input, and the exception is recorded in the audit.
        $legacy_version=(string)($snapshot['version']??'');$legacy_data=json_decode((string)($snapshot['elementor_data']??''),true);
        $valid=strpos($legacy_version,'2.0.')===0&&strlen($expected)===64&&!empty($snapshot['created'])&&array_key_exists('content',$snapshot)&&is_array($legacy_data);
        if($valid)mirrortalk_elementor_audit($post_id,'legacy_snapshot_recovered',array('snapshot_version'=>$legacy_version));
    }
    if(!$valid)return new WP_Error('snapshot_mismatch',__('The migration snapshot failed its integrity check.','astra-child'));
    $result=wp_update_post(wp_slash(array('ID'=>$post_id,'post_content'=>(string)$snapshot['content'])),true); if(is_wp_error($result))return $result;
    update_post_meta($post_id,'_elementor_data',wp_slash((string)$snapshot['elementor_data']));
    if($snapshot['edit_mode']!=='')update_post_meta($post_id,'_elementor_edit_mode',$snapshot['edit_mode']); else delete_post_meta($post_id,'_elementor_edit_mode');
    if($snapshot['template']!=='')update_post_meta($post_id,'_wp_page_template',$snapshot['template']);
    update_post_meta($post_id,'_elementor_page_settings',$snapshot['page_settings']);delete_post_meta($post_id,'_mirrortalk_elementor_migrated');delete_post_meta($post_id,'_mirrortalk_elementor_provisional');
    clean_post_cache($post_id);do_action('litespeed_purge_url',get_permalink($post_id));if(!$internal)mirrortalk_elementor_job_update($post_id,'restored',array('next_stage'=>'','last_error'=>''));mirrortalk_elementor_audit($post_id,'restored',array('internal'=>$internal?'yes':'no'));return true;
}

function mirrortalk_elementor_verify_migration($post_id){
    mirrortalk_elementor_process_stage(absint($post_id),'live');
}
add_action('mirrortalk_elementor_verify_migration',function($post_id){mirrortalk_runtime_run('elementor_verify_'.absint($post_id),function()use($post_id){return mirrortalk_elementor_verify_migration($post_id);},5*MINUTE_IN_SECONDS);},10,1);
add_action('mirrortalk_elementor_migrate_async',function($post_id){$post_id=absint($post_id);if(!$post_id)return;$result=mirrortalk_elementor_queue_document($post_id,'manual');update_post_meta($post_id,'_mirrortalk_elementor_async_result',array('time'=>time(),'status'=>is_wp_error($result)?'failed':'queued','message'=>is_wp_error($result)?$result->get_error_message():''));},10,1);

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
    elseif($action==='retry'&&current_user_can('edit_post',$post_id)){delete_post_meta($post_id,'_mirrortalk_elementor_candidate');delete_transient('mirrortalk_elementor_preview_'.$post_id);$result=mirrortalk_elementor_queue_document($post_id,'manual-retry');$message=is_wp_error($result)?'error:'.$result->get_error_message():'document-retry-queued';}
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
    $snapshot=array('time'=>time(),'status'=>'running','summary'=>$previous['summary']??array('pending'=>0,'queued'=>0,'quarantined'=>0,'stale'=>0,'migrated'=>0,'total'=>0,'pending_scan'=>true),'residual'=>$previous['residual']??array('templates'=>0,'shortcodes'=>0,'pending'=>true),'items'=>$previous['items']??array());
    update_option('mirrortalk_elementor_dashboard_snapshot',$snapshot,false);
    $snapshot['summary']=mirrortalk_elementor_migration_counts(true);
    update_option('mirrortalk_elementor_dashboard_snapshot',$snapshot,false);
    $snapshot['items']=mirrortalk_elementor_dashboard_items(100,0);
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

function mirrortalk_elementor_template_references($template_id){
    global $wpdb;$template_id=absint($template_id);if(!$template_id)return array('referenced'=>true,'reasons'=>array('invalid_id'));
    $reasons=array();$conditions=get_post_meta($template_id,'_elementor_conditions',true);
    if((is_array($conditions)&&$conditions)||(!is_array($conditions)&&trim((string)$conditions)!==''))$reasons[]='theme_builder_conditions';
    $shortcode_patterns=array('%[elementor-template id="'.$template_id.'"%','%[elementor-template id='.$template_id.'%','%[elementor-template id=\''.$template_id.'\'%');
    foreach($shortcode_patterns as$pattern){if((int)$wpdb->get_var($wpdb->prepare("SELECT COUNT(ID) FROM {$wpdb->posts} WHERE ID<>%d AND post_status NOT IN ('trash','auto-draft') AND post_content LIKE %s",$template_id,$pattern))>0){$reasons[]='shortcode_reference';break;}}
    $json_patterns=array('%"template_id":"'.$template_id.'"%','%"template_id":'.$template_id.'%','%"popup_id":"'.$template_id.'"%','%"popup_id":'.$template_id.'%');
    foreach($json_patterns as$pattern){if((int)$wpdb->get_var($wpdb->prepare("SELECT COUNT(meta_id) FROM {$wpdb->postmeta} WHERE post_id<>%d AND meta_key='_elementor_data' AND meta_value LIKE %s",$template_id,$pattern))>0){$reasons[]='elementor_data_reference';break;}}
    return array('referenced'=>!empty($reasons),'reasons'=>array_values(array_unique($reasons)));
}

function mirrortalk_elementor_retire_templates(){
    $templates=get_posts(array('post_type'=>'elementor_library','post_status'=>array('publish','future','private'),'numberposts'=>-1));$snapshots=(array)get_option('mirrortalk_elementor_template_snapshots',array());$retired=0;$protected=0;
    foreach($templates as$template){
        $references=mirrortalk_elementor_template_references($template->ID);
        if(!empty($references['referenced'])){mirrortalk_elementor_audit($template->ID,'template_retirement_deferred',array('reasons'=>$references['reasons']));$protected++;continue;}
        if(!isset($snapshots[$template->ID]))$snapshots[$template->ID]=array('status'=>$template->post_status,'content'=>$template->post_content,'data'=>get_post_meta($template->ID,'_elementor_data',true),'time'=>time());
        $result=wp_update_post(array('ID'=>$template->ID,'post_status'=>'draft'),true);if(!is_wp_error($result)){$retired++;mirrortalk_elementor_audit($template->ID,'template_retired',array('verified_unreferenced'=>'yes'));}
    }
    update_option('mirrortalk_elementor_template_snapshots',$snapshots,false);update_option('mirrortalk_elementor_template_retirement_summary',array('time'=>time(),'retired'=>$retired,'protected'=>$protected),false);return$retired;
}

function mirrortalk_elementor_restore_templates(){
    $snapshots=(array)get_option('mirrortalk_elementor_template_snapshots',array());$restored=0;foreach($snapshots as$id=>$snapshot){$result=wp_update_post(array('ID'=>absint($id),'post_status'=>sanitize_key($snapshot['status']??'draft'),'post_content'=>(string)($snapshot['content']??'')),true);if(is_wp_error($result))continue;update_post_meta(absint($id),'_elementor_data',$snapshot['data']??'');$restored++;}if($restored)delete_option('mirrortalk_elementor_template_snapshots');return$restored;
}

function mirrortalk_elementor_resolve_residuals(){
    $result=array('expanded'=>mirrortalk_elementor_expand_template_shortcodes(),'retired'=>mirrortalk_elementor_retire_templates());
    delete_transient('mirrortalk_elementor_residual_dependencies');
    $result['remaining']=mirrortalk_elementor_residual_dependencies(true);
    mirrortalk_runtime_queue('mirrortalk_elementor_dashboard_refresh',array(),15);
    return$result;
}
add_action('mirrortalk_elementor_resolve_residuals_async',function(){$result=mirrortalk_runtime_run('elementor_residuals','mirrortalk_elementor_resolve_residuals',20*MINUTE_IN_SECONDS);update_option('mirrortalk_elementor_last_residual_result',array('time'=>time(),'result'=>$result),false);});
add_action('mirrortalk_elementor_restore_templates_async',function(){$restored=mirrortalk_runtime_run('elementor_template_restore','mirrortalk_elementor_restore_templates',20*MINUTE_IN_SECONDS);update_option('mirrortalk_elementor_last_template_restore',array('time'=>time(),'restored'=>$restored),false);});

/**
 * Repair only failure modes for which the engine has a deterministic remedy.
 * Unknown failures remain quarantined and can never be silently published.
 */
function mirrortalk_elementor_repair_quarantined($limit=5){
    global $wpdb;$limit=max(1,min(10,absint($limit)));$repaired=0;
    $ids=$wpdb->get_col($wpdb->prepare("SELECT pm.post_id FROM {$wpdb->postmeta} pm INNER JOIN {$wpdb->posts} p ON p.ID=pm.post_id WHERE pm.meta_key='_mirrortalk_elementor_job' AND pm.meta_value LIKE %s AND p.post_status NOT IN ('trash','auto-draft') ORDER BY pm.post_id ASC LIMIT %d",'%quarantined%',$limit));
    foreach((array)$ids as$post_id){
        $post_id=absint($post_id);$job=(array)get_post_meta($post_id,'_mirrortalk_elementor_job',true);if(($job['status']??'')!=='quarantined')continue;
        if((string)get_post_meta($post_id,'_mirrortalk_elementor_repair_version',true)===MIRRORTALK_ELEMENTOR_MIGRATION_VERSION)continue;
        update_post_meta($post_id,'_mirrortalk_elementor_repair_version',MIRRORTALK_ELEMENTOR_MIGRATION_VERSION);
        $error=strtolower((string)($job['last_error']??''));$stage=sanitize_key((string)($job['failed_stage']??''));
        if(strpos($error,'heading_level_jump')!==false&&trim((string)get_post_meta($post_id,'_elementor_data',true))!==''){
            delete_post_meta($post_id,'_mirrortalk_elementor_candidate');delete_transient('mirrortalk_elementor_preview_'.$post_id);
            $result=mirrortalk_elementor_queue_document($post_id,'automatic-repair-heading');if(!is_wp_error($result)){$repaired++;continue;}
        }
        if($stage==='live'&&strpos($error,'snapshot failed its integrity check')!==false){
            $provisional=(array)get_post_meta($post_id,'_mirrortalk_elementor_provisional',true);
            if($provisional&&stripos((string)get_post_field('post_content',$post_id),'data-mt-owned-migration=')!==false){
                mirrortalk_elementor_job_update($post_id,'retry_wait',array('attempts'=>0,'last_error'=>'','failed_stage'=>'','next_stage'=>'live','retry_at'=>time()+5,'repair'=>'legacy_snapshot_recheck'));
                mirrortalk_elementor_schedule_stage($post_id,'live',5);$repaired++;continue;
            }
        }
        mirrortalk_elementor_audit($post_id,'automatic_repair_skipped',array('reason'=>$error?:'unknown_failure'));
    }
    return$repaired;
}

function mirrortalk_elementor_auto_batch(){
    if(!get_option('mirrortalk_elementor_auto_migration')||get_transient('mt_elementor_auto_lock'))return;set_transient('mt_elementor_auto_lock',1,10*MINUTE_IN_SECONDS);$processed=0;$failed=0;
    $repaired=mirrortalk_elementor_repair_quarantined(5);
    foreach(mirrortalk_elementor_inventory(50,0,false)as$item){if($processed>=1)break;$job=(array)($item['job']??array());$state=(string)($job['status']??'');if(in_array($state,array('quarantined','queued','preparing','preview_verifying','preview_verified','committing','live_verifying','retry_wait'),true))continue;if(!in_array($item['readiness'],array('ready','adaptable','pending'),true))continue;$result=mirrortalk_elementor_queue_document($item['id'],'automatic');if(is_wp_error($result)){$failed++;mirrortalk_elementor_fail_stage($item['id'],'queue',$result,false);}else$processed++;}
    $log=(array)get_option('mirrortalk_elementor_migration_log',array());$log[]=array('time'=>time(),'processed'=>$processed,'repaired'=>$repaired,'failed'=>$failed);update_option('mirrortalk_elementor_migration_log',array_slice($log,-100),false);
    $counts=mirrortalk_elementor_migration_counts(true);$remaining=((int)($counts['pending']??0)+(int)($counts['queued']??0))>0;
    delete_transient('mt_elementor_auto_lock');if($remaining){if(!wp_next_scheduled('mirrortalk_elementor_auto_batch'))wp_schedule_single_event(time()+5*MINUTE_IN_SECONDS,'mirrortalk_elementor_auto_batch');return;}if((int)($counts['quarantined']??0)>0){update_option('mirrortalk_elementor_auto_migration',0,false);update_option('mirrortalk_elementor_auto_attention',array('time'=>time(),'reason'=>'quarantined_documents','count'=>(int)$counts['quarantined']),false);return;}
    $residual=mirrortalk_elementor_resolve_residuals();$remaining_residual=(array)($residual['remaining']??array());
    update_option('mirrortalk_elementor_auto_migration',0,false);
    if((int)($remaining_residual['templates']??0)===0&&(int)($remaining_residual['shortcodes']??0)===0)update_option('mirrortalk_elementor_auto_completed',time(),false);
    else update_option('mirrortalk_elementor_auto_attention',array('time'=>time(),'reason'=>'referenced_templates_remain','count'=>(int)($remaining_residual['templates']??0)),false);
}
add_action('mirrortalk_elementor_auto_batch',function(){mirrortalk_runtime_run('elementor_auto_batch','mirrortalk_elementor_auto_batch',15*MINUTE_IN_SECONDS);});

function mirrortalk_elementor_recover_schedule(){if(get_option('mirrortalk_elementor_auto_migration')&&!wp_next_scheduled('mirrortalk_elementor_auto_batch'))wp_schedule_single_event(time()+MINUTE_IN_SECONDS,'mirrortalk_elementor_auto_batch');}
add_action('init','mirrortalk_elementor_recover_schedule',80);

/** Recover document stages after cron loss, PHP termination or a host restart. */
function mirrortalk_elementor_recover_documents(){
    if(get_transient('mt_elementor_recovery_scan'))return;set_transient('mt_elementor_recovery_scan',1,15*MINUTE_IN_SECONDS);
    $ids=get_posts(array('post_type'=>array('post','page'),'post_status'=>array('publish','draft','future','private'),'numberposts'=>25,'fields'=>'ids','meta_key'=>'_mirrortalk_elementor_job','orderby'=>'modified','order'=>'ASC'));
    foreach($ids as$post_id){$job=(array)get_post_meta($post_id,'_mirrortalk_elementor_job',true);$state=(string)($job['status']??'');$stage=sanitize_key((string)($job['next_stage']??''));if(!$stage||in_array($state,array('migrated','quarantined','restored'),true))continue;$retry_at=(int)($job['retry_at']??0);$delay=$retry_at>time()?max(5,$retry_at-time()):5;mirrortalk_elementor_schedule_stage($post_id,$stage,$delay);}
}
add_action('init','mirrortalk_elementor_recover_documents',90);

/** Empty edit-mode flags are historical debris, not migration work. */
function mirrortalk_elementor_cleanup_stale_metadata(){
    global $wpdb;$ids=$wpdb->get_col("SELECT DISTINCT p.ID FROM {$wpdb->posts} p INNER JOIN {$wpdb->postmeta} em ON em.post_id=p.ID AND em.meta_key='_elementor_edit_mode' LEFT JOIN {$wpdb->postmeta} ed ON ed.post_id=p.ID AND ed.meta_key='_elementor_data' WHERE p.post_type IN ('post','page') AND p.post_status NOT IN ('trash','auto-draft') AND (ed.meta_id IS NULL OR TRIM(ed.meta_value) IN ('','[]','{}','null')) LIMIT 250");
    foreach((array)$ids as$post_id){delete_post_meta($post_id,'_elementor_edit_mode');delete_post_meta($post_id,'_elementor_css');mirrortalk_elementor_audit($post_id,'stale_metadata_removed');}return count($ids);
}
add_action('mirrortalk_elementor_cleanup_stale',function(){mirrortalk_runtime_run('elementor_stale_cleanup','mirrortalk_elementor_cleanup_stale_metadata',10*MINUTE_IN_SECONDS);});

function mirrortalk_elementor_upgrade_bootstrap(){
    if(get_option('mirrortalk_elementor_migration_release')===MIRRORTALK_ELEMENTOR_MIGRATION_VERSION)return;
    update_option('mirrortalk_elementor_migration_release',MIRRORTALK_ELEMENTOR_MIGRATION_VERSION,false);update_option('mirrortalk_elementor_auto_migration',1,false);
    if(!wp_next_scheduled('mirrortalk_elementor_cleanup_stale'))wp_schedule_single_event(time()+20,'mirrortalk_elementor_cleanup_stale');if(!wp_next_scheduled('mirrortalk_elementor_dashboard_refresh'))wp_schedule_single_event(time()+30,'mirrortalk_elementor_dashboard_refresh');if(!wp_next_scheduled('mirrortalk_elementor_auto_batch'))wp_schedule_single_event(time()+MINUTE_IN_SECONDS,'mirrortalk_elementor_auto_batch');
}
add_action('after_setup_theme','mirrortalk_elementor_upgrade_bootstrap',50);

function mirrortalk_elementor_migration_page(){
    if(!current_user_can('manage_options'))return;
    // Guaranteed-fast shell: no content queries, JSON decoding, scans, remote
    // requests or cron loopbacks are permitted during this page request.
    $snapshot=(array)get_option('mirrortalk_elementor_dashboard_snapshot',array());
    $summary=is_array($snapshot['summary']??null)?$snapshot['summary']:array('pending'=>0,'queued'=>0,'quarantined'=>0,'stale'=>0,'migrated'=>0,'total'=>0,'pending_scan'=>true);
    $residual=is_array($snapshot['residual']??null)?$snapshot['residual']:array('templates'=>0,'shortcodes'=>0,'pending'=>true);
    $items=is_array($snapshot['items']??null)?$snapshot['items']:array();
    $safe=!empty($snapshot['time'])&&empty($summary['pending_scan'])&&(int)$summary['pending']===0&&(int)($summary['queued']??0)===0&&(int)($summary['quarantined']??0)===0&&empty($residual['pending'])&&$residual['templates']===0&&$residual['shortcodes']===0;
    $notice=sanitize_text_field(rawurldecode((string)($_GET['mt_notice']??'')));
    echo '<div class="wrap"><h1>'.esc_html__('Elementor Migration Centre','astra-child').'</h1><p>'.esc_html__('Convert Elementor documents into fast, semantic and fully owned Mirror Talk content. Every migration creates a checksum-protected snapshot and remains individually reversible.','astra-child').'</p>';
    if($notice)echo '<div class="notice '.(strpos($notice,'error:')===0?'notice-error':'notice-success').' is-dismissible"><p>'.esc_html($notice).'</p></div>';
    echo '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin:24px 0">';foreach(array(array(__('Pending','astra-child'),$summary['pending']??0),array(__('In progress','astra-child'),$summary['queued']??0),array(__('Verified migrated','astra-child'),$summary['migrated']??0),array(__('Quarantined','astra-child'),$summary['quarantined']??0),array(__('Ignored stale metadata','astra-child'),$summary['stale']??0))as$card)echo'<div class="card"><h2>'.esc_html($card[0]).'</h2><p style="font-size:28px;margin:8px 0">'.esc_html(!empty($summary['pending_scan'])?__('Refreshing…','astra-child'):(string)$card[1]).'</p></div>';echo'</div>';
    echo '<div class="card" style="max-width:none"><h2>'.esc_html__('Elementor deactivation gate','astra-child').'</h2><p><strong>'.esc_html($safe?__('SAFE TO DEACTIVATE','astra-child'):__('NOT YET SAFE','astra-child')).'</strong></p><p>'.esc_html($safe?__('No active documents, templates or template shortcodes depend on Elementor. Complete visual and form checks before uninstalling the plugin.','astra-child'):(!empty($summary['pending_scan'])||!empty($residual['pending'])?__('Dependency counts and residual template checks are refreshing safely in the background. Keep Elementor active until the gate has complete results.','astra-child'):sprintf(__('%1$d documents, %2$d Elementor templates and %3$d template shortcodes still require attention. Keep the plugin active.','astra-child'),$summary['pending'],$residual['templates'],$residual['shortcodes']))).'</p></div>';
    echo '<p><a class="button button-secondary" href="'.esc_url(mirrortalk_elementor_action_url('refresh_status')).'">'.esc_html__('Refresh migration status safely','astra-child').'</a> <span class="description">'.esc_html__('The scan runs after this page responds. Reload later to see its cached result.','astra-child').'</span></p>';
    $automatic=(bool)get_option('mirrortalk_elementor_auto_migration');echo'<div class="card" style="max-width:none"><h2>'.esc_html__('Automatic migration','astra-child').'</h2><p>'.esc_html($automatic?__('Running one document per guarded background batch to protect production performance.','astra-child'):__('Paused. Start it when the staging snapshot and backup are ready.','astra-child')).'</p><p><a class="button '.($automatic?'':'button-primary').'" href="'.esc_url(mirrortalk_elementor_action_url($automatic?'auto_stop':'auto_start')).'">'.esc_html($automatic?__('Pause automatic migration','astra-child'):__('Start automatic owned-content migration','astra-child')).'</a></p></div>';
    if($summary['pending']===0&&($residual['templates']||$residual['shortcodes']))echo'<p><a class="button button-secondary" href="'.esc_url(mirrortalk_elementor_action_url('resolve_residuals')).'">'.esc_html__('Queue template-shortcode conversion and template retirement','astra-child').'</a></p>';
    if(get_option('mirrortalk_elementor_template_snapshots'))echo'<p><a href="'.esc_url(mirrortalk_elementor_action_url('restore_templates')).'">'.esc_html__('Restore retired Elementor templates','astra-child').'</a></p>';
    if($summary['pending'])echo'<p><a class="button button-primary" href="'.esc_url(mirrortalk_elementor_action_url('batch')).'">'.esc_html__('Queue the next safe migration batch','astra-child').'</a> <span class="description">'.esc_html__('Work runs outside this browser request in small resumable batches.','astra-child').'</span></p>';
    echo '<h2>'.esc_html__('Exact queue and failure state','astra-child').'</h2><table class="widefat striped"><thead><tr><th>'.esc_html__('Content','astra-child').'</th><th>'.esc_html__('State','astra-child').'</th><th>'.esc_html__('Attempts / next stage','astra-child').'</th><th>'.esc_html__('Failure detail','astra-child').'</th><th>'.esc_html__('Actions','astra-child').'</th></tr></thead><tbody>';
    foreach($items as$item){$job=(array)($item['job']??array());$state=(string)($job['status']??$item['readiness']);$candidate=mirrortalk_elementor_candidate($item['id']);echo'<tr><td><strong>'.esc_html($item['title']).'</strong><br><small>'.esc_html($item['type'].' #'.$item['id']).'</small></td><td><strong>'.esc_html($state).'</strong><br><small>'.esc_html(!empty($job['updated'])?wp_date('Y-m-d H:i:s',(int)$job['updated']):'—').'</small></td><td>'.esc_html((int)($job['attempts']??0).' / '.((string)($job['next_stage']??'—'))).(!empty($job['retry_at'])?'<br><small>'.esc_html(sprintf(__('Retry %s','astra-child'),wp_date('Y-m-d H:i:s',(int)$job['retry_at']))).'</small>':'').'</td><td>'.esc_html((string)($job['last_error']??'—')).(!empty($job['failed_stage'])?'<br><small>'.esc_html(sprintf(__('Stage: %s','astra-child'),$job['failed_stage'])).'</small>':'').'</td><td><a href="'.esc_url($item['url']).'" target="_blank" rel="noopener">'.esc_html__('View','astra-child').'</a>';
        if(!empty($candidate['token']))echo' · <a href="'.esc_url(mirrortalk_elementor_preview_url($item['id'])).'" target="_blank" rel="noopener">'.esc_html__('Preview conversion','astra-child').'</a>';
        if($state==='quarantined')echo' · <a href="'.esc_url(mirrortalk_elementor_action_url('retry',$item['id'])).'">'.esc_html__('Retry only this document','astra-child').'</a>';elseif(!$item['migrated']&&!in_array($state,array('queued','preparing','preview_ready','preview_verifying','preview_verified','committing','live_verifying','retry_wait'),true))echo' · <a href="'.esc_url(mirrortalk_elementor_action_url('migrate',$item['id'])).'">'.esc_html__('Queue migration','astra-child').'</a>';
        if($item['migrated']||get_post_meta($item['id'],'_mirrortalk_elementor_snapshot',true))echo' · <a href="'.esc_url(mirrortalk_elementor_action_url('restore',$item['id'])).'">'.esc_html__('Restore original','astra-child').'</a>';echo'</td></tr>';}
    if(!$items)echo'<tr><td colspan="5">'.esc_html__('No active Elementor documents or migration jobs were found.','astra-child').'</td></tr>';echo'</tbody></table>';
    $audit=array_reverse((array)get_option('mirrortalk_elementor_audit_log',array()));echo'<h2>'.esc_html__('Complete migration audit log','astra-child').'</h2><p class="description">'.esc_html(sprintf(__('Showing the newest %1$d of %2$d retained events.','astra-child'),min(200,count($audit)),count($audit))).'</p><table class="widefat striped"><thead><tr><th>'.esc_html__('Time','astra-child').'</th><th>'.esc_html__('Document','astra-child').'</th><th>'.esc_html__('Event','astra-child').'</th><th>'.esc_html__('Details','astra-child').'</th></tr></thead><tbody>';foreach(array_slice($audit,0,200)as$entry)echo'<tr><td>'.esc_html(wp_date('Y-m-d H:i:s',(int)($entry['time']??0))).'</td><td>'.esc_html('#'.(int)($entry['post_id']??0)).'</td><td>'.esc_html((string)($entry['event']??'')).'</td><td><code>'.esc_html(wp_json_encode($entry['details']??array())).'</code></td></tr>';if(!$audit)echo'<tr><td colspan="4">'.esc_html__('No migration actions have been recorded yet.','astra-child').'</td></tr>';echo'</tbody></table>';
    echo'</div>';
}
