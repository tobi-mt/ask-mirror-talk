<?php
/** Shared containment for expensive background work. */
if (!defined('ABSPATH')) exit;

function mirrortalk_runtime_record($job, $status, $detail = '') {
    $log = (array) get_option('mirrortalk_runtime_log', array());
    $detail = substr(sanitize_text_field($detail), 0, 500);
    $log[] = array('time'=>time(), 'job'=>sanitize_key($job), 'status'=>sanitize_key($status), 'detail'=>$detail);
    update_option('mirrortalk_runtime_log', array_slice($log, -50), false);
    update_option('mirrortalk_runtime_' . sanitize_key($job), end($log), false);
}

/** Remove historic oversized stack traces from the autoloaded runtime log. */
function mirrortalk_runtime_prune_log_once() {
    if (get_option('mirrortalk_runtime_log_format') === '3') return;
    $clean = array();
    foreach (array_slice((array)get_option('mirrortalk_runtime_log',array()),-50) as $row) {
        if (!is_array($row)) continue;
        $row['detail']=substr(sanitize_text_field((string)($row['detail']??'')),0,500);
        if (($row['job']??'')==='php_shutdown' && stripos($row['detail'],'Maximum call stack size')!==false) continue;
        $clean[]=$row;
    }
    update_option('mirrortalk_runtime_log',$clean,false);
    update_option('mirrortalk_runtime_log_format','3',false);
}
add_action('admin_init','mirrortalk_runtime_prune_log_once',2);

function mirrortalk_runtime_run($job, $callback, $lock_seconds = 900) {
    $job = sanitize_key($job); $lock = 'mt_runtime_' . $job;
    if (get_transient($lock)) return new WP_Error('runtime_job_locked', __('This background task is already running.', 'astra-child'));
    set_transient($lock, time(), max(60, absint($lock_seconds)));
    $started = microtime(true); mirrortalk_runtime_record($job, 'running');
    try {
        $result = call_user_func($callback);
        mirrortalk_runtime_record($job, is_wp_error($result) ? 'failed' : 'complete', is_wp_error($result) ? $result->get_error_message() : sprintf('%.2fs', microtime(true)-$started));
        return $result;
    } catch (Throwable $error) {
        mirrortalk_runtime_record($job, 'failed', $error->getMessage());
        return new WP_Error('runtime_job_failed', $error->getMessage());
    } finally {
        delete_transient($lock);
    }
}

function mirrortalk_runtime_queue($hook, $args = array(), $delay = 5) {
    $args = array_values((array) $args);
    if (!wp_next_scheduled($hook, $args)) wp_schedule_single_event(time() + max(1, absint($delay)), $hook, $args);
    // Never open a loopback HTTP connection from an admin/editor request.
    // WordPress or the host cron will dispatch the scheduled event later.
    return true;
}

function mirrortalk_runtime_status($job) {
    return (array) get_option('mirrortalk_runtime_' . sanitize_key($job), array());
}

/** Dispatch queued work after the response; never make editors wait for it. */
function mirrortalk_runtime_request_dispatch() {
    $GLOBALS['mirrortalk_runtime_dispatch_requested'] = true;
}

add_action('shutdown', function () {
    if (empty($GLOBALS['mirrortalk_runtime_dispatch_requested'])) return;
    if (function_exists('spawn_cron')) { spawn_cron(time()); return; }
    wp_remote_post(site_url('wp-cron.php?doing_wp_cron=' . rawurlencode(sprintf('%.22F', microtime(true)))), array(
        'timeout' => 0.01, 'blocking' => false,
        'sslverify' => apply_filters('https_local_ssl_verify', false),
    ));
}, 1000);

add_action('admin_notices', function () {
    if (!current_user_can('manage_options') || strpos(sanitize_key($_GET['page'] ?? ''), 'mirror-talk') !== 0) return;
    if (defined('DISABLE_WP_CRON') && DISABLE_WP_CRON) echo '<div class="notice notice-warning"><p><strong>'.esc_html__('Background processing requires the host cron.','astra-child').'</strong> '.esc_html__('WP-Cron is disabled; confirm that the hosting control panel calls wp-cron.php at least every five minutes.','astra-child').'</p></div>';
    if (($_GET['mt_job'] ?? '') === 'queued') echo '<div class="notice notice-info is-dismissible"><p><strong>'.esc_html__('Work queued safely.','astra-child').'</strong> '.esc_html__('You may leave this page; the job will continue in the background.','astra-child').'</p></div>';
    $log = array_reverse((array) get_option('mirrortalk_runtime_log', array()));
    foreach ($log as $row) {
        if (($row['status']??'') !== 'failed' || (int)($row['time']??0) < time()-DAY_IN_SECONDS) continue;
        echo '<div class="notice notice-warning"><p><strong>'.esc_html__('A background task needs attention:','astra-child').'</strong> '.esc_html(ucwords(str_replace('_',' ',(string)($row['job']??'')))).'. '.esc_html(substr((string)($row['detail']??''),0,300)).' '.esc_html__('Public pages and editor saves were not interrupted.','astra-child').'</p></div>';
        break;
    }
});

register_shutdown_function(function () {
    $error = error_get_last();
    if (!$error || !in_array($error['type'], array(E_ERROR,E_PARSE,E_CORE_ERROR,E_COMPILE_ERROR,E_USER_ERROR), true)) return;
    if (function_exists('mirrortalk_runtime_record')) mirrortalk_runtime_record('php_shutdown', 'failed', basename((string)$error['file']).':'.(int)$error['line'].' '.$error['message']);
});
