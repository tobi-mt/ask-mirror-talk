<?php
/**
 * Mirror Talk Page-One Growth.
 *
 * Converts verified search and first-party content signals into a ranked,
 * reversible work queue. Factual enrichment is always review-led; URLs,
 * quotations, credentials and source material are never generated here.
 */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_PAGE_ONE_VERSION', '1.0.0');

function mirrortalk_page_one_normalize_query($query) {
    return strtolower(trim(preg_replace('/\s+/', ' ', sanitize_text_field((string) $query))));
}

function mirrortalk_page_one_high_intent($query) {
    $query = mirrortalk_page_one_normalize_query($query);
    if (!$query) return false;
    if (preg_match('/^(?:how|why|what|when|where|which|who|can|should|does|do|is|are)\b/i', $query)) return true;
    if (preg_match('/\b(?:ways|steps|signs|meaning|guide|help|tips|questions|overcome|improve|build|find|learn)\b/i', $query)) return true;
    $tokens = preg_split('/[^a-z0-9]+/', remove_accents($query), -1, PREG_SPLIT_NO_EMPTY);
    $stop = array('a','an','and','for','from','in','of','on','or','the','to','with');
    return count(array_diff($tokens, $stop)) >= 4;
}

function mirrortalk_page_one_search_rows($days = 90) {
    $cutoff = gmdate('Y-m-d', time() - max(28, absint($days)) * DAY_IN_SECONDS);
    return array_values(array_filter((array) get_option('mirrortalk_search_performance', array()), function ($row) use ($cutoff) {
        return in_array(($row['engine'] ?? ''), array('google', 'bing'), true)
            && !empty($row['query']) && !empty($row['page']) && ($row['date'] ?? '') >= $cutoff;
    }));
}

function mirrortalk_page_one_profile($post_id) {
    $post = get_post($post_id);
    if (!$post || $post->post_status !== 'publish') return array();
    $content = (string) $post->post_content;
    $plain = wp_strip_all_tags(strip_shortcodes($content));
    $knowledge = function_exists('mirrortalk_knowledge_profile') ? mirrortalk_knowledge_profile($post_id) : array();
    $internal = 0;
    if (preg_match_all('/<a\b[^>]*href=["\']([^"\']+)/i', $content, $links)) {
        $host = wp_parse_url(home_url('/'), PHP_URL_HOST);
        foreach ($links[1] as $link) if (!$host || wp_parse_url($link, PHP_URL_HOST) === $host || strpos($link, '/') === 0) $internal++;
    }
    $has_video = (bool) preg_match('/(?:youtube(?:-nocookie)?\.com|youtu\.be|mt-story-video)/i', $content . ' ' . get_post_meta($post_id, '_mt_story_video_url', true));
    $has_audio = (bool) preg_match('/(?:<audio\b|mt-story-podcast|spotify\.com\/embed)/i', $content) || (bool) get_post_meta($post_id, '_mt_story_episode_url', true);
    $gaps = array();
    if (str_word_count($plain) < 650) $gaps[] = __('deeper original answer', 'astra-child');
    if (empty($knowledge['questions'])) $gaps[] = __('direct questions answered', 'astra-child');
    if (empty($knowledge['transcript'])) $gaps[] = __('verified transcript', 'astra-child');
    if (empty($knowledge['moments'])) $gaps[] = __('timestamped key moments', 'astra-child');
    if (empty($knowledge['quotes'])) $gaps[] = __('verified quotations', 'astra-child');
    if (empty($knowledge['sources'])) $gaps[] = __('sources and references', 'astra-child');
    if ($internal < 2) $gaps[] = __('contextual internal links', 'astra-child');
    $outreach = array();
    if (!empty($knowledge['guest'])) $outreach[] = sprintf(__('Invite %s to reference the episode source page.', 'astra-child'), $knowledge['guest']);
    foreach (array_slice((array) ($knowledge['sources'] ?? array()), 0, 2) as $source) {
        $source_host = wp_parse_url($source, PHP_URL_HOST);
        if ($source_host) $outreach[] = sprintf(__('Consider a factual resource-link request to %s.', 'astra-child'), $source_host);
    }
    return array(
        'words' => str_word_count($plain), 'internal_links' => $internal, 'gaps' => $gaps,
        'knowledge' => $knowledge, 'has_video' => $has_video, 'has_audio' => $has_audio, 'outreach' => $outreach,
        'channels' => array(
            'Google' => !empty($knowledge['questions']) && str_word_count($plain) >= 650,
            'Bing' => !empty($knowledge['sources']) && str_word_count($plain) >= 500,
            'Video' => $has_video && !empty($knowledge['moments']),
            'Podcast' => $has_audio && (!empty($knowledge['transcript']) || !empty($knowledge['summary'])),
            'AI citations' => !empty($knowledge['sources']) && !empty($knowledge['questions']) && (!empty($knowledge['quotes']) || !empty($knowledge['transcript'])),
        ),
    );
}

function mirrortalk_page_one_trend($post_id, $engine) {
    $url = function_exists('mirrortalk_learning_url') ? mirrortalk_learning_url(get_permalink($post_id)) : '';
    $recent = $previous = 0;
    $recent_cutoff = gmdate('Y-m-d', time() - 28 * DAY_IN_SECONDS);
    $previous_cutoff = gmdate('Y-m-d', time() - 56 * DAY_IN_SECONDS);
    foreach (mirrortalk_page_one_search_rows(60) as $row) {
        if (($row['engine'] ?? '') !== $engine || mirrortalk_learning_url($row['page'] ?? '') !== $url) continue;
        $date = (string) ($row['date'] ?? '');
        if ($date >= $recent_cutoff) $recent += max(0, (int) ($row['clicks'] ?? 0));
        elseif ($date >= $previous_cutoff) $previous += max(0, (int) ($row['clicks'] ?? 0));
    }
    $declining = $previous >= 3 && $recent <= floor($previous * .7);
    return array('recent_clicks'=>$recent, 'previous_clicks'=>$previous, 'declining'=>$declining);
}

function mirrortalk_page_one_aggregate($days = 90) {
    $groups = array();
    foreach (mirrortalk_page_one_search_rows($days) as $row) {
        $query = mirrortalk_page_one_normalize_query($row['query'] ?? '');
        $post_id = url_to_postid(esc_url_raw($row['page'] ?? ''));
        if (!$post_id || !mirrortalk_learning_query_eligible($query, $post_id)) continue;
        $engine = sanitize_key($row['engine'] ?? '');
        $key = $engine . '|' . $query . '|' . $post_id;
        if (!isset($groups[$key])) $groups[$key] = array('engine'=>$engine,'query'=>$query,'post_id'=>$post_id,'clicks'=>0,'impressions'=>0,'position_sum'=>0,'weight'=>0);
        $impressions = max(0, (int) ($row['impressions'] ?? 0));
        $groups[$key]['clicks'] += max(0, (int) ($row['clicks'] ?? 0));
        $groups[$key]['impressions'] += $impressions;
        $groups[$key]['position_sum'] += max(0, (float) ($row['position'] ?? 0)) * max(1, $impressions);
        $groups[$key]['weight'] += max(1, $impressions);
    }
    foreach ($groups as &$group) {
        $group['position'] = $group['weight'] ? $group['position_sum'] / $group['weight'] : 0;
        $group['ctr'] = $group['impressions'] ? $group['clicks'] / $group['impressions'] : 0;
    }
    unset($group);
    return array_values($groups);
}

function mirrortalk_page_one_cannibalization($groups) {
    $queries = array();
    foreach ($groups as $group) {
        if ($group['impressions'] < 3) continue;
        $key = $group['engine'] . '|' . $group['query'];
        $queries[$key][] = $group;
    }
    $result = array();
    foreach ($queries as $key => $pages) {
        $ids = array_values(array_unique(array_column($pages, 'post_id')));
        if (count($ids) < 2) continue;
        usort($pages, function ($a, $b) {
            if ($a['clicks'] !== $b['clicks']) return $b['clicks'] <=> $a['clicks'];
            if ($a['impressions'] !== $b['impressions']) return $b['impressions'] <=> $a['impressions'];
            return $a['position'] <=> $b['position'];
        });
        list($engine, $query) = explode('|', $key, 2);
        $result[$key] = array('engine'=>$engine,'query'=>$query,'winner'=>(int)$pages[0]['post_id'],'pages'=>$ids);
    }
    return $result;
}

function mirrortalk_page_one_build_queue($force = false) {
    $cached = get_transient('mirrortalk_page_one_queue');
    if (!$force && is_array($cached)) return $cached;
    $groups = mirrortalk_page_one_aggregate(90);
    $conflicts = mirrortalk_page_one_cannibalization($groups);
    $items = array();
    foreach ($groups as $group) {
        if ($group['impressions'] < 3 || !mirrortalk_page_one_high_intent($group['query'])) continue;
        $position = (float) $group['position'];
        $profile = mirrortalk_page_one_profile($group['post_id']);
        if (!$profile) continue;
        $trend = mirrortalk_page_one_trend($group['post_id'], $group['engine']);
        $key = $group['engine'] . '|' . $group['query'];
        $action = __('Monitor this opportunity.', 'astra-child');
        if (isset($conflicts[$key])) $action = __('Consolidate competing coverage around the strongest canonical page; editorial approval required.', 'astra-child');
        elseif ($trend['declining']) $action = __('Refresh this declining page with current, verified evidence and direct answers; preserve its URL.', 'astra-child');
        elseif ($position >= 4 && $position <= 20) $action = $profile['gaps'] ? sprintf(__('Strengthen this near-page-one result: add %s.', 'astra-child'), implode(', ', array_slice($profile['gaps'], 0, 3))) : __('Strengthen contextual links and preserve the complete answer.', 'astra-child');
        elseif ($position <= 10 && $group['impressions'] >= 50 && $group['ctr'] < .025) $action = __('Test a clearer intent-aligned search title under the guarded experiment rules.', 'astra-child');
        elseif ($position > 20) $action = __('Build supporting topic coverage and links before changing the title.', 'astra-child');
        $position_factor = ($position >= 4 && $position <= 20) ? 2.2 : (($position > 20 && $position <= 40) ? 1.25 : .8);
        $score = round(log(1 + $group['impressions']) * 18 * $position_factor * max(.35, 1 - $group['ctr']) + min(18, count($profile['gaps']) * 2), 1);
        $items[] = array_merge($group, array(
            'title'=>get_the_title($group['post_id']), 'url'=>get_permalink($group['post_id']),
            'score'=>$score + ($trend['declining'] ? 12 : 0), 'action'=>$action, 'gaps'=>$profile['gaps'], 'channels'=>$profile['channels'], 'trend'=>$trend, 'outreach'=>$profile['outreach'],
            'cannibalization'=>$conflicts[$key] ?? array(),
            'safety'=>isset($conflicts[$key]) ? 'editorial_review' : (($position >= 4 && $position <= 20) ? 'safe_supporting_links' : 'observe'),
        ));
    }
    usort($items, function ($a, $b) { return $b['score'] <=> $a['score']; });
    $queue = array('generated_at'=>time(),'items'=>array_slice($items, 0, 100),'conflicts'=>array_values($conflicts));
    update_option('mirrortalk_page_one_queue', $queue, false);
    set_transient('mirrortalk_page_one_queue', $queue, 12 * HOUR_IN_SECONDS);
    return $queue;
}

function mirrortalk_page_one_snapshot($post_id, $reason) {
    $history = (array) get_post_meta($post_id, '_mirrortalk_page_one_history', true);
    $history[] = array('time'=>time(),'reason'=>sanitize_text_field($reason),'focus'=>(string)get_post_meta($post_id,'_mirrortalk_focus_keyword',true),'evidence'=>get_post_meta($post_id,'_mirrortalk_focus_keyword_evidence',true),'links'=>(array)get_post_meta($post_id,'_mirrortalk_page_one_links',true));
    update_post_meta($post_id, '_mirrortalk_page_one_history', array_slice($history, -20));
}

function mirrortalk_page_one_related_sources($target_id, $limit = 3) {
    $tax_query = array('relation'=>'OR');
    foreach (array('category','post_tag') as $taxonomy) {
        $terms = wp_get_post_terms($target_id, $taxonomy, array('fields'=>'ids'));
        if (!is_wp_error($terms) && $terms) $tax_query[] = array('taxonomy'=>$taxonomy,'field'=>'term_id','terms'=>$terms);
    }
    if (count($tax_query) === 1) return array();
    return get_posts(array('post_type'=>'post','post_status'=>'publish','post__not_in'=>array($target_id),'numberposts'=>$limit,'fields'=>'ids','tax_query'=>$tax_query));
}

function mirrortalk_page_one_apply_safe_improvements($queue = null) {
    $queue = is_array($queue) ? $queue : mirrortalk_page_one_build_queue();
    $applied = 0;
    foreach (array_slice((array) ($queue['items'] ?? array()), 0, 20) as $item) {
        $post_id = absint($item['post_id'] ?? 0);
        if (!$post_id || ($item['safety'] ?? '') !== 'safe_supporting_links' || ($item['impressions'] ?? 0) < 5 || get_post_meta($post_id, '_mirrortalk_seo_auto_lock', true)) continue;
        $changed = false;
        $current_focus = (string) get_post_meta($post_id, '_mirrortalk_focus_keyword', true);
        if ($current_focus !== $item['query']) {
            mirrortalk_page_one_snapshot($post_id, 'verified_search_focus');
            update_post_meta($post_id, '_mirrortalk_focus_keyword', $item['query']);
            update_post_meta($post_id, '_mirrortalk_focus_keyword_evidence', array('updated'=>time(),'engine'=>$item['engine'],'impressions'=>$item['impressions'],'clicks'=>$item['clicks'],'position'=>round($item['position'],1),'source'=>'page_one_growth'));
            $changed = true;
        }
        foreach (mirrortalk_page_one_related_sources($post_id) as $source_id) {
            $links = array_values(array_unique(array_filter(array_map('absint', (array) get_post_meta($source_id, '_mirrortalk_page_one_links', true)))));
            if (in_array($post_id, $links, true)) continue;
            mirrortalk_page_one_snapshot($source_id, 'contextual_link_to_' . $post_id);
            $links[] = $post_id;
            update_post_meta($source_id, '_mirrortalk_page_one_links', array_slice($links, -3));
            $managed = array_values(array_unique(array_filter(array_map('absint', (array) get_post_meta($post_id, '_mirrortalk_page_one_sources', true)))));
            $managed[] = $source_id;
            update_post_meta($post_id, '_mirrortalk_page_one_sources', array_slice(array_values(array_unique($managed)), -10));
            $changed = true;
        }
        if ($changed) $applied++;
    }
    $audit = (array) get_option('mirrortalk_page_one_audit', array());
    $audit[] = array('time'=>time(),'action'=>'safe_cycle','applied'=>$applied,'opportunities'=>count((array)($queue['items'] ?? array())),'conflicts'=>count((array)($queue['conflicts'] ?? array())));
    update_option('mirrortalk_page_one_audit', array_slice($audit, -100), false);
    update_option('mirrortalk_page_one_last_run', time(), false);
    mirrortalk_runtime_queue('mirrortalk_seo_crawl', array(), 45);
    mirrortalk_runtime_queue('mirrortalk_seo_cleanup_broken_links', array(), 90);
    return $applied;
}

function mirrortalk_page_one_cycle() {
    if (get_transient('mirrortalk_page_one_cycle_lock')) return;
    set_transient('mirrortalk_page_one_cycle_lock', 1, 20 * MINUTE_IN_SECONDS);
    $queue = mirrortalk_page_one_build_queue(true);
    mirrortalk_page_one_apply_safe_improvements($queue);
    delete_transient('mirrortalk_page_one_cycle_lock');
}
add_action('mirrortalk_weekly_seo_report', function () { mirrortalk_runtime_queue('mirrortalk_page_one_cycle_manual', array(), 30); }, 30);
add_action('mirrortalk_page_one_cycle_manual', 'mirrortalk_page_one_cycle');

add_action('admin_post_mirrortalk_page_one_run', function () {
    if (!current_user_can('manage_mirrortalk_seo')) wp_die(esc_html__('SEO permission required.', 'astra-child'));
    check_admin_referer('mirrortalk_page_one_run');
    mirrortalk_runtime_queue('mirrortalk_page_one_cycle_manual', array(), 30);
    wp_safe_redirect(admin_url('admin.php?page=mirror-talk-intelligence&mt_job=queued#page-one')); exit;
});

add_action('admin_post_mirrortalk_page_one_restore', function () {
    $post_id = absint($_GET['post_id'] ?? 0);
    if (!$post_id || !current_user_can('edit_post', $post_id)) wp_die(esc_html__('You cannot restore this item.', 'astra-child'));
    check_admin_referer('mirrortalk_page_one_restore_' . $post_id);
    $history = (array) get_post_meta($post_id, '_mirrortalk_page_one_history', true);
    $snapshot = array_pop($history);
    if ($snapshot) {
        $snapshot['focus'] === '' ? delete_post_meta($post_id, '_mirrortalk_focus_keyword') : update_post_meta($post_id, '_mirrortalk_focus_keyword', $snapshot['focus']);
        empty($snapshot['evidence']) ? delete_post_meta($post_id, '_mirrortalk_focus_keyword_evidence') : update_post_meta($post_id, '_mirrortalk_focus_keyword_evidence', $snapshot['evidence']);
        empty($snapshot['links']) ? delete_post_meta($post_id, '_mirrortalk_page_one_links') : update_post_meta($post_id, '_mirrortalk_page_one_links', $snapshot['links']);
        update_post_meta($post_id, '_mirrortalk_page_one_history', $history);
    }
    foreach ((array) get_post_meta($post_id, '_mirrortalk_page_one_sources', true) as $source_id) {
        $links = array_values(array_diff(array_map('absint', (array) get_post_meta($source_id, '_mirrortalk_page_one_links', true)), array($post_id)));
        $links ? update_post_meta($source_id, '_mirrortalk_page_one_links', $links) : delete_post_meta($source_id, '_mirrortalk_page_one_links');
    }
    delete_post_meta($post_id, '_mirrortalk_page_one_sources');
    wp_safe_redirect(admin_url('admin.php?page=mirror-talk-intelligence#page-one')); exit;
});

function mirrortalk_page_one_panel() {
    $queue = (array) get_option('mirrortalk_page_one_queue', array());
    $items = (array) ($queue['items'] ?? array());
    $run = wp_nonce_url(admin_url('admin-post.php?action=mirrortalk_page_one_run'), 'mirrortalk_page_one_run');
    echo '<section id="page-one" class="mti-panel"><header><div><p class="mti-kicker">PAGE-ONE GROWTH</p><h2>' . esc_html__('Evidence-led organic growth queue', 'astra-child') . '</h2><p>' . esc_html__('Attainable, high-intent opportunities are ranked across Google and Bing. Safe metadata and supporting links are reversible; consolidation and factual enrichment remain review-led.', 'astra-child') . '</p></div><a class="button button-primary" href="' . esc_url($run) . '">' . esc_html__('Refresh and apply safe actions', 'astra-child') . '</a></header>';
    echo '<div class="mti-cards mti-cards--compact"><article><small>' . esc_html__('Ranked opportunities', 'astra-child') . '</small><strong>' . esc_html(count($items)) . '</strong><span>' . esc_html__('high-intent only', 'astra-child') . '</span></article><article><small>' . esc_html__('Positions 4–20', 'astra-child') . '</small><strong>' . esc_html(count(array_filter($items, function($i){return ($i['position']??0)>=4&&($i['position']??0)<=20;}))) . '</strong><span>' . esc_html__('closest to page one', 'astra-child') . '</span></article><article><small>' . esc_html__('Cannibalization clusters', 'astra-child') . '</small><strong>' . esc_html(count((array)($queue['conflicts']??array()))) . '</strong><span>' . esc_html__('never merged automatically', 'astra-child') . '</span></article></div>';
    if (!$items) echo '<p class="mti-empty">' . esc_html__('No eligible opportunities yet. Connect and synchronize Google Search Console and Bing Webmaster data, then refresh this queue.', 'astra-child') . '</p>';
    else { echo '<div class="mti-table-wrap"><table class="widefat striped"><thead><tr><th>Priority</th><th>Page and query</th><th>Evidence</th><th>Recommended action</th><th>Channel readiness</th><th>Control</th></tr></thead><tbody>'; foreach (array_slice($items,0,40) as $item) {
        $ready=array(); foreach((array)$item['channels'] as $channel=>$ok)$ready[]=$channel.': '.($ok?'ready':'gap');
        $restore=wp_nonce_url(admin_url('admin-post.php?action=mirrortalk_page_one_restore&post_id='.(int)$item['post_id']),'mirrortalk_page_one_restore_'.(int)$item['post_id']);
        $outreach = !empty($item['outreach']) ? '<br><small>' . esc_html(implode(' ', $item['outreach'])) . '</small>' : '';
        $trend = !empty($item['trend']['declining']) ? ' · ' . __('declining', 'astra-child') : '';
        echo '<tr><td><strong>'.esc_html(number_format_i18n($item['score'],1)).'</strong></td><td><a href="'.esc_url(get_edit_post_link($item['post_id'])).'">'.esc_html($item['title']).'</a><br><small>'.esc_html($item['query']).' · '.esc_html(ucfirst($item['engine'])).'</small></td><td>'.esc_html(sprintf(__('%1$d impressions · %2$d clicks · position %3$s · CTR %4$s%%','astra-child'),$item['impressions'],$item['clicks'],number_format_i18n($item['position'],1),number_format_i18n($item['ctr']*100,1)) . $trend).'</td><td>'.esc_html($item['action']).$outreach.'</td><td>'.esc_html(implode(' · ',$ready)).'</td><td><a href="'.esc_url($restore).'">'.esc_html__('Restore last safe action','astra-child').'</a></td></tr>';
    } echo '</tbody></table></div>'; }
    echo '<p class="description">' . esc_html__('Guardrails: public URLs and visible headlines are never changed here; claims, credentials, quotations, transcripts and backlinks are never fabricated; title experiments retain the existing impression threshold, single-variable test and automatic rollback.', 'astra-child') . '</p></section>';
}

