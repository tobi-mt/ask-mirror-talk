from app.api.routes.admin import AdminDashboardData, render_admin_dashboard_html


def test_render_admin_dashboard_html_includes_core_sections():
    data = AdminDashboardData(
        total_questions=12,
        unique_users=5,
        avg_latency=321.4,
        fb_positive=3,
        fb_negative=1,
        fb_total=4,
        fb_pct=75,
        unanswered_count=2,
        cached_count=6,
        top_unanswered=[("Why do I feel stuck?", 2)],
        top_episodes=[(1, "Episode One", 7)],
        runs=[(10, "2026-04-01", "2026-04-01", "success", "processed=2")],
        logs=[(99, "2026-04-02", "How do I heal?", 123, "127.0.0.1")],
    )

    html = render_admin_dashboard_html(data)

    assert "Ask Mirror Talk Admin" in html
    assert "Analytics & System Dashboard" in html
    assert "User Satisfaction" in html
    assert "Top Unanswered Questions" in html
    assert "Episode One" in html
    assert "How do I heal?" in html
