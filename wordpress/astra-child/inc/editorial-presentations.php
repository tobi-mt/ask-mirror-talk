<?php
/** Content-led archive and feature presentation modes. */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_EDITORIAL_PRESENTATIONS_VERSION','1.0.0');

function mirrortalk_editorial_profile($post_id) {
    $explicit=sanitize_key((string)get_post_meta($post_id,'_mt_rss_article_tier',true));
    if(in_array($explicit,array('compact','editorial','deep-dive'),true))return $explicit;
    $result=(array)get_post_meta($post_id,'_mt_composer_v2_result',true);$words=absint($result['source_words']??0);
    if(!$words)$words=str_word_count(wp_strip_all_tags(strip_shortcodes((string)get_post_field('post_content',$post_id))));
    if($words<650)return 'compact';if($words>=1500)return 'deep-dive';return 'editorial';
}

function mirrortalk_is_major_conversation($post_id) {
    if(get_post_meta($post_id,'_mt_featured_conversation',true)==='1'||is_sticky($post_id))return true;
    $result=(array)get_post_meta($post_id,'_mt_composer_v2_result',true);
    return has_post_thumbnail($post_id)&&mirrortalk_editorial_profile($post_id)==='deep-dive'&&(int)($result['score']??0)>=85;
}

function mirrortalk_editorial_card_data($post_id,$index=0) {
    $profile=mirrortalk_editorial_profile($post_id);$major=mirrortalk_is_major_conversation($post_id);$topic=function_exists('mirrortalk_resolve_topic_context')?mirrortalk_resolve_topic_context($post_id):array();
    $result=(array)get_post_meta($post_id,'_mt_composer_v2_result',true);$words=absint($result['source_words']??0);if(!$words)$words=str_word_count(wp_strip_all_tags(strip_shortcodes((string)get_post_field('post_content',$post_id))));
    $evidence=(array)get_post_meta($post_id,'_mt_rss_evidence',true);$duration=trim((string)($evidence['duration']??''));
    $role=$index===0?'lead':($index===1?'supporting':'standard');
    return array('profile'=>$profile,'presentation'=>$major?'cinematic':$profile,'role'=>$major?'feature':$role,'major'=>$major,'topic'=>(string)($topic['label']??__('Conversation','astra-child')),'minutes'=>max(1,(int)ceil($words/220)),'duration'=>$duration,'is_episode'=>(bool)get_post_meta($post_id,'_mt_rss_audio_url',true),'has_transcript'=>(bool)get_post_meta($post_id,'_mt_rss_transcript_url',true));
}

function mirrortalk_render_editorial_card($post_id,$index=0,$heading_level='h2') {
    $post=get_post($post_id);if(!$post)return;$data=mirrortalk_editorial_card_data($post_id,$index);$heading=in_array($heading_level,array('h2','h3'),true)?$heading_level:'h2';$class='mt-editorial-card mt-editorial-card--'.$data['presentation'].' mt-editorial-card--'.$data['role'];
    $image_args=array('class'=>'mt-editorial-card__image','decoding'=>'async');if($data['presentation']==='cinematic'){$image_args['loading']='eager';$image_args['fetchpriority']='high';}else$image_args['loading']='lazy';
    ?>
    <article <?php post_class($class,$post_id); ?> data-editorial-profile="<?php echo esc_attr($data['profile']); ?>">
        <a class="mt-editorial-card__link" href="<?php echo esc_url(get_permalink($post_id)); ?>">
            <span class="mt-editorial-card__visual">
                <?php if(function_exists('mirrortalk_document_visual'))echo mirrortalk_document_visual($post_id,$data['presentation']==='cinematic'?'large':'medium_large',$image_args);elseif(has_post_thumbnail($post_id))echo get_the_post_thumbnail($post_id,'medium_large',$image_args); ?>
                <?php if($data['is_episode']): ?><span class="mt-editorial-card__play" aria-hidden="true">▶</span><?php endif; ?>
            </span>
            <span class="mt-editorial-card__content">
                <span class="mt-editorial-card__eyebrow"><?php echo esc_html($data['topic']); ?> · <?php echo esc_html(get_the_date('', $post_id)); ?></span>
                <<?php echo tag_escape($heading); ?> class="mt-editorial-card__title"><?php echo esc_html(get_the_title($post_id)); ?></<?php echo tag_escape($heading); ?>>
                <span class="mt-editorial-card__excerpt"><?php echo esc_html(wp_trim_words(get_the_excerpt($post_id),$data['presentation']==='cinematic'?38:24,'…')); ?></span>
                <span class="mt-editorial-card__footer"><span><?php echo esc_html(sprintf(_n('%s min read','%s min read',$data['minutes'],'astra-child'),number_format_i18n($data['minutes']))); ?><?php echo $data['duration']?' · '.esc_html($data['duration']):''; ?><?php echo $data['has_transcript']?' · '.esc_html__('Transcript','astra-child'):''; ?></span><strong><?php echo esc_html($data['is_episode']?__('Listen and explore','astra-child'):__('Read and reflect','astra-child')); ?> →</strong></span>
            </span>
        </a>
    </article>
    <?php
}
