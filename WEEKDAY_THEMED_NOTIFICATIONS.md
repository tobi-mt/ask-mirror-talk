# Intelligent Weekday-Themed QOTD & Midday Motivation

## Overview

Added intelligent day-of-week themed notifications to Ask Mirror Talk. The system now automatically prioritizes specific themes based on the day of the week, creating a natural weekly rhythm (e.g., "Monday Motivation" with Empowerment themes, "Wednesday Calm" with Inner Peace themes, "Friday Gratitude").

## What Was Built

### 1. Database Table: `weekday_themes`

Stores theme preferences for each day of the week with priority levels.

Schema:
- `day_of_week`: 0=Monday, 6=Sunday
- `theme`: Maps to existing themes (Empowerment, Purpose, Faith, etc.)
- `priority`: Higher number = more preferred (1-10 scale)
- `description`: Human-readable explanation
- `active`: Enable/disable individual theme assignments

### 2. Weekly Theme Strategy

Each day has 3 prioritized themes designed to match the emotional needs of that day:

#### Monday - Start Strong
1. **Empowerment** (priority 10) - Agency and confidence
2. **Purpose** (priority 9) - Align with calling
3. **Leadership** (priority 8) - Step into influence

#### Tuesday - Build Momentum
1. **Growth** (priority 10) - Embrace change
2. **Courage** (priority 9) - Take honest steps
3. **Transition** (priority 7) - Navigate change

#### Wednesday - Midweek Self-Care
1. **Inner peace** (priority 10) - Find steadiness
2. **Healing** (priority 9) - Tend what needs care
3. **Self-worth** (priority 8) - Return to center

#### Thursday - Push Through
1. **Purpose** (priority 10) - Stay aligned
2. **Boundaries** (priority 9) - Honor yes/no
3. **Empowerment** (priority 8) - Reclaim voice

#### Friday - Celebrate Progress
1. **Gratitude** (priority 10) - Notice what carried you
2. **Relationships** (priority 9) - Connect with clarity
3. **Community** (priority 8) - Acknowledge support

#### Saturday - Personal Reflection
1. **Identity** (priority 10) - Reconnect with voice
2. **Self-worth** (priority 9) - Remember value
3. **Growth** (priority 7) - Reflect on becoming

#### Sunday - Rest & Spiritual
1. **Faith** (priority 10) - Trust in the quiet
2. **Inner peace** (priority 9) - Release bracing
3. **Gratitude** (priority 8) - Honor the week

### 3. Priority System

The system uses a three-tier priority system for selecting questions/messages:

**Priority 1: Holiday Themes** (highest)
- If today is a special holiday (e.g., Mother's Day), those themes take absolute priority
- Example: May 10, 2026 is both Sunday AND Mother's Day → Parenting theme wins

**Priority 2: Weekday Themes**
- If no holiday, use day-of-week themes
- Tries themes in priority order (10, 9, 8, etc.)
- Falls through to next theme if all questions in top theme have been seen

**Priority 3: Normal Rotation** (fallback)
- If all themed content exhausted, falls back to any unseen content
- Maintains the no-repeat guarantee

### 4. Integration Points

Modified functions in `app/notifications/push.py`:
- `get_today_weekday_themes()` - Returns prioritized themes for today
- `send_qotd_notification()` - Uses weekday themes when selecting questions
- `send_midday_motivation_notification()` - Uses weekday themes for motivation messages

### 5. Logging

The system logs which strategy is being used:

**Holiday active:**
```
🎉 Today is Mother's Day — prioritizing 'Parenting' themed questions
```

**Weekday themes active:**
```
📅 Monday — prioritizing themes: Empowerment, Purpose
```

**Per-subscriber selection:**
```
Subscriber 123: selected weekday-themed question (theme=Empowerment)
```

## Testing Results

✅ **Configuration**: 21 weekday theme preferences across 7 days
✅ **Today (Sunday, May 10)**: Correctly detected Faith, Inner peace, Gratitude
✅ **Tomorrow (Monday, May 11)**: Will prioritize Empowerment, Purpose
✅ **Theme Coverage**: Most themes have 2-5 QOTD questions available

### Content Gaps (⚠️ Low/No content for some themes)

**QOTD:**
- Courage: 0 questions (used on Tuesdays)

**Midday Motivation:**
- Boundaries: 0 messages (used on Thursdays)
- Community: 0 messages (used on Fridays)
- Empowerment: 0 messages (used Mon/Thu)
- Identity: 0 messages (used on Saturdays)
- Inner peace: 0 messages (used Wed/Sun)
- Transition: 0 messages (used on Tuesdays)

**Recommendation**: Generate additional content for underrepresented themes, especially those used on popular sending days (Monday, Wednesday, Friday).

## Usage

### Running Migrations

```bash
# First time setup
python3 scripts/migrate_add_weekday_themes.py
```

### Testing

```bash
# View all weekday themes and test detection
python3 scripts/test_weekday_themes.py
```

### Customizing Themes

Adjust priorities or themes for specific days:

```sql
-- Change Monday's top theme to Courage instead of Empowerment
UPDATE weekday_themes 
SET priority = 11 
WHERE day_of_week = 0 AND theme = 'Courage';

-- Disable a theme for a specific day
UPDATE weekday_themes 
SET active = false 
WHERE day_of_week = 0 AND theme = 'Leadership';

-- Add a new theme to Tuesday
INSERT INTO weekday_themes (day_of_week, theme, priority, description)
VALUES (1, 'Communication', 8, 'Tuesday dialogue - speak and listen with care');
```

### Adding Themed Content

To maximize the benefit of weekday themes, generate more questions/messages for underrepresented themes:

```python
# Example: Generate Courage-themed QOTD questions for Tuesdays
# (would need to modify generate_qotd_batch() to target specific themes)
```

## Examples in Practice

### Monday Morning (8 AM local time)
User receives: QOTD with **Empowerment** theme  
"How do I reclaim my voice when I've been silencing myself to keep peace?"

### Wednesday Midday (12 PM local time)
User receives: Midday motivation with **Inner peace** theme  
"💆 Midweek Breath — Your nervous system doesn't need permission to rest..."

### Friday Afternoon
User receives: QOTD with **Gratitude** theme  
"What unexpected support helped me most this week?"

### Mother's Day (Any Sunday in May)
Holiday theme overrides weekday theme:  
User receives: QOTD with **Parenting** theme instead of Faith/Inner peace

## Files Created/Modified

**New Files:**
- `scripts/migrate_add_weekday_themes.py` - Database migration
- `scripts/test_weekday_themes.py` - Test suite
- `WEEKDAY_THEMED_NOTIFICATIONS.md` - This documentation

**Modified Files:**
- `app/notifications/push.py` - Added weekday detection and themed selection

## Benefits

1. **Predictable Weekly Rhythm** - Users can anticipate themed content
2. **Emotionally Intelligent** - Themes match the energy of each day
3. **Increased Engagement** - Relevant content = higher open rates
4. **Flexible System** - Easy to adjust priorities or add new themes
5. **Works with Holidays** - Holidays always take priority, weekdays are backup
6. **No-Repeat Guarantee** - Still maintained even with themed selection

## Future Enhancements

- **User Preferences**: Allow users to opt out of certain weekday themes
- **A/B Testing**: Test different theme combinations per day
- **Regional Variations**: Different themes for different cultures/regions
- **Content Generation**: AI-generated questions targeted to underrepresented themes
- **Analytics Dashboard**: Track which weekday themes perform best
- **Seasonal Adjustments**: Different themes in summer vs. winter

## Notes

- Weekday themes run automatically with existing hourly cron job
- Holiday themes always override weekday themes when both apply
- Personalized motivations (based on user's recent questions) still take priority over pool-based themed messages
- The system gracefully degrades: Holiday → Weekday → Normal rotation
- No impact on subscribers who have already exhausted all themed content
