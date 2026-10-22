"""Static release gates for the WordPress Listen Everywhere module."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1] / "wordpress" / "astra-child"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_route_is_distinct_from_episode_archive():
    module = read("inc/listen-everywhere.php")
    navigation = read("inc/navigation.php")
    assert "^listen/?$" in module
    assert "index.php?mirror_listen=1" in module
    assert "home_url('/listen/')" in navigation
    assert "podcast-episodes" in navigation


def test_public_registry_is_guarded():
    module = read("inc/listen-everywhere.php")
    assert "verified_native" in module
    assert "verified_web" in module
    assert "rss_capable" in module
    assert "in_array($platform['status']" in module
    # Review candidates must ship without fabricated destinations.
    assert "'status'=>'unverified'" in module
    assert "'enabled'=>0" in module


def test_one_registry_drives_all_public_surfaces():
    required = {
        "footer.php": "mirrortalk_listen_platforms(true)",
        "inc/listen-and-connect.php": "mirrortalk_render_platform_cards('dialog')",
        "page-templates/mirror-talk-home.php": "mirrortalk_render_listen_invitation('home')",
        "single.php": "mirrortalk_render_listen_invitation('episode')",
        "listen.php": "mirrortalk_render_platform_cards('directory')",
    }
    for path, marker in required.items():
        assert marker in read(path), f"{path} is not connected to the registry"


def test_accessible_no_autoplay_player():
    template = read("listen.php")
    assert '<h1 id="mt-listen-title">' in template
    assert "<audio controls" in template
    assert "autoplay" not in template.lower()
    assert "aria-labelledby" in template


def test_seo_discovery_owns_listen_route():
    seo = read("inc/intelligence-seo.php")
    platform = read("inc/seo-platform.php")
    assert "get_query_var('mirror_listen')" in seo
    assert "home_url('/listen/')" in seo
    assert "Listen to Mirror Talk" in platform


def test_privacy_safe_client_behavior():
    script = read("listen-everywhere.js")
    assert "geolocation" not in script
    assert "fingerprint" not in script.lower()
    assert "mt_preferred_listen_platform" in script
    assert "listen_platform_selected" in script
    assert "window.location" not in script


def test_mobile_and_reduced_motion_rules_exist():
    css = read("mirror-talk-site.css")
    assert "@media(max-width:620px)" in css
    assert "prefers-reduced-motion:reduce" in css
    assert ".mt-listen-platforms" in css


def test_theme_release_changed():
    style = read("style.css")
    match = re.search(r"^Version:\s+(.+)$", style, re.MULTILINE)
    assert match and tuple(map(int, match.group(1).strip().split('.'))) >= (8, 17, 5)


def test_intelligence_parent_is_registered_before_children():
    dashboard = read("inc/intelligence-dashboard.php")
    listen = read("inc/listen-everywhere.php")
    composer = read("inc/editorial-composer-v2.php")
    taxonomy = read("inc/guarded-taxonomy.php")

    assert "'mirror-talk-intelligence',\n        __('Mirror Talk Intelligence'" in dashboard
    assert "add_action('admin_menu', 'mirrortalk_intelligence_admin_menu', 5)" in dashboard
    assert "add_action('admin_menu', 'mirrortalk_listen_admin_menu', 20)" in listen
    assert "mirrortalk_composer_v2_admin_page');},20);" in composer
    assert "mirrortalk_taxonomy_settings_page');},20);" in taxonomy


def test_feed_cache_hot_path_is_read_only():
    feed = read("inc/listen-and-connect.php")
    cached_branch = feed.split("$last_good =", 1)[0]
    assert "update_option" not in cached_branch
    assert "return array_slice($cached, 0, $limit);" in cached_branch


def test_recurring_schedule_recovery_does_not_run_on_public_init():
    modules = {
        "inc/intelligence-dashboard.php": "mirrortalk_intelligence_schedule_cleanup",
        "inc/intelligence-seo.php": "mirrortalk_intelligence_schedule_weekly_report",
        "inc/knowledge-quality.php": "mirrortalk_quality_schedule_guardian",
        "inc/listen-everywhere.php": "mirrortalk_listen_schedule_health_check",
        "inc/seo-platform.php": "mirrortalk_seo_schedule_events",
        "inc/editorial-composer-v2.php": "mirrortalk_composer_v2_schedule_backfill",
    }
    for path, callback in modules.items():
        source = read(path)
        assert f"add_action('admin_init', '{callback}'" in source or f"add_action('admin_init','{callback}'" in source
        assert f"add_action('init', '{callback}'" not in source
        assert f"add_action('init','{callback}'" not in source


def test_dashboard_snapshot_has_short_lived_query_cache():
    dashboard = read("inc/intelligence-dashboard.php")
    assert "get_transient($cache_key)" in dashboard
    assert "set_transient($cache_key, $snapshot, 3 * MINUTE_IN_SECONDS)" in dashboard


def test_owned_surfaces_drop_plugin_assets_they_do_not_render():
    functions = read("functions.php")
    assert "get_query_var('mirror_listen')" in functions
    assert "get_query_var('mirror_blog')" in functions
    assert "get_query_var('mirror_topic')" in functions
    assert "'hostinger-reach-embed'" in functions
    assert "'contact-form-7'" in functions


def test_legacy_iframes_receive_a_non_fabricated_accessible_name():
    normalizer = read("inc/content-normalizer.php")
    assert "<iframe\\b(?![^>]*\\btitle=)" in normalizer
    assert "Embedded media" in normalizer


def test_quality_dashboard_caps_the_initial_issue_table():
    quality = read("inc/knowledge-quality.php")
    assert "array_slice((array)($quality['issues']??array()),0,50)" in quality
    assert "Showing the first %2$d of %3$d ranked issues" in quality


def test_content_only_singular_pages_drop_global_form_runtime():
    functions = read("functions.php")
    assert "function mirrortalk_streamline_singular_form_assets()" in functions
    assert "'mc4wp' =>" in functions
    assert "if (!$uses['hostinger'])" in functions
    assert "if (!$uses['mc4wp'] && !$uses['wpforms'] && !$uses['sureforms'])" in functions
    assert "'prosopo-procaptcha'" in functions
    assert "'hostinger-reach-embed'" in functions


def test_private_admin_paths_are_excluded_from_journey_analytics():
    browser = read("intelligence.js")
    backend = read("inc/intelligence-dashboard.php")
    assert "wp-admin|wp-login\\.php" in browser
    assert "wp-admin|wp-login\\.php" in backend
    assert "destination_path NOT LIKE '/wp-admin%'" in backend


def test_legacy_youtube_widgets_receive_a_click_to_load_guard():
    functions = read("functions.php")
    guard = read("legacy-video-guard.js")
    assert "mirrortalk_enqueue_legacy_video_guard" in functions
    assert "get_post_meta($post_id, '_elementor_data', true)" in functions
    assert "'\"widgetType\":\"video\"'" in functions
    assert "youtube-nocookie.com/embed/" in guard
    assert "elementor-widget-video[data-settings]" in guard
    assert "autoplay=1" in guard


def test_elementor_migration_is_guarded_reversible_and_owned():
    functions = read("functions.php")
    migration = read("inc/elementor-migration.php")
    assert "inc/elementor-migration.php" in functions
    assert "_mirrortalk_elementor_snapshot" in migration
    assert "hash_equals" in migration
    assert "mirrortalk_elementor_restore" in migration
    assert "mirrortalk_elementor_residual_dependencies" in migration
    assert "elementor_library" in migration
    assert "[elementor-template" in migration
    assert "SAFE TO DEACTIVATE" in migration


def test_elementor_migration_rejects_unknown_widgets_and_preserves_urls():
    migration = read("inc/elementor-migration.php")
    assert "$unsupported[$type]" in migration
    assert "'readiness'=>" in migration
    assert "wp_update_post(wp_slash(array('ID'=>$post_id,'post_content'" in migration
    assert "post_name" not in migration
    assert "guid" not in migration
    assert "mirrortalk_indexnow_queue_url" in migration


def test_elementor_conversion_uses_semantic_privacy_first_components():
    migration = read("inc/elementor-migration.php")
    assert "<!-- wp:heading" in migration
    assert "<!-- wp:image" in migration
    assert "[mirror_talk_video" in migration
    assert "mirrortalk_story_studio_video" in migration
    assert "mirrortalk_composer_v2_run($post_id,true)" in migration
    supported = migration.split("function mirrortalk_elementor_supported_widgets", 1)[1].split("}", 1)[0]
    assert "'html'" in supported
    assert "mirrortalk_elementor_convert_custom_html" in migration


def test_elementor_migration_has_zero_review_fallback_path():
    migration = read("inc/elementor-migration.php")
    assert "'adaptable'" in migration
    assert "mirrortalk_elementor_generic_fallback" in migration
    assert "invalid_elementor_data_recovered" in migration
    assert "owned_contact_form" in migration
    assert "owned_newsletter_form" in migration
    assert "iframe_to_safe_link" in migration
    assert "script_removed_content_preserved" in migration


def test_owned_slider_is_accessible_and_motion_aware():
    migration = read("inc/elementor-migration.php")
    script = read("owned-widgets.js")
    css = read("mirror-talk-site.css")
    assert "data-mt-owned-slider" in migration
    assert "aria-roledescription" in migration
    assert "prefers-reduced-motion: reduce" in script
    assert "visibilitychange" in script
    assert ".mt-owned-slider" in css


def test_elementor_templates_and_shortcodes_can_be_retired_and_restored():
    migration = read("inc/elementor-migration.php")
    assert "mirrortalk_elementor_expand_template_shortcodes" in migration
    assert "mirrortalk_elementor_retire_templates" in migration
    assert "mirrortalk_elementor_restore_templates" in migration
    assert "mirrortalk_elementor_template_snapshots" in migration


def test_migration_intelligence_is_resumable_verified_and_self_recovering():
    migration = read("inc/elementor-migration.php")
    assert "mirrortalk_elementor_auto_batch" in migration
    assert "mirrortalk_elementor_recover_schedule" in migration
    assert "mt_elementor_stage_" in migration
    assert "mirrortalk_elementor_conversion_quality" in migration
    assert "low_text_retention" in migration
    assert "mirrortalk_elementor_verify_migration" in migration
    assert "render_failure" in migration
    assert "mirrortalk_elementor_restore($post_id,true)" in migration
    assert "delete_post_meta($post_id,'_elementor_data')" in migration


def test_owned_form_adapter_uses_intent_and_never_collects_payments():
    migration = read("inc/elementor-migration.php")
    assert "mirrortalk_elementor_form_adapter" in migration
    assert "owned_newsletter_form" in migration
    assert "owned_contact_form" in migration
    assert "payment_form_to_verified_destination" in migration
    assert "https://www.patreon.com/MirrorTalk" in migration


def test_primary_buttons_cannot_inherit_low_contrast_link_colour():
    css = read("mirror-talk-site.css")
    assert "color: #fff !important;" in css
    assert "color: #fffaf3 !important;" in css


def test_trust_pages_have_a_dedicated_non_composer_surface():
    functions = read("functions.php")
    template = read("page.php")
    composer = read("inc/editorial-composer-v2.php")
    youtube = read("inc/youtube-studio.php")
    css = read("mirror-talk-site.css")
    assert "function mirrortalk_is_trust_page" in functions
    assert "'corrections', 'editorial-standards'" in functions
    assert "mt-page--trust" in template
    assert "mt-trust-document" in template
    assert "mirrortalk_is_trust_page($post_id)" in composer
    assert "mirrortalk_is_trust_page()" in youtube
    assert ".mt-trust-layout" in css
    assert "@media(max-width:820px)" in css


def test_elementor_dashboard_is_bounded_paginated_and_non_blocking():
    migration = read("inc/elementor-migration.php")
    assert "function mirrortalk_elementor_inventory($limit = 50, $offset = 0, $include_migrated = true)" in migration
    assert "min(100,max(1,absint($limit)))" in migration
    assert "function mirrortalk_elementor_migration_counts($force = false)" in migration
    assert "mirrortalk_elementor_count_scan" in migration
    assert "$snapshot['items']=mirrortalk_elementor_dashboard_items(100,0)" in migration
    assert "mirrortalk_elementor_resolve_residuals_async" in migration
    assert "mirrortalk_elementor_restore_templates_async" in migration
    assert "migration-batch-queued" in migration
    assert "function mirrortalk_elementor_dashboard_items" in migration
    assert "EXISTS (SELECT 1 FROM {$wpdb->postmeta}" in migration
    assert "mirrortalk_elementor_residual_scan" in migration
    assert "mirrortalk_elementor_dashboard_refresh" in migration
    page_function = migration.split("function mirrortalk_elementor_migration_page", 1)[1]
    assert "mirrortalk_elementor_inventory($per_page" not in page_function
    assert "mirrortalk_elementor_conversion($preview)" not in page_function
    assert "mirrortalk_elementor_migration_counts()" not in page_function
    assert "mirrortalk_elementor_dashboard_items(" not in page_function
    assert "mirrortalk_elementor_residual_dependencies()" not in page_function


def test_runtime_queue_never_spawns_loopback_http_from_admin_request():
    runtime = read("inc/runtime-resilience.php")
    queue = runtime.split("function mirrortalk_runtime_queue", 1)[1].split("function mirrortalk_runtime_status", 1)[0]
    assert "wp_schedule_single_event" in queue
    assert "spawn_cron(" not in queue


def test_topic_detection_cannot_recurse_through_excerpt_content_filters():
    journey = read("inc/journey.php")
    resolver = journey.split("function mirrortalk_resolve_topic_context", 1)[1].split("function mirrortalk_topic_rewrite_rules", 1)[0]
    bridge = journey.split("function mirrortalk_append_reflection_bridge", 1)[1].split("add_filter('the_content'", 1)[0]
    assert "get_the_excerpt(" not in resolver
    assert "post_excerpt" in resolver
    assert "static $rendering = false" in bridge


def test_runtime_logs_are_size_bounded():
    runtime = read("inc/runtime-resilience.php")
    assert "substr(sanitize_text_field($detail), 0, 500)" in runtime
    assert "mirrortalk_runtime_prune_log_once" in runtime
    assert "Maximum call stack size" in runtime


def test_elementor_snapshot_commits_progress_before_residual_scan():
    migration = read("inc/elementor-migration.php")
    refresh = migration.split("function mirrortalk_elementor_refresh_dashboard_snapshot", 1)[1].split("add_action('mirrortalk_elementor_dashboard_refresh'", 1)[0]
    assert refresh.count("update_option('mirrortalk_elementor_dashboard_snapshot'") >= 4
    assert "mirrortalk_elementor_migration_counts(true)" in refresh
    assert "mirrortalk_elementor_dashboard_items(100,0)" in refresh
    assert "mirrortalk_elementor_residual_dependencies(true)" not in refresh


def test_runtime_resilience_contains_slow_and_failed_jobs():
    runtime = read("inc/runtime-resilience.php")
    functions = read("functions.php")
    quality = read("inc/knowledge-quality.php")
    platform = read("inc/seo-platform.php")
    assert "function mirrortalk_runtime_run" in runtime
    assert "function mirrortalk_runtime_queue" in runtime
    assert "catch (Throwable $error)" in runtime
    assert "register_shutdown_function" in runtime
    assert "runtime-resilience.php" in functions
    assert "mirrortalk_intelligence_artifacts_refresh" in quality
    assert "get_transient('mirrortalk_command_centre')" in quality
    assert "array_slice($keys, $cursor, 8)" in platform
    assert "crawl-queued" in platform


def test_frontend_feeds_never_wait_for_remote_services():
    podcast = read("inc/listen-and-connect.php")
    youtube = read("inc/youtube-studio.php")
    assert "if (!$force_refresh)" in podcast
    assert "mirrortalk_runtime_run('podcast_feed'" in podcast
    assert "if (!$force_refresh)" in youtube
    assert "mirrortalk_runtime_run('youtube_feed'" in youtube
