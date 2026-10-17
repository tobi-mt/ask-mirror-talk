<?php
/** Resilient, observable Intelligence aggregation pipeline. */
if (!defined('ABSPATH')) exit;

define('MIRRORTALK_PIPELINE_VERSION', '1.0.0');

function mirrortalk_pipeline_state() {
    return wp_parse_args((array) get_option('mirrortalk_intelligence_pipeline', array()), array(
        'version'=>MIRRORTALK_PIPELINE_VERSION,'requested_at'=>0,'completed_at'=>0,
        'status'=>'waiting','stages'=>array(),'message'=>'',
    ));
}

function mirrortalk_pipeline_set_stage($stage, $status, $detail = '') {
    $state=mirrortalk_pipeline_state();
    $state['version']=MIRRORTALK_PIPELINE_VERSION;
    $state['stages'][sanitize_key($stage)]=array('status'=>sanitize_key($status),'time'=>time(),'detail'=>substr(sanitize_text_field((string)$detail),0,300));
    $states=wp_list_pluck($state['stages'],'status');
    $required=array('quality','recommendations','knowledge');
    if(in_array('failed',$states,true))$state['status']='attention';
    else {
        $complete=true;
        foreach($required as $required_stage)if(($state['stages'][$required_stage]['status']??'')!=='complete'){$complete=false;break;}
        if($complete){$state['status']='healthy';$state['completed_at']=time();}
        else $state['status']='running';
    }
    update_option('mirrortalk_intelligence_pipeline',$state,false);
}

function mirrortalk_pipeline_request($source='scheduled') {
    $state=array('version'=>MIRRORTALK_PIPELINE_VERSION,'requested_at'=>time(),'completed_at'=>0,'status'=>'queued','source'=>sanitize_key($source),'stages'=>array(),'message'=>'');
    update_option('mirrortalk_intelligence_pipeline',$state,false);
    mirrortalk_runtime_queue('mirrortalk_intelligence_quality_stage',array(),2);
    mirrortalk_runtime_queue('mirrortalk_intelligence_recommendations_stage',array(),12);
    mirrortalk_runtime_queue('mirrortalk_intelligence_knowledge_stage',array(),22);
    return $state;
}

function mirrortalk_pipeline_run_stage($stage,$callback) {
    mirrortalk_pipeline_set_stage($stage,'running');
    $result=mirrortalk_runtime_run('intelligence_'.$stage,$callback,20*MINUTE_IN_SECONDS);
    if(is_wp_error($result)){mirrortalk_pipeline_set_stage($stage,'failed',$result->get_error_message());return $result;}
    $detail=is_array($result)?wp_json_encode(array_intersect_key($result,array_flip(array('checked','counts')))):'';
    mirrortalk_pipeline_set_stage($stage,'complete',$detail?:__('Artifact refreshed.','astra-child'));
    return $result;
}

add_action('mirrortalk_intelligence_quality_stage',function(){mirrortalk_pipeline_run_stage('quality',function(){return mirrortalk_quality_scan(true);});});
add_action('mirrortalk_intelligence_recommendations_stage',function(){mirrortalk_pipeline_run_stage('recommendations',function(){return mirrortalk_command_recommendations(30,true);});});
add_action('mirrortalk_intelligence_knowledge_stage',function(){mirrortalk_pipeline_run_stage('knowledge',function(){$graph=mirrortalk_knowledge_graph();set_transient('mirrortalk_knowledge_graph_cache',$graph,12*HOUR_IN_SECONDS);return array('checked'=>count($graph['episodes']),'counts'=>array('entities'=>count($graph['entities']),'relationships'=>count($graph['relationships'])));});});

/** Requeue only missing/failed stages; completed artifacts remain available. */
function mirrortalk_pipeline_watchdog() {
    if(get_transient('mirrortalk_pipeline_watchdog_lock'))return;
    set_transient('mirrortalk_pipeline_watchdog_lock',1,5*MINUTE_IN_SECONDS);
    $state=mirrortalk_pipeline_state();$requested=(int)($state['requested_at']??0);
    if(!$requested||$state['status']==='healthy'||$requested>time()-3*MINUTE_IN_SECONDS)return;
    foreach(array('quality','recommendations','knowledge') as $index=>$stage){
        $row=(array)($state['stages'][$stage]??array());
        if(($row['status']??'')==='complete')continue;
        if(($row['status']??'')==='running'&&(int)($row['time']??0)>time()-20*MINUTE_IN_SECONDS)continue;
        $hook='mirrortalk_intelligence_'.$stage.'_stage';
        if(!wp_next_scheduled($hook))mirrortalk_runtime_queue($hook,array(),3+$index*10);
    }
    mirrortalk_runtime_request_dispatch();
}
add_action('admin_init','mirrortalk_pipeline_watchdog',95);

function mirrortalk_pipeline_health() {
    global $wpdb;$state=mirrortalk_pipeline_state();$table=function_exists('mirrortalk_intelligence_table')?mirrortalk_intelligence_table():'';
    $table_ok=$table&&$wpdb->get_var($wpdb->prepare('SHOW TABLES LIKE %s',$table))===$table;
    $last_event=$table_ok?(string)$wpdb->get_var("SELECT MAX(occurred_at) FROM {$table}"):'';$cron=array();
    foreach(array('mirrortalk_intelligence_quality_stage','mirrortalk_intelligence_recommendations_stage','mirrortalk_intelligence_knowledge_stage') as $hook){$next=wp_next_scheduled($hook);if($next)$cron[$hook]=$next;}
    return array('state'=>$state,'table_ok'=>$table_ok,'last_event'=>$last_event,'scheduled'=>$cron,'fresh'=>!empty($state['completed_at'])&&(int)$state['completed_at']>time()-DAY_IN_SECONDS);
}

function mirrortalk_pipeline_health_panel() {
    $health=mirrortalk_pipeline_health();$state=$health['state'];$label=$state['status']==='healthy'&&$health['fresh']&&$health['table_ok']?'Healthy':ucfirst((string)$state['status']);
    echo '<section class="mti-panel" id="pipeline"><header><div><p class="mti-kicker">SYSTEM HEALTH</p><h2>'.esc_html__('Intelligence pipeline','astra-child').'</h2><p>'.esc_html__('Collection, aggregation and derived artifacts are monitored independently so one failed stage cannot hide or block the others.','astra-child').'</p></div></header>';
    echo '<div class="mti-cards mti-cards--compact"><article><small>Pipeline</small><strong>'.esc_html($label).'</strong><span>'.esc_html(!empty($state['completed_at'])?sprintf(__('Completed %s','astra-child'),wp_date('j M Y H:i',$state['completed_at'])):__('Awaiting a complete run','astra-child')).'</span></article><article><small>Event storage</small><strong>'.esc_html($health['table_ok']?'Ready':'Attention').'</strong><span>'.esc_html($health['last_event']?sprintf(__('Last event %s UTC','astra-child'),$health['last_event']):__('No event recorded yet','astra-child')).'</span></article><article><small>Recovery</small><strong>'.esc_html($health['scheduled']?'Scheduled':'Standing by').'</strong><span>'.esc_html__('Failed or stale stages retry without blocking admin requests.','astra-child').'</span></article></div>';
    $rows=array();foreach(array('quality','recommendations','knowledge') as $stage){$row=(array)($state['stages'][$stage]??array());$rows[]=array('stage'=>ucfirst($stage),'status'=>ucfirst($row['status']??'waiting'),'updated'=>!empty($row['time'])?wp_date('j M Y H:i',$row['time']):'—','detail'=>$row['detail']??'');}
    mirrortalk_intelligence_table_view($rows,array('stage'=>'Stage','status'=>'Status','updated'=>'Updated','detail'=>'Detail'));echo '</section>';
}
