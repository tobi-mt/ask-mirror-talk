"""
card_template_analytics.py
Analytics and A/B testing utilities for card template performance tracking.
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def log_card_template_impression(
    db,
    template_family: str,
    template_variant: int,
    user_ip: str,
    device_id: str | None = None,
    qa_log_id: int | None = None,
    question_theme: str | None = None,
    ab_test_group: str = "control"
):
    """
    Log a card template impression (when a template is shown to a user).
    
    Args:
        db: SQLAlchemy session
        template_family: e.g., 'editorial', 'aura_poster', 'bold_vibrant'
        template_variant: 0-3 (visual variant number)
        user_ip: User's IP for session tracking
        device_id: Optional device identifier
        qa_log_id: Associated QA log ID if applicable
        question_theme: Theme of the question/card
        ab_test_group: 'control' or 'bold_variant' for A/B testing
    """
    try:
        sql = """
        INSERT INTO card_template_variants
        (created_at, user_ip, device_id, template_family, template_variant, 
         qa_log_id, question_theme, ab_test_group)
        VALUES (now(), :user_ip, :device_id, :template_family, :template_variant,
                :qa_log_id, :question_theme, :ab_test_group)
        """
        db.execute(text(sql), {
            'user_ip': user_ip,
            'device_id': device_id,
            'template_family': template_family,
            'template_variant': template_variant,
            'qa_log_id': qa_log_id,
            'question_theme': question_theme,
            'ab_test_group': ab_test_group
        })
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Failed to log template impression: {e}")


def record_card_engagement(
    db,
    template_family: str,
    engagement_type: str,  # 'share', 'like', 'skip'
    user_ip: str,
    device_id: str | None = None,
    weight: float | None = None
):
    """
    Record engagement event for a card template.
    
    Args:
        db: SQLAlchemy session
        template_family: Template family that received engagement
        engagement_type: 'share' (2.0), 'like' (1.0), 'skip' (-1.0)
        user_ip: User's IP
        device_id: Optional device ID
        weight: Optional engagement weight (defaults: share=2.0, like=1.0, skip=-1.0)
    """
    engagement_weights = {"share": 2.0, "like": 1.0, "skip": -1.0}
    if weight is None:
        weight = engagement_weights.get(engagement_type, 0.0)
    
    try:
        # Find the most recent impression from this user/device for this template
        sql = """
        UPDATE card_template_variants
        SET 
            was_shared = CASE WHEN :engagement_type = 'share' THEN true ELSE was_shared END,
            was_liked = CASE WHEN :engagement_type = 'like' THEN true ELSE was_liked END,
            was_skipped = CASE WHEN :engagement_type = 'skip' THEN true ELSE was_skipped END,
            shares_count = shares_count + CASE WHEN :engagement_type = 'share' THEN 1 ELSE 0 END,
            engagement_score = engagement_score + :weight
        WHERE template_family = :template_family
          AND user_ip = :user_ip
          AND (:device_id IS NULL OR device_id = :device_id)
          AND created_at > now() - interval '7 days'
        ORDER BY created_at DESC
        LIMIT 1
        """
        db.execute(text(sql), {
            'template_family': template_family,
            'engagement_type': engagement_type,
            'user_ip': user_ip,
            'device_id': device_id,
            'weight': weight
        })
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Failed to record engagement: {e}")


def get_template_performance_metrics(db, days: int = 7) -> dict:
    """
    Get performance metrics for all card templates in the past N days.
    Returns dict with template_family -> metrics mapping.
    """
    try:
        sql = """
        SELECT 
            template_family,
            ab_test_group,
            COUNT(*) as impressions,
            SUM(CASE WHEN was_shared THEN 1 ELSE 0 END) as shares,
            SUM(CASE WHEN was_liked THEN 1 ELSE 0 END) as likes,
            SUM(CASE WHEN was_skipped THEN 1 ELSE 0 END) as skips,
            ROUND(AVG(engagement_score)::numeric, 3) as avg_engagement_score,
            ROUND((SUM(CASE WHEN was_shared OR was_liked THEN 1 ELSE 0 END)::float / 
                   NULLIF(COUNT(*), 0))::numeric, 3) as engagement_rate,
            ROUND((SUM(shares_count)::float / NULLIF(COUNT(*), 0))::numeric, 2) as avg_shares_per_user
        FROM card_template_variants
        WHERE created_at >= now() - make_interval(days => :days)
        GROUP BY template_family, ab_test_group
        ORDER BY template_family, ab_test_group
        """
        rows = db.execute(text(sql), {'days': days}).fetchall()
        
        result = {}
        for row in rows:
            template_family = row[0]
            ab_group = row[1]
            if template_family not in result:
                result[template_family] = {}
            
            result[template_family][ab_group] = {
                'impressions': row[2] or 0,
                'shares': row[3] or 0,
                'likes': row[4] or 0,
                'skips': row[5] or 0,
                'avg_engagement_score': float(row[6] or 0),
                'engagement_rate': float(row[7] or 0),
                'avg_shares_per_user': float(row[8] or 0)
            }
        
        return result
    except SQLAlchemyError as e:
        logger.error(f"Failed to get template metrics: {e}")
        return {}


def get_ab_test_results(db, days: int = 7) -> dict:
    """
    Compare control vs bold_variant performance.
    Returns dict with comparison metrics.
    """
    try:
        metrics = get_template_performance_metrics(db, days)
        
        results = {}
        for template_family, groups in metrics.items():
            control = groups.get('control', {})
            bold = groups.get('bold_variant', {})
            
            results[template_family] = {
                'control': control,
                'bold_variant': bold,
                'winner': None,
                'lift_pct': 0.0
            }
            
            # Determine winner based on engagement rate
            if control and bold:
                control_rate = control.get('engagement_rate', 0)
                bold_rate = bold.get('engagement_rate', 0)
                
                if bold_rate > control_rate:
                    results[template_family]['winner'] = 'bold_variant'
                    results[template_family]['lift_pct'] = round(
                        ((bold_rate - control_rate) / (control_rate or 1)) * 100, 1
                    )
                elif control_rate > bold_rate:
                    results[template_family]['winner'] = 'control'
                    results[template_family]['lift_pct'] = round(
                        ((control_rate - bold_rate) / (bold_rate or 1)) * 100, 1
                    )
        
        return results
    except SQLAlchemyError as e:
        logger.error(f"Failed to get A/B test results: {e}")
        return {}


def get_template_by_theme_performance(db, days: int = 7) -> dict:
    """
    Get template performance breakdown by question theme.
    Helps identify which templates work best for specific themes.
    """
    try:
        sql = """
        SELECT 
            question_theme,
            template_family,
            COUNT(*) as impressions,
            ROUND((SUM(CASE WHEN was_shared OR was_liked THEN 1 ELSE 0 END)::float / 
                   NULLIF(COUNT(*), 0))::numeric, 3) as engagement_rate,
            ROUND(AVG(engagement_score)::numeric, 3) as avg_engagement
        FROM card_template_variants
        WHERE created_at >= now() - make_interval(days => :days)
          AND question_theme IS NOT NULL
        GROUP BY question_theme, template_family
        HAVING COUNT(*) >= 5
        ORDER BY question_theme, engagement_rate DESC
        """
        rows = db.execute(text(sql), {'days': days}).fetchall()
        
        result = {}
        for theme, family, impressions, engagement_rate, avg_engagement in rows:
            if theme not in result:
                result[theme] = []
            result[theme].append({
                'template': family,
                'impressions': impressions,
                'engagement_rate': float(engagement_rate or 0),
                'avg_engagement': float(avg_engagement or 0)
            })
        
        return result
    except SQLAlchemyError as e:
        logger.error(f"Failed to get theme performance: {e}")
        return {}
