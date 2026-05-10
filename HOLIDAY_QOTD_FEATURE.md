# Holiday-Themed QOTD & Midday Motivation

## Overview

Implemented a holiday-aware system for Ask Mirror Talk QOTD and midday motivation notifications. When a special holiday is detected (e.g., Mother's Day, Valentine's Day), the system automatically prioritizes questions and motivational messages matching that holiday's theme.

## What Was Built

### 1. Database Table: `holidays`

A new table to store holiday configuration with support for:
- **Fixed-date holidays** (e.g., January 1, December 25)
- **Calculated holidays** (e.g., 2nd Sunday in May for Mother's Day)

Schema includes:
- `name`: Holiday name
- `description`: Optional description
- `theme`: Maps to existing themes (Parenting, Relationships, Faith, etc.)
- `fixed_month/fixed_day`: For holidays on fixed dates
- `calc_month/calc_week/calc_day_of_week`: For calculated holidays
- `active`: Enable/disable individual holidays

### 2. Pre-Seeded Holidays

The system comes with 13 popular holidays:
- **New Year's Day** → Purpose
- **Valentine's Day** → Relationships
- **International Women's Day** → Empowerment
- **Earth Day** → Gratitude
- **Mother's Day** → Parenting
- **Father's Day** → Parenting
- **Independence Day (US)** → Empowerment
- **World Mental Health Day** → Healing
- **Thanksgiving (US)** → Gratitude
- **World Kindness Day** → Community
- **Christmas Eve** → Faith
- **Christmas Day** → Faith
- **New Year's Eve** → Gratitude

### 3. Smart Question Selection

Modified both QOTD and midday motivation to:
1. Detect if today is a holiday
2. Prioritize questions/messages matching the holiday theme
3. Fall back to normal rotation if no themed content is available or all themed content has been seen

### 4. Files Created/Modified

**New Files:**
- `scripts/migrate_add_holidays.py` - Database migration
- `scripts/test_holiday_detection.py` - Test suite

**Modified Files:**
- `app/notifications/push.py` - Added holiday detection and themed selection logic

## How It Works

### Holiday Detection

The system runs hourly (same schedule as QOTD/midday motivation) and:
1. Checks if today matches any active holiday
2. Returns the holiday's theme if found
3. Uses that theme to filter available questions/messages

### Question Selection Logic

**QOTD:**
```python
# If today is Mother's Day (theme: Parenting)
# 1. Look for unseen "Parenting" themed questions
# 2. If found, send that question
# 3. If not, fall back to next unseen question regardless of theme
```

**Midday Motivation:**
```python
# Same logic applies to midday motivation messages
# Personalized messages still take priority over pool-based selection
```

## Testing

Verified on May 10, 2026 (Mother's Day):
- ✅ Holiday correctly detected
- ✅ Theme correctly identified as "Parenting"
- ✅ 4 Parenting-themed QOTD questions available
- ✅ System logs show holiday selection is active

## Usage

### Running the Migration

```bash
python3 scripts/migrate_add_holidays.py
```

### Testing Holiday Detection

```bash
python3 scripts/test_holiday_detection.py
```

### Adding New Holidays

Add holidays directly to the database:

```sql
-- Fixed date (e.g., Halloween)
INSERT INTO holidays (name, description, theme, fixed_month, fixed_day, active)
VALUES ('Halloween', 'Spooky celebration', 'Community', 10, 31, true);

-- Calculated date (e.g., Easter - complex, would need external calculation)
INSERT INTO holidays (name, description, theme, calc_month, calc_week, calc_day_of_week, active)
VALUES ('Labor Day (US)', 'Labor Day', 'Gratitude', 9, 1, 0, true);  -- 1st Monday in September
```

### Disabling a Holiday

```sql
UPDATE holidays SET active = false WHERE name = 'Halloween';
```

## Logs

When a holiday is active, you'll see logs like:
```
🎉 Today is Mother's Day — prioritizing 'Parenting' themed questions
```

When a subscriber receives a holiday-themed question:
```
Subscriber 123: selected holiday-themed question (theme=Parenting)
```

## Future Enhancements

Potential additions:
- Regional holiday variations (UK, EU, etc.)
- Multi-language holiday names
- Custom holiday creation via admin UI
- Easter and other complex calculated holidays
- Holiday-specific notification copy/imagery

## Notes

- Holiday detection runs automatically; no manual intervention needed
- If all themed questions have been seen by a subscriber, they fall back to normal rotation
- Holidays don't interrupt the "no-repeat" guarantee - subscribers still won't receive duplicate questions
- The system is timezone-aware and works with subscribers' local dates
