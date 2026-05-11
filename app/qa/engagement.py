"""
User Engagement Tracking

Tracks user activity patterns to enable retention features like:
- Streak counting (consecutive days of use)
- Personalized recommendations based on past questions
- Milestone celebrations

This module provides read-only analytics helpers for the frontend.
"""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_user_stats(db: Session, user_ip: str) -> dict:
    """
    Get engagement statistics for a user (by IP).
    
    Returns:
        {
            "total_questions": int,
            "current_streak": int,  # consecutive days with activity
            "longest_streak": int,
            "first_visit": datetime,
            "last_visit": datetime,
            "days_active": int,  # unique days with activity
            "favorite_topics": list[str],  # inferred from question patterns
        }
    """
    try:
        # Get basic activity stats
        stats_query = text("""
            SELECT 
                COUNT(*) as total_questions,
                MIN(created_at) as first_visit,
                MAX(created_at) as last_visit,
                COUNT(DISTINCT DATE(created_at)) as days_active
            FROM qa_logs
            WHERE user_ip = :user_ip
        """)
        
        result = db.execute(stats_query, {"user_ip": user_ip}).fetchone()
        
        if not result or result.total_questions == 0:
            return {
                "total_questions": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "first_visit": None,
                "last_visit": None,
                "days_active": 0,
                "favorite_topics": [],
            }
        
        # Calculate streak by checking consecutive days
        streak_query = text("""
            SELECT DISTINCT DATE(created_at) as activity_date
            FROM qa_logs
            WHERE user_ip = :user_ip
            ORDER BY activity_date DESC
        """)
        
        activity_dates = [row.activity_date for row in db.execute(streak_query, {"user_ip": user_ip})]
        
        current_streak = _calculate_current_streak(activity_dates)
        longest_streak = _calculate_longest_streak(activity_dates)
        
        # Infer favorite topics from question keywords
        topics_query = text("""
            SELECT question
            FROM qa_logs
            WHERE user_ip = :user_ip
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        questions = [row.question for row in db.execute(topics_query, {"user_ip": user_ip})]
        favorite_topics = _infer_topics(questions)
        
        return {
            "total_questions": result.total_questions,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "first_visit": result.first_visit,
            "last_visit": result.last_visit,
            "days_active": result.days_active,
            "favorite_topics": favorite_topics[:3],  # Top 3 topics
        }
        
    except Exception as exc:
        logger.error(f"Failed to get user stats for {user_ip}: {exc}", exc_info=True)
        return {
            "total_questions": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "first_visit": None,
            "last_visit": None,
            "days_active": 0,
            "favorite_topics": [],
        }


def _calculate_current_streak(activity_dates: list) -> int:
    """Calculate current consecutive days streak."""
    if not activity_dates:
        return 0
    
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    
    # Streak is broken if no activity today or yesterday
    if activity_dates[0] not in (today, yesterday):
        return 0
    
    streak = 0
    expected_date = activity_dates[0]
    
    for date in activity_dates:
        if date == expected_date:
            streak += 1
            expected_date = date - timedelta(days=1)
        else:
            break
    
    return streak


def _calculate_longest_streak(activity_dates: list) -> int:
    """Calculate longest ever consecutive days streak."""
    if not activity_dates:
        return 0
    
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(activity_dates)):
        expected = activity_dates[i-1] - timedelta(days=1)
        if activity_dates[i] == expected:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    
    return max_streak


def _infer_topics(questions: list[str]) -> list[str]:
    """Infer user's favorite topics from their question history."""
    # Topic keywords and their display names
    topic_keywords = {
        "relationships": ["love", "relationship", "partner", "marriage", "dating", "trust", "boundary"],
        "grief": ["grief", "loss", "death", "died", "mourning", "goodbye"],
        "courage": ["courage", "brave", "fear", "afraid", "scared", "risk"],
        "forgiveness": ["forgive", "forgiveness", "resentment", "anger", "hurt"],
        "parenting": ["parent", "child", "kids", "son", "daughter", "family"],
        "purpose": ["purpose", "meaning", "calling", "passion", "destiny"],
        "healing": ["heal", "trauma", "recovery", "therapy", "wounded"],
        "faith": ["faith", "god", "prayer", "spiritual", "divine", "belief"],
        "growth": ["change", "growth", "transform", "better", "improve"],
        "anxiety": ["anxiety", "worry", "stress", "overwhelm", "peace", "calm"],
    }
    
    topic_counts = {topic: 0 for topic in topic_keywords}
    
    for question in questions:
        question_lower = question.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                topic_counts[topic] += 1
    
    # Sort by count and return top topics
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, count in sorted_topics if count > 0]


def get_milestone_message(stats: dict) -> str | None:
    """
    Generate a celebratory message for user milestones.
    
    Returns None if no milestone reached, otherwise a friendly message.
    """
    total = stats["total_questions"]
    streak = stats["current_streak"]
    
    milestones = {
        1: "Welcome! You've asked your first question. 🌱",
        5: "You've asked 5 questions! You're building a reflection practice. ✨",
        10: "10 questions explored! You're diving deeper. 🌊",
        25: "25 reflections! You're becoming more self-aware. 🎯",
        50: "50 questions! You're committed to growth. 🌟",
        100: "100 reflections! You're a wisdom seeker. 🏆",
    }
    
    streak_milestones = {
        3: "3-day streak! You're building momentum. 🔥",
        7: "Week streak! You're making this a habit. 💪",
        14: "2-week streak! You're truly committed. ⭐",
        30: "30-day streak! You're a daily reflection champion! 🎉",
    }
    
    # Check for question milestones
    if total in milestones:
        return milestones[total]
    
    # Check for streak milestones
    if streak in streak_milestones:
        return streak_milestones[streak]
    
    return None
