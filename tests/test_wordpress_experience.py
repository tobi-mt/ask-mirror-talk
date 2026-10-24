from pathlib import Path


THEME_DIR = Path(__file__).parents[1] / "wordpress" / "astra-child"


def test_heavy_widget_assets_are_scoped_to_widget_pages():
    php = (THEME_DIR / "ask-mirror-talk.php").read_text()

    assert "has_shortcode((string) $post->post_content, 'ask_mirror_talk')" in php
    assert "is_page('ask-mirror-talk')" in php
    assert "if (!$has_widget_shortcode && !$is_widget_page)" in php
    assert "ask-mirror-talk-redesign.css" in php
    assert "array('ask-mirror-talk', 'ask-mirror-talk-premium')" in php


def test_blocked_notifications_are_only_explained_on_request():
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    denied_branch = js.split("if (Notification.permission === 'denied')", 1)[1][:500]
    assert "if (!explicitlyRequested) return;" in denied_branch


def test_onboarding_prefill_updates_dependent_interface():
    js = (THEME_DIR / "ask-mirror-talk-premium.js").read_text()

    assert "input.dispatchEvent(new Event('input', { bubbles: true }))" in js
    assert "Your question is sent securely to the Mirror Talk response service" in js
    assert "optional usage analytics remains off unless you choose to enable it" in js


def test_singular_citation_copy_and_question_coach_are_grammatical():
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    assert "support${count === 1 ? 's' : ''} this reflection" in js
    assert "What is one practical first step to ${howToAction}?" in js
    assert "What is the first step I should take with ${topic}?" not in js


def test_audio_preview_avoids_eager_full_download():
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    assert "previewAudio.preload = 'metadata'" in js


def test_question_events_use_submission_lifecycle_ids():
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    assert "let activeSubmissionId = null;" in js
    assert "activeSubmissionId = createSubmissionId();" in js
    assert "submission_id: activeSubmissionId" in js
    assert "emitProductEvent('question_failed'" in js


def test_pre_answer_events_do_not_inherit_previous_qa_log_id():
    addon = (THEME_DIR / "analytics-addon.js").read_text()

    assert "const POST_ANSWER_EVENTS = new Set" in addon
    assert "const mayInheritCurrentQALogId = POST_ANSWER_EVENTS.has(eventName);" in addon
    assert ": (mayInheritCurrentQALogId ? currentQALogId : null);" in addon
    assert "'question_submitted'" not in addon.split("const POST_ANSWER_EVENTS = new Set", 1)[1].split("]);", 1)[0]


def test_optional_analytics_requires_explicit_consent():
    addon = (THEME_DIR / "analytics-addon.js").read_text()
    php = (THEME_DIR / "ask-mirror-talk.php").read_text()

    assert "amt_analytics_consent_v1" in addon
    assert "if (storedConsent === 'granted')" in addon
    assert "initializeAnalytics();" in addon
    assert 'id="amt-analytics-consent"' in php
    assert "pseudonymous usage analytics" in php


def test_private_reflections_are_not_injected_as_faq_schema():
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    assert "injectFAQSchema" not in js
    assert "amt-faq-schema" not in js


def test_theme_has_editorial_home_and_design_tokens():
    theme_json = (THEME_DIR / "theme.json").read_text()
    site_css = (THEME_DIR / "mirror-talk-site.css").read_text()
    template = (THEME_DIR / "page-templates" / "mirror-talk-home.php").read_text()

    assert '"slug": "coral"' in theme_json
    assert '"contentSize": "760px"' in theme_json
    assert ".mt-home__hero" in site_css
    assert "Template Name: Mirror Talk Editorial Home" in template
    assert "new WP_Query" in template
    assert "mirrortalk_document_visual(get_the_ID(), 'medium_large'" in template
    assert "mt-episode-card__image--fallback" in template
    assert '<span class="mt-episode-card__image" aria-hidden="true"></span>' not in template


def test_living_question_is_resilient_sitewide_and_does_not_restore_page_caching():
    functions = (THEME_DIR / "functions.php").read_text()
    feature = (THEME_DIR / "inc" / "question-of-the-day.php").read_text()
    home = (THEME_DIR / "page-templates" / "mirror-talk-home.php").read_text()
    script = (THEME_DIR / "mirror-talk-site.js").read_text()
    worker = (THEME_DIR / "mirror-talk-push-sw.js").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "inc/question-of-the-day.php" in functions
    assert "mirrortalk_render_question_of_the_day('home')" in home
    assert home.index('mt-topics-title') < home.index('mt-home__living-question') < home.index('mt-latest-title')
    assert "mirrortalk_insert_qotd_after_editorial_opening" in feature
    assert "mirrortalk_qotd_safe_insertion_offset" in feature
    assert "mirrortalk_qotd_word_count" in feature
    assert "$word_count < 250" in feature
    assert "$progress >= .30 && $progress <= .68" in feature
    assert "mt-composer-document" in feature
    assert "!empty($stack[0]['transparent'])" in feature
    assert "return $content . $card" not in feature
    assert "A thoughtful pause" in feature
    assert "if ($context === 'home')" in feature
    assert "data-mt-living-question" in feature
    assert "autoask" in feature
    assert "ask-mirror-talk" in feature and "insights" in feature
    assert "mirror-talk-push-sw.js" in functions
    assert "script.indexOf('/mirror-talk-push-sw.js')" in functions
    assert "/api/push/recover" in script
    assert "/api/question-of-the-day" in script
    assert "data-mt-qotd-reminder" in script
    assert "addEventListener('fetch'" not in worker
    assert "addEventListener('push'" in worker
    assert ".mt-living-question" in css
    assert ".mt-living-question--inline .mt-living-question__content" in css
    assert 'grid-template-areas:"meta action" "theme action" "question action"' in css
    assert ".mt-living-question--inline .mt-living-question__mark{display:none}" in css
    assert "prefers-reduced-motion" in css


def test_owned_link_hub_replaces_third_party_bio_pages():
    functions = (THEME_DIR / "functions.php").read_text()
    route = (THEME_DIR / "inc" / "link-hub.php").read_text()
    template = (THEME_DIR / "link-hub.php").read_text()
    css = (THEME_DIR / "link-hub.css").read_text()
    js = (THEME_DIR / "link-hub.js").read_text()
    seo = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()

    assert "inc/link-hub.php" in functions
    assert "^listen-connect/?$" in route and "mirror_links" in route
    assert "mirror_links_legacy" in route and "301" in route
    assert "mirrortalk_link_hub_connections" in route
    assert "ItemList" in route and "CollectionPage" in route
    assert "data-mt-link-hub-audio" in template
    assert "data-mt-platform-directory" in template
    assert 'data-mt-open-dialog="mt-newsletter-invite"' in template
    assert "data-mt-link-hub-share" in template
    assert "/confessions-book/" in template
    assert "Official Mirror Talk links" in template
    assert "@media(max-width:620px)" in css
    assert "prefers-reduced-motion" in css
    assert "link_hub_action" in js
    assert "navigator.share" in js and "navigator.clipboard.writeText" in js
    assert "home_url('/listen-connect/')" in seo


def test_legacy_editorial_content_is_normalized_without_rewriting_storage():
    functions = (THEME_DIR / "functions.php").read_text()
    normalizer = (THEME_DIR / "inc" / "content-normalizer.php").read_text()
    single = (THEME_DIR / "single.php").read_text()
    page = (THEME_DIR / "page.php").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "inc/content-normalizer.php" in functions
    assert "add_filter('the_content', 'mirrortalk_normalize_editorial_content', 20)" in normalizer
    assert "mirrortalk_semantic_repair_content" in normalizer
    assert "mirrortalk_semantic_repair_paragraph_runs" in normalizer
    assert "mirror-talk:preserve-format" in normalizer
    assert "mirrortalk_autolink_plain_urls" in normalizer
    assert "wp_html_split" in normalizer
    assert "wp_http_validate_url" in normalizer
    assert 'target="_blank" rel="noopener noreferrer external"' in normalizer
    assert "mirrortalk_autolink_is_known_broken" in normalizer
    assert "(?:nbsp|#160|#x0*a0)" in normalizer
    assert ".mt-semantic-chapters" in css
    assert ".mt-semantic-list" in css
    assert ".mt-auto-link" in css
    assert "mt-semantic-list-prose" in normalizer
    assert "count($words) < 24" in normalizer
    assert ".mt-semantic-list-prose" in css
    assert "mirror-talk:preserve-format" in normalizer
    assert "is_singular('post')" in normalizer
    assert "<h2$1>" in normalizer and "</h2>" in normalizer
    assert "&nbsp;|&#160;" in normalizer
    assert "mt-editorial-content" in single
    assert "mt-editorial-content" in page
    assert ".mt-editorial-content table" in css
    assert "overflow-x: auto" in css
    assert "iframe[src*='youtube']" in css
    assert "aspect-ratio: 16 / 9" in css
    assert "container-type: inline-size" in css
    assert "flex-direction: column" in css


def test_world_class_knowledge_and_quality_engine_is_integrated():
    functions = (THEME_DIR / "functions.php").read_text()
    engine = (THEME_DIR / "inc" / "knowledge-quality.php").read_text()
    dashboard = (THEME_DIR / "inc" / "intelligence-dashboard.php").read_text()
    single = (THEME_DIR / "single.php").read_text()
    footer = (THEME_DIR / "footer.php").read_text()
    personalization = (THEME_DIR / "knowledge.js").read_text()
    gate = (Path(__file__).parents[1] / "scripts" / "release_quality_gate.py").read_text()

    assert "inc/knowledge-quality.php" in functions
    assert "mirrortalk_command_post_metrics" in engine
    assert "google_impressions" in engine and "bing_impressions" in engine
    assert "ai_referrals" in engine and "newsletter_subscribed" in engine
    assert "mirrortalk_knowledge_graph" in engine
    assert "knowledge-graph" in engine
    assert "Guest biography (verified)" in engine
    assert "Verified quotations" in engine
    assert "mirrortalk_render_citation_brief" in single
    assert "mirrortalk_quality_guardian_daily" in engine
    for issue in ("broken_link", "broken_embed", "missing_visual", "duplicate_h1", "thin_content", "freshness", "orphan", "mobile_overflow", "accessibility", "invalid_schema", "declining_search", "slow_template", "runtime_failure"):
        assert issue in engine
    assert "#command-centre" in dashboard
    assert "#knowledge" in dashboard and "#quality" in dashboard
    assert "amt_analytics_consent_v1" in personalization
    assert "mt_content_history_v1" in personalization
    assert "safeTopics" in personalization
    assert "ai-citations" in engine
    assert "mirrortalk_seo_crawl" in engine and "mirrortalk_seo_repair_media" in engine
    assert "/editorial-standards/" in footer and "/corrections/" in footer
    assert "visible keyboard focus" in gate and "44px controls" in gate


def test_rss_editorial_pipeline_is_bounded_review_first_and_reversible():
    functions = (THEME_DIR / "functions.php").read_text()
    pipeline = (THEME_DIR / "inc" / "rss-editorial-ingestion.php").read_text()
    story = (THEME_DIR / "inc" / "editorial-story-studio.php").read_text()

    assert "inc/rss-editorial-ingestion.php" in functions
    assert "MIRRORTALK_RSS_INGESTION_BATCH" in pipeline
    assert "mirrortalk_runtime_queue('mirrortalk_rss_ingestion_batch'" in pipeline
    assert "'post_status'=>'draft'" in pipeline
    assert "editorial-review-required" in pipeline
    assert "mirrortalk_composer_v2_run($post_id, true)" in pipeline
    assert "mirrortalk_rss_ingestion_match" in pipeline
    assert "never publishes" in pipeline.lower()
    assert "apply_filters('mirrortalk_story_studio_episode'" in story
    assert "mirrortalk_rss_ingestion_daily" in pipeline
    assert "wp_schedule_event" in pipeline and "'daily'" in pipeline
    assert "mirrortalk_rss_ingestion_review" in pipeline
    assert "mirrortalk_rss_ingestion_publish_if_ready" in pipeline
    assert "source_identity_mismatch" in pipeline
    assert "automatically-published" in pipeline


def test_rss_pipeline_enriches_concise_sources_and_retries_owned_drafts_safely():
    pipeline = (THEME_DIR / "inc" / "rss-editorial-ingestion.php").read_text()
    studio = (THEME_DIR / "inc" / "editorial-story-studio.php").read_text()

    assert "mirror-talk:rss-source-v2" in pipeline
    assert "mirrortalk_rss_ingestion_note_insights" in pipeline
    assert "mirrortalk_rss_ingestion_recompose_owned_draft" in pipeline
    assert "_mt_rss_content_history" in pipeline
    assert "_mt_rss_owned_content_hash" in pipeline
    assert "source_notes_too_thin" not in pipeline
    assert "primary_media_complete" in pipeline
    assert "episode_player_not_ready" in pipeline
    assert "video_companion_not_ready" in pipeline
    assert "mirrortalk_rss_ingestion_enable_media" in pipeline
    assert "mirrortalk_rss_ingestion_upgrade_reconcile" in pipeline
    assert "podcast_audio" in pipeline and "youtube_mode" in pipeline
    assert "mirrortalk_story_studio_ensure_post_media" in studio
    assert "mirrortalk_story_media_backfill" in studio
    assert "post_type IN ('post','page')" in studio and "LIMIT 20" in studio


def test_content_led_editorial_presentations_are_shared_and_responsive():
    functions = (THEME_DIR / "functions.php").read_text()
    presentations = (THEME_DIR / "inc" / "editorial-presentations.php").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()
    single = (THEME_DIR / "single.php").read_text()
    archive_templates = "\n".join((THEME_DIR / name).read_text() for name in ("home.php", "archive.php", "category.php", "topic.php", "search.php"))

    assert "inc/editorial-presentations.php" in functions
    for profile in ("compact", "editorial", "deep-dive"):
        assert profile in presentations
    assert "mirrortalk_is_major_conversation" in presentations
    assert "'lead'" in presentations and "'supporting'" in presentations
    assert "is_sticky" in presentations and "_mt_featured_conversation" in presentations
    assert "mirrortalk_render_editorial_card" in archive_templates
    assert "mt-reading__hero--cinematic" in single
    assert ".mt-editorial-card--cinematic" in css
    assert ".mt-editorial-card--deep-dive" in css
    assert ".mt-editorial-card--lead" in css and ".mt-editorial-card--supporting" in css
    assert "@media(max-width:700px)" in css
    assert "prefers-reduced-motion:reduce" in css


def test_story_video_uses_shared_consent_and_mobile_safe_muted_autoplay():
    script = (THEME_DIR / "editorial-story-studio.js").read_text()
    studio = (THEME_DIR / "inc" / "editorial-story-studio.php").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "mt_external_media_consent_v1" in script
    assert "IntersectionObserver" in script
    assert "mute: '1'" in script
    assert "playsinline: '1'" in script
    assert "iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share'" in script
    assert "button.hidden = true" in script
    assert "button[hidden]{display:none!important}" in css
    assert "Play video" in studio
    assert "Allow privacy-enhanced YouTube once" not in studio
    assert "mirrortalk_latest_youtube_video" in studio
    assert "mirror_talk_video" in studio
    assert "MIRRORTALK_STORY_STUDIO_VERSION', '1.3.2'" in studio
    assert "if(get_post_type($post_id)==='post')$settings['enabled']='1'" in studio
    assert "mirrortalk_story_studio_insert_video($content,$video)" in studio
    assert "post_type IN ('post','page')" in studio
    assert "return $content.$module" in studio
    assert "Starts muted" in studio


def test_intelligence_collects_redacted_internal_search_without_private_reflections():
    engine = (THEME_DIR / "inc" / "knowledge-quality.php").read_text()
    dashboard = (THEME_DIR / "inc" / "intelligence-dashboard.php").read_text()
    browser = (THEME_DIR / "intelligence.js").read_text()

    assert "mirrortalk_intelligence_safe_search_term" in engine
    assert "[email removed]" in engine and "[number removed]" in engine
    assert "internal_search" in dashboard
    assert "search_term varchar(300)" in dashboard
    assert "url.searchParams.get('s')" in browser
    assert "reflection" not in engine.split("mirrortalk_intelligence_safe_search_term", 1)[0]


def test_citation_schema_requires_explicit_editorial_facts():
    engine = (THEME_DIR / "inc" / "knowledge-quality.php").read_text()

    assert "Only publish facts that an editor can verify" in engine
    assert "_mt_guest_bio" not in engine  # keys are generated from an allow-list
    assert "'citation'" in engine
    assert "'subjectOf'" in engine
    assert "PodcastEpisode" in engine
    assert "correction_note" in engine


def test_automatic_editorial_composer_runs_a_guarded_save_pipeline():
    functions = (THEME_DIR / "functions.php").read_text()
    composer = (THEME_DIR / "inc" / "editorial-composer.php").read_text()
    normalizer = (THEME_DIR / "inc" / "content-normalizer.php").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "inc/editorial-composer.php" in functions
    assert "mirrortalk_composer_detect_type" in composer
    for content_type in ("interview", "episode", "reflection", "resource", "article"):
        assert "return '" + content_type + "'" in composer
    assert "mirrortalk_composer_provisional_topic" in composer
    assert "provisional-content" in composer
    assert "verified-search-data" in composer
    assert "mirrortalk_composer_search_title" in composer
    assert "mirrortalk_seo_description_candidate" in composer
    assert "mirrortalk_composer_assign_taxonomy" in composer
    assert "mirrortalk_composer_internal_links" in composer
    assert "mirrortalk_repair_media_alt" in composer
    assert "mirrortalk_indexnow_queue_url" in composer
    assert "_mt_composer_history" in composer
    assert "mirrortalk_composer_rollback" in composer
    assert "mirror_talk_composer" in composer
    assert "preg_replace_callback('/<h([2-6])" in normalizer
    assert ".mt-composer-intro" in css and ".mt-composer-takeaways" in css


def test_composer_does_not_silently_rewrite_editorial_body_or_invent_facts():
    composer = (THEME_DIR / "inc" / "editorial-composer.php").read_text()

    run_body = composer.split("function mirrortalk_composer_run", 1)[1].split("add_action('save_post'", 1)[0]
    assert "wp_update_post" not in run_body
    assert "Stored body copy is never silently rewritten" in composer
    assert "pspell_suggest" in composer
    assert "Editor review" in composer
    assert "mirror-talk:preserve-format" in composer


def test_composer_v2_is_visible_reversible_and_server_rendered():
    functions = (THEME_DIR / "functions.php").read_text()
    composer = (THEME_DIR / "inc" / "editorial-composer-v2.php").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "inc/editorial-composer-v2.php" in functions
    assert "MIRRORTALK_COMPOSER_V2_VERSION" in composer
    assert "mirrortalk_composer_v2_render" in composer
    assert "add_filter('the_content','mirrortalk_composer_v2_render',25)" in composer
    assert "_mt_composer_decisions" in composer
    for action in ("toggle", "approve", "run", "restore"):
        assert "mirrortalk_composer_v2_" + action in composer
    assert "mirror-talk:preserve-format" in composer
    assert "wp_update_post" not in composer
    assert "mirrortalk_composer_v2_backfill" in composer
    assert "topic-rejected" in composer
    assert "mt-composer-lead" in composer and "mt-composer-links" in composer
    assert ".mt-composer-document" in css and ".mt-composer-section" in css


def test_composer_v2_protects_special_flows_and_editorial_material():
    composer = (THEME_DIR / "inc" / "editorial-composer-v2.php").read_text()

    for slug in ("ask-mirror-talk", "contact", "join-us", "insights"):
        assert "'" + slug + "'" in composer
    for protected in ("blockquote", "figure", "pre", "code", "iframe", "audio", "video"):
        assert protected in composer
    assert "confidence'=>'rejected'" in composer
    assert "rtrim" in composer


def test_dark_editorial_system_covers_core_wordpress_views():
    css = (THEME_DIR / "mirror-talk-site.css").read_text()
    script = (THEME_DIR / "mirror-talk-site.js").read_text()

    for template_name in ("home.php", "archive.php", "single.php", "page.php"):
        assert (THEME_DIR / template_name).exists()

    assert "Dark editorial sanctuary" in css
    assert ".mt-library__grid" in css
    assert ".mt-reading__body" in css
    assert "data-mt-slider" in script
    assert "prefers-reduced-motion: reduce" in css
    assert "matchMedia('(prefers-reduced-motion: reduce)')" in script


def test_intelligent_slider_is_adaptive_accessible_and_privacy_first():
    script = (THEME_DIR / "mirror-talk-site.js").read_text()
    template = (THEME_DIR / "page-templates" / "mirror-talk-home.php").read_text()

    assert "data-mt-slider-toggle" not in template
    assert "data-mt-slider-prev" not in template
    assert "data-mt-slider-next" not in template
    assert "data-mt-slider-progress" in template
    assert "data-mt-topic-link" in template
    assert "mt_preferences_v1" in script
    assert "IntersectionObserver" in script
    assert "Math.max(6500, Math.min(11000" in script
    assert "pointerdown" in script and "pointerup" in script
    assert "Your preferences stay in this browser" in script
    assert "geolocation" not in script.lower()
    slider_runtime = script.split("// A cache-free, root-scoped worker", 1)[0]
    assert "fetch(" not in slider_runtime


def test_first_party_intelligence_and_native_seo_system_are_wired():
    php = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()
    js = (THEME_DIR / "intelligence.js").read_text()
    functions = (THEME_DIR / "functions.php").read_text()

    assert "inc/intelligence-seo.php" in functions
    assert "amt_analytics_consent_v1" in js
    assert "site_page_view" in js
    assert "podcast_complete" in (THEME_DIR / "listen-connect.js").read_text()
    assert "largest-contentful-paint" in js
    assert "layout-shift" in js
    assert "durationThreshold" in js
    assert "mirror-talk-sitemap/" in php
    assert "PodcastEpisode" in php
    assert "BreadcrumbList" in php
    assert "og:title" in php and "twitter:card" in php
    assert "mirrortalk_external_seo_active" in php
    assert "mirrortalk_weekly_seo_report" in php


def test_mirror_talk_is_authoritative_and_builds_featured_image_social_cards():
    php = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()

    assert "function mirrortalk_seo_authoritative()" in php
    assert "add_filter('aioseo_disable'" in php
    assert "get_theme_mod('mirrortalk_seo_authoritative', true)" in php
    assert "function mirrortalk_social_image" in php
    assert "get_post_thumbnail_id" in php
    assert 'property=\"og:image:width\"' in php
    assert 'property=\"og:image:height\"' in php
    assert 'property=\"og:image:alt\"' in php
    assert 'name=\"twitter:image\"' in php
    assert "max-image-preview" in php
    assert "xmlns:image" in php
    assert "Shared-link preview" in php
    assert "mirrortalk_seo_conflict_notice" not in functions
    assert "external SEO plugin is active" not in functions


def test_seo_platform_covers_autonomous_discovery_governance_and_integrations():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    core = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()

    assert "inc/seo-platform.php" in functions
    assert "api.indexnow.org/indexnow" in platform
    assert "mirror-talk-news-sitemap/" in platform
    assert "mirror-talk-video-sitemap/" in platform
    assert "^llms\\.txt$" in platform
    assert "the_content_feed" in platform and "the_excerpt_rss" in platform
    assert "mirrortalk_redirects" in platform
    assert "mirrortalk_seo_crawl" in platform
    assert "mirrortalk_seo_history" in platform and "mt_rollback_post" in platform
    assert "mirror_talk_seo" in platform and "manage_mirrortalk_seo" in platform
    assert "mt_author_" in platform and "knowsAbout" in core
    assert "mirrortalk_seo_repair_media" in platform
    assert "mirrortalk_seo_editorial_analysis" in platform
    assert "google-site-verification" in platform
    assert "mirrortalk_search_connectors_sync" in platform
    assert "LocalBusiness" in platform and "WooCommerce" in platform
    assert "mirrortalk_schema_graph" in core and "apply_filters" in core


def test_seo_platform_does_not_fake_external_authorization_or_rank_scrape():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    connectors = (THEME_DIR / "inc" / "search-connectors.php").read_text()
    visibility = (THEME_DIR / "inc" / "ai-visibility.php").read_text()

    assert "never scrapes search result pages" in platform
    assert "Neither metric proves that a generated answer cited Mirror Talk" in visibility
    assert "Google Search Console is not connected" in connectors
    assert "does not have a verified Mirror Talk property" in connectors


def test_ai_visibility_is_first_party_private_bounded_and_not_mislabelled():
    visibility = (THEME_DIR / "inc" / "ai-visibility.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()

    assert "inc/ai-visibility.php" in functions
    assert "OAI-SearchBot" in visibility and "ChatGPT-User" in visibility
    assert "PerplexityBot" in visibility and "Claude-SearchBot" in visibility
    assert "chatgpt.com" in visibility and "gemini.google.com" in visibility
    assert "array_slice($data, -120" in visibility
    assert "HTTP_REFERER" in visibility and "HTTP_USER_AGENT" in visibility
    assert "REMOTE_ADDR" not in visibility and "setcookie" not in visibility
    assert "Bingbot/Googlebot crawls are intentionally not presented as AI use" in visibility
    assert "mirrortalk_ai_visibility_admin_panel" in visibility
    assert "AI-search visibility\nThe platform records citation checks" not in visibility


def test_separate_intelligence_dashboard_is_complete_private_and_exportable():
    dashboard = (THEME_DIR / "inc" / "intelligence-dashboard.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()
    tracking = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()
    admin_js = (THEME_DIR / "intelligence-admin.js").read_text()
    admin_css = (THEME_DIR / "intelligence-admin.css").read_text()

    assert "inc/intelligence-dashboard.php" in functions
    assert "add_menu_page" in dashboard and "Mirror Talk Intelligence" in dashboard
    assert "mirrortalk_intelligence_events" in dashboard and "dbDelta" in dashboard
    assert "rest_url('mirror-talk/v1/intelligence/event')" in tracking
    assert "site_page_view" in dashboard and "COUNT(DISTINCT NULLIF(visitor_hash,''))" in dashboard
    assert "podcast_play" in dashboard and "podcast_complete" in dashboard
    assert "web_vital" in dashboard and "broken_link_seen" in dashboard
    assert "campaign_source" in dashboard and "referrer_host" in dashboard
    assert "previous_path" in dashboard and "destination_path" in dashboard
    assert "device_class" in dashboard and "mirrortalk_intelligence_country" in dashboard
    assert "mirrortalk_search_performance" in dashboard
    assert "mirrortalk_ai_visibility_totals" in dashboard
    assert "mirrortalk_intelligence_export" in dashboard and "text/csv" in dashboard
    assert "mirrortalk_intelligence_weekly_reports" in dashboard
    assert "Generate report now" in dashboard
    assert "REMOTE_ADDR" in dashboard and "visitor_hash" in dashboard
    assert "hash_hmac('sha256', $device_id" in dashboard
    assert "reflection text" in dashboard and "email addresses" in dashboard
    assert "data-mti-filter" in dashboard and "mti-filterable" in admin_js
    assert ".mti-cards" in admin_css and "@media(max-width:600px)" in admin_css


def test_seo_learning_is_evidence_led_bounded_and_reversible():
    learning = (THEME_DIR / "inc" / "seo-learning.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()
    dashboard = (THEME_DIR / "inc" / "intelligence-dashboard.php").read_text()
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()

    assert "inc/seo-learning.php" in functions
    assert "mirrortalk_search_performance" in learning and "engine'] ?? '') === 'google'" in learning
    assert "_mirrortalk_focus_keyword" in learning and "_mirrortalk_focus_keyword_evidence" in learning
    assert "_mirrortalk_meta_title" in learning and "get_the_title($post_id)" in learning
    assert "visible editorial headline" in learning
    assert "$running >= 2" in learning
    assert "baseline['impressions']" in learning and "< 100" in learning
    assert "21 * DAY_IN_SECONDS" in learning and "35 * DAY_IN_SECONDS" in learning
    assert "mirrortalk_learning_significant_ctr_gain" in learning and "$z >= 1.64" in learning
    assert "rolled_back" in learning and "baseline_title" in learning
    assert "mirrortalk_learning_pause_and_restore" in learning
    assert "_mirrortalk_seo_auto_lock" in learning
    assert "editor_override" in learning and "$current_title !==" in learning
    assert "position_weight" in learning
    assert "if ($baseline_title" in learning
    assert "mirrortalk_seo_snapshot" in learning and "mirrortalk_indexnow_queue_url" in learning
    assert "Highest-confidence opportunities" in learning and "Decision history" in learning
    assert "mirrortalk_seo_learning_panel" in dashboard
    assert "focus_keyword" in platform and "learning_status" in platform


def test_seo_learning_rejects_unsafe_navigational_and_irrelevant_queries():
    learning = (THEME_DIR / "inc" / "seo-learning.php").read_text()
    assert "function mirrortalk_learning_query_eligible" in learning
    assert "site|inurl|intitle|allinurl|allintitle" in learning
    assert "porn|pornhub|xxx|sexcam|casino|viagra|cialis" in learning
    assert "mirrortalkpodcast" in learning
    assert "$matches >= $required" in learning
    assert "mirrortalk_learning_query_eligible($query, $post_id)" in learning


def test_search_connectors_use_real_authorization_refresh_and_verified_properties():
    connectors = (THEME_DIR / "inc" / "search-connectors.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()

    assert "inc/search-connectors.php" in functions
    assert "aes-256-gcm" in connectors
    assert "https://accounts.google.com/o/oauth2/v2/auth" in connectors
    assert "https://oauth2.googleapis.com/token" in connectors
    assert "access_type' => 'offline" in connectors
    assert "refresh_token" in connectors
    assert "hash_equals" in connectors
    assert "siteUnverifiedUser" in connectors
    assert "searchAnalytics/query" in connectors
    assert "GetUserSites" in connectors and "GetQueryStats" in connectors
    assert "SubmitFeed" in connectors
    assert "mirrortalk_connector_disconnect" in connectors
    assert "mirrortalk_search_store_engine_rows" in connectors
    assert "Content-Length'] = '0'" in connectors


def test_link_health_distinguishes_broken_from_blocked_or_transient_checks():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    dashboard = (THEME_DIR / "inc" / "intelligence-dashboard.php").read_text()
    assert "function mirrortalk_seo_link_state" in platform
    assert "array(404, 410)" in platform
    assert "401, 403, 405, 406, 408, 409, 423, 425, 429" in platform
    assert "could not resolve host|certificate subject name|ssl certificate problem" in platform
    assert "could not be verified" in platform
    assert "mirrortalk_seo_link_state($row) === 'broken'" in dashboard


def test_safe_seo_automation_repairs_only_high_confidence_internal_links():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    assert "function mirrortalk_seo_internal_repair_target" in platform
    assert "_wp_old_slug" in platform and "mirrortalk_redirects" in platform
    assert "count($matches) === 1" in platform
    assert "mirrortalk_connector_host($url) !== mirrortalk_connector_host(home_url('/'))" in platform
    assert "mirrortalk_seo_repair_definitive_internal_links" in platform
    assert "wp_update_post" in platform and "mirrortalk_link_repair_log" in platform
    assert "verified_replacement" in platform
    assert "repeated_external_failure_unlinked" in platform


def test_visibility_automation_covers_pages_preserves_manual_control_and_is_auditable():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    learning = (THEME_DIR / "inc" / "seo-learning.php").read_text()
    assert "mirrortalk_seo_autofill_metadata" in platform
    assert "_mirrortalk_meta_description" in platform
    assert "_mirrortalk_seo_auto_lock" in platform
    assert "mirrortalk_seo_automation_log" in platform
    assert "Safe automation history" in platform
    assert "mirrortalk_seo_public_post_types()" in learning
    assert "mirrortalk_learning_internal_link_suggestion" in learning
    assert "Relevant internal link" in learning


def test_standard_pages_do_not_render_duplicate_h1_when_content_has_own_hero():
    page = (THEME_DIR / "page.php").read_text()
    assert "$content_has_h1" in page
    assert "preg_match('/<h1\\b/i'" in page
    assert "$show_template_hero=!$is_ask_page&&($is_contact_page||!$content_has_h1)" in page


def test_mobile_ask_dock_yields_to_expanded_living_mirror_player():
    script = (THEME_DIR / "listen-connect.js").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()
    assert "document.body.classList.toggle('mt-listen-open', expanded)" in script
    assert ".mt-listen-open .mt-ask-dock" in css


def test_web_vitals_emit_one_final_page_level_sample():
    intelligence = (THEME_DIR / "intelligence.js").read_text()
    assert "let cls = 0; let lcp = 0; let inp = 0; let vitalsSent = false" in intelligence
    assert "lcp = Math.max(lcp, entry.startTime)" in intelligence
    assert "inp = Math.max(inp, entry.duration || 0)" in intelligence
    assert "const flushVitals" in intelligence
    assert "addEventListener('pagehide', flushVitals" in intelligence


def test_seo_crawler_is_incremental_and_player_storage_failures_are_nonfatal():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    player = (THEME_DIR / "listen-connect.js").read_text()
    window = (THEME_DIR / "listen-window.js").read_text()

    assert "array_slice($keys, $cursor, 8)" in platform
    assert "'timeout' => 3" in platform
    assert "mirrortalk_link_crawl_cursor" in platform
    assert "function_exists('mb_strlen')" in platform
    assert "typeof HTMLDialogElement !== 'undefined'" in player
    assert "const saveAudioState = () => {" in player and "catch (_) {}" in player
    assert "const saveState = () => {" in window and "catch (_) {}" in window


def test_owned_home_blog_and_authoritative_head_do_not_depend_on_wp_configuration():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    seo = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()
    ask = (THEME_DIR / "ask-mirror-talk.php").read_text()

    assert "^blog/?$" in platform and "mirror_blog" in platform
    assert "mirror-talk-home.php" in platform and "is_front_page()" in platform
    assert "mirrortalk_authoritative_head_buffer_start" in platform
    assert "mirrortalk_authoritative_head_buffer_end" in platform
    assert "application/ld\\+json" in platform
    assert "untrailingslashit" in seo and "mirror-talk-sitemap" in seo
    assert "pre_get_document_title" in seo
    assert "home_url('/blog/')" in seo
    assert "mirrortalk_streamline_owned_home_assets" in functions
    assert "jetpack-block-podcast-player" in functions
    assert "<h1>Ask Mirror Talk</h1>" in ask


def test_ask_route_has_one_owned_truthful_onboarding_surface():
    page = (THEME_DIR / "page.php").read_text()
    premium = (THEME_DIR / "ask-mirror-talk-premium.js").read_text()
    intelligence = (THEME_DIR / "intelligence.js").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "do_shortcode('[ask_mirror_talk]')" in page
    init = premium.split("function initializePremiumFeatures()", 1)[1]
    assert "setTimeout(showOnboarding, 500)" not in init
    assert "waitForOnboarding" in intelligence
    assert "mt-consent-pending" in intelligence
    assert ".mt-consent-pending .mt-listen" in css


def test_single_posts_use_intelligent_topic_labels_and_home_images_are_bounded():
    single = (THEME_DIR / "single.php").read_text()
    home = (THEME_DIR / "page-templates" / "mirror-talk-home.php").read_text()

    assert "mirrortalk_resolve_topic_context" in single
    assert "array('general', 'uncategorized')" in single
    assert "get_the_post_thumbnail_url(get_the_ID(), 'large')" in home
    assert "get_the_post_thumbnail_url(get_the_ID(), 'full')" not in home


def test_listening_companion_uses_rss_and_respectful_ctas():
    php = (THEME_DIR / "inc" / "listen-and-connect.php").read_text()
    registry = (THEME_DIR / "inc" / "listen-everywhere.php").read_text()
    script = (THEME_DIR / "listen-connect.js").read_text()

    assert "fetch_feed($feed_url)" in php
    assert "anchor.fm/s/261b1464/podcast/rss" in php
    assert "set_transient('mirrortalk_feed_episodes_v2'" in php
    assert "preload=\"metadata\"" in php
    assert "data-mt-episode" in php
    assert "podcasts.apple.com/us/podcast/mirror-talk-soulful-conversations/id1518394292" in registry
    assert "open.spotify.com/show/0trwqguYCic32smqh3Ny60" in registry
    assert "youtube.com/channel/UCFj3nBFVYJhsEGciiu52eEw" in registry
    assert "whatsapp.com/channel/0029VaEER5vC1Fu8V82fFm0u" in php
    assert "patreon.com/MirrorTalk" in php
    assert "21 * 24 * 60 * 60 * 1000" in script
    assert "window.setTimeout" in script
    assert "window.scrollY / available >= 0.55" in script


def test_theme_uses_full_bleed_fluid_viewport_architecture():
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "--mt-viewport-gutter: clamp(16px, 3vw, 52px)" in css
    assert "--mt-wide-shell: 1680px" in css
    assert ".site-content > .ast-container" in css
    assert "max-width: none !important" in css
    assert "width: calc(100% - 24px)" in css
    assert "overflow-x: clip" in css


def test_topic_links_resolve_to_real_virtual_collections():
    journey = (THEME_DIR / "inc" / "journey.php").read_text()
    home = (THEME_DIR / "page-templates" / "mirror-talk-home.php").read_text()
    topic = (THEME_DIR / "topic.php").read_text()

    assert "^explore/(purpose|resilience|relationships|faith|healing|leadership)" in journey
    assert "get_stylesheet_directory() . '/topic.php'" in journey
    assert "home_url('/explore/' . $topic_slug . '/')" in home
    assert "mirrortalk_resolve_topic_context($post->ID)" in topic
    assert "array_slice($matches" in topic
    assert "the_content();" not in home


def test_continuous_listening_has_explicit_browser_player_window():
    php = (THEME_DIR / "inc" / "listen-and-connect.php").read_text()
    main_js = (THEME_DIR / "listen-connect.js").read_text()
    window_js = (THEME_DIR / "listen-window.js").read_text()
    window_template = (THEME_DIR / "player-window.php").read_text()

    assert "data-mt-popout" in php
    assert "mirror_player=1" in php
    assert "window.open(popout.dataset.playerUrl" in main_js
    assert "mt_audio_state_v1" in main_js
    assert "mt_audio_state_v1" in window_js
    assert "data-mt-window-audio" in window_template


def test_contextual_journey_connects_content_to_ask_without_auto_submit():
    journey = (THEME_DIR / "inc" / "journey.php").read_text()
    js = (THEME_DIR / "ask-mirror-talk.js").read_text()

    assert "function mirrortalk_topic_map()" in journey
    assert "function mirrortalk_append_reflection_bridge" in journey
    assert "function mirrortalk_render_ask_dock" in journey
    assert "'prefill' => $topic['prompt']" in journey
    assert "applyContextualPrefill" in js
    prefill_block = js.split("(function applyContextualPrefill()", 1)[1].split("})();", 1)[0]
    assert "input.value = prefill" in prefill_block
    assert "autoSubmitQuestion" not in prefill_block


def test_topic_hubs_are_native_indexable_archives():
    category = (THEME_DIR / "category.php").read_text()
    home = (THEME_DIR / "page-templates" / "mirror-talk-home.php").read_text()

    assert "single_cat_title" in category
    assert "category_description" in category
    assert "the_posts_pagination" in category
    assert "mirrortalk_topic_map()" in home
    assert "home_url('/explore/' . $topic_slug . '/')" in home


def test_insights_library_never_publishes_private_question_archive():
    template = (THEME_DIR / "answer-archive-template.php").read_text()

    assert "Mirror Talk Insights Library" in template
    assert "amt_saved_insights" in template
    assert "Free-form visitor questions are never published" in template
    assert "/api/answer-archive?limit=24" in template
    assert "Privacy-screened" in template
    assert "item.privacy === 'curated_prompt'" in template
    assert "FAQPage" not in template
    assert "new WP_Query" not in template


def test_youtube_studio_is_cached_contextual_and_privacy_aware():
    php = (THEME_DIR / "inc" / "youtube-studio.php").read_text()
    js = (THEME_DIR / "youtube-studio.js").read_text()
    footer = (THEME_DIR / "footer.php").read_text()

    assert "get_transient(MIRRORTALK_YOUTUBE_CACHE_KEY)" in php
    assert "set_transient(MIRRORTALK_YOUTUBE_CACHE_KEY" in php
    assert "MIRRORTALK_YOUTUBE_LAST_GOOD_KEY" in php
    assert "mirrortalk_youtube_fallback_video" in php
    assert "update_option(MIRRORTALK_YOUTUBE_LAST_GOOD_KEY" in php
    assert "wp_safe_remote_get" in php
    assert "youtube.com/feeds/videos.xml" in php
    assert "is_front_page()) return 'cinematic'" in php
    assert "is_singular('post')) return 'article'" in php
    assert "is_home() || is_archive()" in php
    assert "is_page(array('ask-mirror-talk', 'insights'))" in php
    assert "mirrortalk_render_youtube_studio" in footer
    assert "mt_external_media_consent_v1" in js
    assert "youtube-nocookie.com" in js
    assert "intersectionRatio >= 0.5" in js
    assert "prefers-reduced-motion: reduce" in js
    assert "navigator.connection && navigator.connection.saveData" in js


def test_youtube_and_podcast_players_coordinate_audio():
    youtube_js = (THEME_DIR / "youtube-studio.js").read_text()
    podcast_js = (THEME_DIR / "listen-connect.js").read_text()
    hub_js = (THEME_DIR / "link-hub.js").read_text()

    assert "mt:podcast-play" in podcast_js
    assert "mt:podcast-play" in youtube_js
    assert "pausePodcast()" in youtube_js
    assert "youtube_video_unmuted" in youtube_js
    assert "youtube_video_complete" in youtube_js
    assert "[data-mt-audio],[data-mt-link-hub-audio]" in youtube_js
    assert "mt:podcast-play" in hub_js


def test_link_hub_has_compact_latest_youtube_studio():
    hub_php = (THEME_DIR / "inc" / "link-hub.php").read_text()
    template = (THEME_DIR / "link-hub.php").read_text()
    css = (THEME_DIR / "link-hub.css").read_text()
    youtube_php = (THEME_DIR / "inc" / "youtube-studio.php").read_text()

    assert "mirrortalk_render_link_hub_youtube" in hub_php
    assert "mirrortalk_latest_youtube_video" in hub_php
    assert "mirror-talk-youtube-studio" in hub_php
    assert "data-mt-youtube-studio" in hub_php
    assert "data-mt-youtube-media" in hub_php
    assert "data-mt-youtube-consent" in hub_php
    assert "data-mt-youtube-sound" in hub_php
    assert "youtube-video" in hub_php and "youtube-subscribe" in hub_php
    assert "mirrortalk_render_link_hub_youtube();" in template
    assert template.index("mirrortalk_render_link_hub_youtube();") < template.index('class="mt-link-hub__primary"')
    assert ".mt-youtube-studio--link-hub" in css
    assert ".mt-youtube-studio--link-hub.is-short" in css
    assert "if (get_query_var('mirror_links')) return '';" in youtube_php
    assert "mirrortalk_link_hub_duration_label" in hub_php
    assert "mirrortalk_link_hub_duration_label" in template


def test_intelligence_collector_receives_window_and_document_feature_events():
    js = (THEME_DIR / "intelligence.js").read_text()
    assert "window.addEventListener('mt:intelligence-event', receiveIntelligenceEvent)" in js
    assert "document.addEventListener('mt:intelligence-event', receiveIntelligenceEvent)" in js
    assert "new WeakSet()" in js


def test_youtube_studio_prevents_overlap_and_black_autoplay_state():
    php = (THEME_DIR / "inc" / "youtube-studio.php").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()
    js = (THEME_DIR / "youtube-studio.js").read_text()

    assert ".mt-youtube-studio__copy, .mt-youtube-studio__media { min-width: 0; }" in css
    assert "grid-template-columns: minmax(0,.78fr) minmax(0,1.22fr)" in css
    assert "@media (max-width: 1050px)" in css
    assert "Watch. Reflect. Continue." in php
    assert "overflow-wrap: anywhere" not in css
    assert "word-break: break-all" not in css
    assert ".mt-site-frame :where(h1, h2, h3, h4, h5, h6)" in css
    assert "text-wrap: balance" in css
    assert ".mt-youtube-studio.is-short .mt-youtube-studio__player" in css
    assert "width: min(56.25%,430px)" in css
    assert "showPreparingState" in js
    assert "revealNativePlayer" in js
    assert "youtube_autoplay_fallback" in js
    assert "YouTube player API timed out" in js
    assert "poster.hidden = true" in js
    assert "player = event.target" in js
    assert "typeof player.pauseVideo === 'function'" in js
    assert "typeof player.isMuted !== 'function' ? true : player.isMuted()" in js


def test_first_party_contact_form_replaces_plugin_form_and_is_protected():
    php = (THEME_DIR / "inc" / "contact-forms.php").read_text()
    page = (THEME_DIR / "page.php").read_text()
    js = (THEME_DIR / "contact-form.js").read_text()

    assert "mirrortalk_render_contact_form" in page
    assert "mirrortalk_contact_submit" in php
    assert "check_ajax_referer" in php
    assert "mirrortalk_contact_rate_limit" in php
    assert "company_website" in php
    assert "hash_hmac" in php
    assert "mt_contact_message" in php
    assert "wp_mail" in php
    assert "srfm-form-submit" in php
    assert "data-mt-contact-form" in php
    dashboard = (THEME_DIR / "inc" / "intelligence-dashboard.php").read_text()
    assert "mirrortalk_intelligence_record_operational_event" in php
    assert "contact_message_sent" in php and "contact_message_sent" in dashboard
    assert "MirrorTalkTrack('contact_message_sent'" not in js


def test_hardening_release_recovers_jobs_and_preserves_real_404s():
    hardening = (THEME_DIR / "inc" / "production-hardening.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()
    assert "production-hardening.php" in functions
    assert "action_scheduler_run_queue" in hardening
    assert "mirrortalk_elementor_auto_batch" in hardening
    assert "all-404-redirect-to-homepage" in hardening
    assert "deactivate_plugins" in hardening
    assert "wp_redirect(home_url" not in hardening


def test_listening_and_conversion_measurement_is_complete_and_not_duplicated():
    analytics = (THEME_DIR / "intelligence.js").read_text()
    player = (THEME_DIR / "listen-connect.js").read_text()
    story = (THEME_DIR / "editorial-story-studio.js").read_text()
    newsletter = (THEME_DIR / "inc" / "listen-and-connect.php").read_text()
    assert "aggregateEvents" in analytics and "podcast_play" in analytics
    assert "podcast_progress" in analytics and "podcast_complete" in analytics
    assert "document.querySelectorAll('audio').forEach(instrumentAudio)" in analytics
    assert "[data-mt-audio],[data-mt-story-audio]" in analytics
    assert "percent >= 95" in player and ">= 0.95" in story
    assert "mirrortalk_intelligence_record_operational_event('newsletter_subscribed'" in newsletter
    assert "MirrorTalkTrack('newsletter_subscribed'" not in (THEME_DIR / "listen-connect.js").read_text()


def test_campaign_links_and_source_hygiene_are_guarded():
    hardening = (THEME_DIR / "inc" / "production-hardening.php").read_text()
    platforms = (THEME_DIR / "inc" / "listen-everywhere.php").read_text()
    assert "utm_source" in hardening and "utm_campaign" in hardening
    assert "mirrortalk_campaign_url" in platforms
    assert "_mirrortalk_source_hygiene_snapshot_v1" in hardening
    assert "'_elementor_data', 'compare' => 'NOT EXISTS'" in hardening
    assert "title=\"" in hardening and "<h2$1>" in hardening


def test_ai_source_discovery_is_explicit_and_collision_proof():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    seo = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()

    assert "mirror-talk-ai-guide" in platform
    assert "mt_ai_guide" in platform
    assert "OAI-SearchBot" in platform
    assert "ChatGPT-User" in platform
    assert "PerplexityBot" in platform
    assert "Citation guidance" in platform
    assert "Mirror Talk AI source guide" in seo


def test_llms_endpoints_are_owned_and_bounded():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()

    assert "^llms\\.txt$" in platform
    assert "^llms-full\\.txt$" in platform
    assert "mirrortalk_claim_llms_ownership" in platform
    assert "getFilePath($full)" in platform
    assert "$limit = $full ? 500 : 30" in platform
    assert "Private Ask Mirror Talk reflections" in platform
    assert "alternate[\"\\']" in platform and "text/plain" in platform


def test_primary_navigation_is_listener_first_and_self_healing():
    navigation = (THEME_DIR / "inc" / "navigation.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()

    assert "mirrortalk_listener_first_menu" in navigation
    assert "home_url('/listen/')" in navigation
    assert "podcast-episodes" in navigation
    assert "'/insights/'" in navigation
    assert "'home' => 10, 'listen' => 20, 'explore' => 30, 'ask' => 40" in navigation
    assert "$has_nested_insights" in navigation
    assert "__('Listen', 'astra-child')" in navigation
    assert ".site-header .ast-header-button-1" in (THEME_DIR / "mirror-talk-site.css").read_text()
    assert "inc/navigation.php" in functions


def test_mobile_floating_actions_have_separate_lanes():
    css = (THEME_DIR / "mirror-talk-site.css").read_text()
    assert "bottom: calc(max(12px, env(safe-area-inset-bottom)) + 66px) !important" in css
    assert ".mt-listen__launcher { display: inline-flex !important; }" in css
    assert ".home .mt-home__feature { display: block !important" in css


def test_player_return_and_archive_heading_are_reliable():
    player_window = (THEME_DIR / "player-window.php").read_text()
    player_runtime = (THEME_DIR / "listen-window.js").read_text()
    archive = (THEME_DIR / "archive.php").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "data-return-url" in player_window
    assert 'href="<?php echo esc_url(home_url(\'/\')); ?>"' in player_window
    assert "window.opener.focus()" in player_runtime
    assert "window.close()" in player_runtime
    assert "window.location.assign(returnUrl)" in player_runtime
    assert "single_tag_title('', false)" in archive
    assert ".tag .site-content > .ast-container > h1:first-child" in css


def test_global_shell_is_owned_by_mirror_talk():
    header = (THEME_DIR / "header.php").read_text()
    footer = (THEME_DIR / "footer.php").read_text()
    search = (THEME_DIR / "search.php").read_text()
    not_found = (THEME_DIR / "404.php").read_text()
    runtime = (THEME_DIR / "mirror-talk-site.js").read_text()

    assert "mt-site-header" in header
    assert "wp_head()" in header
    assert "wp_body_open()" in header
    assert "wp_nav_menu" in header
    assert "mt-site-footer" in footer
    assert "wp_footer()" in footer
    assert "A reflective space" in footer
    assert "Search the conversations" in search
    assert "This page has moved beyond the mirror" in not_found
    assert "data-mt-nav-toggle" in runtime


def test_staging_delivery_is_uncached_and_release_assets_are_fingerprinted():
    functions = (THEME_DIR / "functions.php").read_text()
    widget = (THEME_DIR / "ask-mirror-talk.php").read_text()

    assert "calm.mirrortalkpodcast.com" in functions
    assert "DONOTCACHEPAGE" in functions
    assert "X-LiteSpeed-Cache-Control" in functions
    assert "litespeed_purge_all" in functions
    assert "mirrortalk_asset_version" in functions
    assert "filemtime($path)" in functions
    assert "wp_get_theme()->get('Version')" in widget
    assert "return '6.1.0'" not in widget
    assert "mirror-talk-release.json" in functions
    assert "X-Mirror-Talk-Release" in functions
    assert "mirror-talk-release" in functions
    assert "remove_action('wp_footer', 'ask_mirror_talk_pwa_footer', 99)" in functions
    assert "registration.unregister()" in functions
    assert "caches.delete(key)" in functions


def test_release_maintenance_never_flushes_rewrites_on_public_requests():
    listen = (THEME_DIR / "inc" / "listen-everywhere.php").read_text()
    journey = (THEME_DIR / "inc" / "journey.php").read_text()

    assert "add_action('after_switch_theme', 'mirrortalk_refresh_listen_route_once'" in listen
    assert "add_action('admin_init', 'mirrortalk_refresh_listen_route_once'" in listen
    assert "add_action('init', 'mirrortalk_refresh_listen_route_once'" not in listen
    assert "add_action('after_switch_theme', 'mirrortalk_refresh_topic_routes_once'" in journey
    assert "add_action('admin_init', 'mirrortalk_refresh_topic_routes_once'" in journey
    assert "add_action('init', 'mirrortalk_refresh_topic_routes_once'" not in journey


def test_discovery_documents_are_cached_and_invalidated():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    sitemap = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()

    assert "function mirrortalk_discovery_document" in platform
    assert "function mirrortalk_flush_discovery_documents" in platform
    assert "add_action('save_post', 'mirrortalk_flush_discovery_documents'" in platform
    for key in (
        "mirrortalk_llms_short_v2",
        "mirrortalk_llms_full_v2",
        "mirrortalk_news_sitemap_v2",
        "mirrortalk_video_sitemap_v2",
    ):
        assert key in platform
    assert "mirrortalk_main_sitemap_v2" in sitemap


def test_owned_surfaces_remove_generated_spectra_assets_without_touching_posts():
    functions = (THEME_DIR / "functions.php").read_text()

    assert "function mirrortalk_streamline_owned_home_assets" in functions
    assert "get_query_var('mirror_blog')" in functions
    assert "get_query_var('mirror_topic')" in functions
    assert "'/uploads/uag-plugin/assets/'" in functions
    assert "wp_dequeue_script($handle)" in functions


def test_living_mirror_connects_listening_moments_to_private_reflection():
    player = (THEME_DIR / "inc" / "listen-and-connect.php").read_text()
    runtime = (THEME_DIR / "listen-connect.js").read_text()
    ask = (THEME_DIR / "ask-mirror-talk.js").read_text()
    insights = (THEME_DIR / "answer-archive-template.php").read_text()

    assert "What would help you today?" in player
    assert "data-mt-save-moment" in player
    assert "data-mt-reflect-moment" in player
    assert "data-mt-reflection-workspace" in player
    assert "Return to listening" in player
    assert "data-mt-transcript-panel" in player
    assert "podcastindex.org/namespace/1.0" in player
    assert "mt_saved_moments_v1" in runtime
    assert "requestReflection" in runtime
    assert "living_mirror_reflection_answered" in runtime
    assert "amt_saved_insights" in runtime
    assert "parseVtt" in runtime
    assert "navigator.mediaSession.setActionHandler" in runtime
    assert "Continuing from your listening" in ask
    assert "data-mt-saved-moments" in insights


def test_newsletter_modal_collects_consent_without_contact_redirect():
    php = (THEME_DIR / "inc" / "listen-and-connect.php").read_text()
    js = (THEME_DIR / "listen-connect.js").read_text()

    assert "data-mt-newsletter-form" in php
    assert "mirrortalk_newsletter_signup" in php
    assert "_mt_subscriber_consent_at" in php
    assert "_mt_subscriber_confirmation_hash" in php
    assert "mirrortalk_newsletter_rate_limit" in php
    assert "hash_equals($expected_proof, $proof)" in php
    assert "wp_ajax_nopriv_mirrortalk_newsletter_signup" in php
    assert "home_url('/contact/')" not in php
    assert "newsletterForm.reportValidity()" in js


def test_redesign_is_scoped_and_accessibility_aware():
    css = (THEME_DIR / "ask-mirror-talk-redesign.css").read_text()

    assert css.count(".ask-mirror-talk") >= 40
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "@media (prefers-contrast: more)" in css
    assert "button:focus-visible" in css


def test_light_premium_surfaces_have_explicit_readable_text_colors():
    css = (THEME_DIR / "ask-mirror-talk-redesign.css").read_text()
    fixture = (Path(__file__).parent / "fixtures" / "premium_redesign_preview.html").read_text()

    assert ".ask-mirror-talk .amt-stats-prompt-text" in css
    assert "color: #2b2433" in css
    assert ".ask-mirror-talk .amt-stats-prompt-subtext" in css
    assert "color: #62596b" in css
    assert ".ask-mirror-talk .amt-stats-prompt-kicker" in css
    assert "color: #6b536f" in css
    assert ".ask-mirror-talk .amt-heading-controls" in css
    assert "background: rgba(24, 15, 31, 0.34)" in css
    assert ".ask-mirror-talk #ask-mirror-talk-input::placeholder" in css
    assert "color: #706777" in css
    assert ".ask-mirror-talk .amt-form-note" in css
    assert ".ask-mirror-talk .amt-workflow-label" in css
    assert "font-size: 11px" in css
    assert "amt-badge-count" in fixture
    assert "amt-stats-prompt-text" in fixture


def test_editorial_composer_uses_complete_semantic_phrases():
    composer = (THEME_DIR / "inc" / "editorial-composer-v2.php").read_text()
    normalizer = (THEME_DIR / "inc" / "content-normalizer.php").read_text()

    assert "MIRRORTALK_COMPOSER_V2_VERSION', '2.7.0'" in composer
    assert "'semantic_formatting'" in composer
    assert "'automatic_links'" in composer
    assert "mirrortalk_composer_v2_focus_phrase" in composer
    assert "array_key_first($term_scores)" not in composer
    assert "preg_split('/\\s*:\\s*/u',$title,2" in composer
    assert "$item = trim($sentence);" in composer
    assert "wp_trim_words($sentence, 18" not in composer
    assert "mirrortalk_composer_v2_hook" in composer
    assert "mirrortalk_composer_v2_similarity" in composer
    assert "count($unique)>=2?$unique:array()" in composer
    assert "mt-composer-lead__eyebrow" in composer
    assert "mirrortalk_prepare_existing_editorial_links" in normalizer


def test_elementor_migration_is_staged_verified_resumable_and_reversible():
    migration = (THEME_DIR / "inc" / "elementor-migration.php").read_text()

    assert "MIRRORTALK_ELEMENTOR_MIGRATION_VERSION = '2.1.0'" in migration
    assert "strpos($template,'elementor_')===0" in migration
    assert "mirrortalk_elementor_restore($post_id,true);mirrortalk_elementor_fail_stage" in migration
    assert "mirrortalk_elementor_prepare_candidate" in migration
    assert "mirrortalk_elementor_render_validation" in migration
    assert "array('desktop','mobile')" in migration
    assert "mirrortalk_elementor_process_stage" in migration
    assert "mirrortalk_elementor_fail_stage" in migration
    assert "'quarantined'" in migration
    assert "mirrortalk_elementor_recover_documents" in migration
    assert "_mirrortalk_elementor_snapshot" in migration
    assert "mirrortalk_elementor_restore" in migration
    assert "Complete migration audit log" in migration
    assert "Exact queue and failure state" in migration
    assert "Ignored stale metadata" in migration
    assert "update_post_meta($post_id,'_mirrortalk_elementor_migrated'" in migration


def test_elementor_migration_repairs_known_quarantines_and_counts_provisional_jobs():
    migration = (THEME_DIR / "inc" / "elementor-migration.php").read_text()

    assert "function mirrortalk_elementor_repair_quarantined" in migration
    assert "automatic-repair-heading" in migration
    assert "legacy_snapshot_recheck" in migration
    assert "_mirrortalk_elementor_repair_version" in migration
    assert "job.meta_key='_mirrortalk_elementor_job'" in migration
    assert "wp_slash($snapshot)" in migration
    assert "wp_json_encode(wp_slash($check))" in migration
    assert "legacy_snapshot_recovered" in migration
    assert "strpos($legacy_version,'2.0.')===0" in migration


def test_elementor_template_retirement_is_reference_guarded():
    migration = (THEME_DIR / "inc" / "elementor-migration.php").read_text()

    assert "function mirrortalk_elementor_template_references" in migration
    assert "theme_builder_conditions" in migration
    assert "shortcode_reference" in migration
    assert "elementor_data_reference" in migration
    assert "template_retirement_deferred" in migration
    assert "verified_unreferenced" in migration
    assert "mirrortalk_elementor_residual_dependencies(true)" in migration


def test_editorial_composer_has_governed_corrections_and_audit_ledger():
    composer = (THEME_DIR / "inc" / "editorial-composer-v2.php").read_text()

    assert "mirrortalk_composer_v2_log" in composer
    assert "_mt_composer_v2_events" in composer
    assert "source_hash" in composer
    assert "source_preserved" in composer
    assert "url_locked" in composer
    assert "Correct generated decisions" in composer
    assert "mirrortalk_composer_v2_correct" in composer
    assert "Save corrections and record change" in composer
    assert "Change ledger" in composer
    assert "Review, correct or restore" in composer
    assert "wp_update_post" not in composer
    assert "is_array($saved[$key]??null)" in composer
    assert "$decisions[$key]=$merged" in composer
    assert "is_array($result['topic']??null)" in composer
    assert "$topic_result['keyword']" in composer


def test_story_studio_assets_are_not_gated_by_loop_state():
    studio = (THEME_DIR / "inc" / "editorial-story-studio.php").read_text()

    enqueue = studio.split("add_action('wp_enqueue_scripts'", 1)[1]
    assert "mirrortalk_story_studio_should_enqueue" in enqueue
    assert "mirrortalk_composer_v2_should_render(get_queried_object_id())" not in enqueue
    assert "in_the_loop()" not in enqueue
    assert "wp_enqueue_script('mirror-talk-story-studio'" in enqueue


def test_story_studio_deduplicates_legacy_modules_and_utility_outline_items():
    studio = (THEME_DIR / "inc" / "editorial-story-studio.php").read_text()
    composer = (THEME_DIR / "inc" / "editorial-composer-v2.php").read_text()
    quality = (THEME_DIR / "inc" / "knowledge-quality.php").read_text()

    assert "$plan = mirrortalk_story_studio_plan($post_id);" in studio
    assert "!empty($plan['show_follow'])" in studio
    assert "array('share this','like this')" in composer
    assert "if (!empty($composer) && !get_post_meta($post_id, '_mirrortalk_page_one_links', true)) $related = array();" in quality


def test_release_guardian_probes_composer_runtime_and_prunes_stale_links():
    quality = (THEME_DIR / "inc" / "knowledge-quality.php").read_text()
    seo = (THEME_DIR / "inc" / "seo-platform.php").read_text()

    assert "Story Studio interaction runtime" in quality
    assert "editorial-story-studio.js" in quality
    assert "Composer document runtime" in quality
    assert "$results = array_intersect_key($results, $links);" in seo


def test_frontend_performance_work_never_blocks_reader_requests():
    composer = (THEME_DIR / "inc" / "editorial-composer-v2.php").read_text()
    legacy_composer = (THEME_DIR / "inc" / "editorial-composer.php").read_text()
    feed = (THEME_DIR / "inc" / "listen-and-connect.php").read_text()
    youtube = (THEME_DIR / "inc" / "youtube-studio.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "add_action('wp',function()" not in composer
    assert "add_action('admin_init',function()" not in composer
    assert "if(!$result)return $content" in composer
    assert "mirrortalk_compose_saved_content" in composer
    assert "mirrortalk_composer_v2_queue_saved_content" in composer
    assert "mirrortalk_composer_v2_run($post_id,true);},75,2);" not in composer
    assert "add_action('save_post'" not in legacy_composer
    assert "add_action('wp', function ()" not in legacy_composer
    assert "add_action('admin_init', function ()" not in legacy_composer
    assert "mirrortalk_legacy_composer_disabled" in legacy_composer
    assert "mirrortalk_feed_episodes_last_good_v2" in feed
    assert "mirrortalk_refresh_podcast_feed" in feed
    assert "mirrortalk_refresh_youtube_feed" in youtube
    assert "mirrortalk_frontend_performance_assets" in functions
    assert "wp_dequeue_style('admin-bar')" in functions
    assert "jetpack-paypal-payments" in functions
    assert "content-visibility: auto" in css


def test_story_studio_guides_and_composes_media_without_rewriting_source():
    studio = (THEME_DIR / "inc" / "editorial-story-studio.php").read_text()
    composer = (THEME_DIR / "inc" / "editorial-composer-v2.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()
    script = (THEME_DIR / "editorial-story-studio.js").read_text()
    css = (THEME_DIR / "mirror-talk-site.css").read_text()

    assert "editorial-story-studio.php" in functions
    assert "Mirror Talk Story Studio" in studio
    assert "mirrortalk_story_studio_episode_options" in studio
    assert "mirrortalk_story_studio_resolve_video" in studio
    assert "Latest episode automatically" in studio
    assert "latest channel video when blank" in studio
    assert "mirrortalk_story_studio_insert_after" in studio
    assert "mirrortalk_story_studio_source_video_id" in studio
    assert "mirrortalk_story_studio_find_video_id" in studio
    assert "html_entity_decode" in studio
    assert "data-video-source" in studio
    assert "mirrortalk_story_studio_insert_video" in studio
    assert "'source'=>'document'" in studio
    assert "count($headings[0]) >= 2" in studio
    assert studio.index("get_post_field('post_content'") < studio.index("$manual = esc_url_raw")
    assert "_mt_story_studio" in composer
    assert "podcast_player" in composer
    assert "youtube_player" in composer
    assert "follow_cta" in composer
    assert "newsletter_cta" in composer
    assert "wp_update_post" not in studio
    assert "youtube-nocookie.com/embed/" in script
    assert "data-mt-story-audio" in studio
    assert ".mt-story-podcast" in css
    assert ".mt-story-video" in css
    assert ".mt-story-newsletter" in css


def test_guarded_taxonomy_is_evidence_led_owned_and_reversible():
    taxonomy = (THEME_DIR / "inc" / "guarded-taxonomy.php").read_text()
    composer = (THEME_DIR / "inc" / "editorial-composer-v2.php").read_text()
    knowledge = (THEME_DIR / "inc" / "knowledge-quality.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()

    assert "guarded-taxonomy.php" in functions
    assert "mirrortalk_taxonomy_approved_category_ids" in taxonomy
    assert "mirrortalk_taxonomy_verified_topic" in taxonomy
    assert "confidence']??'')==='high'" in taxonomy
    assert "_mt_taxonomy_owned_categories" in taxonomy
    assert "_mt_taxonomy_owned_tags" in taxonomy
    assert "_mt_taxonomy_exclusions" in taxonomy
    assert "mirrortalk_taxonomy_distinct_tags" in taxonomy
    assert "levenshtein" in taxonomy
    assert "mirrortalk_taxonomy_remove" in taxonomy
    assert "mirrortalk_taxonomy_restore" in taxonomy
    assert "mirrortalk_taxonomy_recheck" in taxonomy
    assert "Taxonomy governance" in taxonomy
    assert "mirrortalk_composer_v2_report_after_decisions" in composer
    assert "mirrortalk_guarded_taxonomy_run" in composer
    assert "books_mentioned" in knowledge
    assert "named_concepts" in knowledge


def test_authenticated_previews_do_not_start_background_or_global_work():
    functions = (THEME_DIR / "functions.php").read_text()
    listen = (THEME_DIR / "inc" / "listen-and-connect.php").read_text()
    youtube = (THEME_DIR / "inc" / "youtube-studio.php").read_text()
    intelligence = (THEME_DIR / "inc" / "intelligence-seo.php").read_text()
    journey = (THEME_DIR / "inc" / "journey.php").read_text()
    knowledge = (THEME_DIR / "inc" / "knowledge-quality.php").read_text()

    assert "mirrortalk_is_editor_preview_request" in functions
    assert "remove_action('init', 'wp_cron')" in functions
    assert "X-Mirror-Talk-Preview-Mode: fast" in functions
    assert "mirrortalk_is_editor_preview_request" in listen
    assert "mirrortalk_is_editor_preview_request" in youtube
    assert "mirrortalk_is_editor_preview_request" in intelligence
    assert "mirrortalk_is_editor_preview_request" in journey
    assert "mirrortalk_is_editor_preview_request" in knowledge


def test_page_one_growth_is_evidence_led_channel_aware_and_reversible():
    growth = (THEME_DIR / "inc" / "page-one-growth.php").read_text()
    functions = (THEME_DIR / "functions.php").read_text()
    dashboard = (THEME_DIR / "inc" / "intelligence-dashboard.php").read_text()
    knowledge = (THEME_DIR / "inc" / "knowledge-quality.php").read_text()

    assert "page-one-growth.php" in functions
    assert "mirrortalk_page_one_high_intent" in growth
    assert "mirrortalk_learning_query_eligible" in growth
    assert "$position >= 4 && $position <= 20" in growth
    assert "mirrortalk_page_one_cannibalization" in growth
    assert "verified transcript" in growth
    assert "timestamped key moments" in growth
    assert "AI citations" in growth
    assert "mirrortalk_page_one_trend" in growth
    assert "mirrortalk_page_one_history" in growth
    assert "mirrortalk_page_one_restore" in growth
    assert "mirrortalk_seo_crawl" in growth
    assert "never fabricated" in growth
    assert "#page-one" in dashboard
    assert "_mirrortalk_page_one_links" in knowledge


def test_link_guardian_replaces_or_unlinks_only_confirmed_failures():
    platform = (THEME_DIR / "inc" / "seo-platform.php").read_text()
    growth = (THEME_DIR / "inc" / "page-one-growth.php").read_text()

    assert "mirrortalk_seo_confirm_link" in platform
    assert "wp_remote_get" in platform
    assert "limit_response_size" in platform
    assert "max(2, (int) ($previous['failures'] ?? 0) + 1)" in platform
    assert "repeated_internal_failure_unlinked" in platform
    assert "repeated_external_failure_unlinked" in platform
    assert "md5($post->ID . '|' . $url)" in platform
    assert "mirrortalk_seo_cleanup_broken_links_continue" in platform
    assert "mirrortalk_clean_link_guardian_version" in platform
    assert "mirrortalk_link_repair_log" in platform
    assert "mirrortalk_seo_cleanup_broken_links" in growth
