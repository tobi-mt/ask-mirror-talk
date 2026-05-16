# Card Template A/B Testing Framework

## Overview

A comprehensive A/B testing system for safely evaluating new card template variants (bold_vibrant) against existing templates to determine which design drives higher engagement and shareability.

## Architecture

### 1. **Database Model: CardTemplateVariant**
Tracks every card rendering and its engagement metrics:
- Template family selected (editorial, aura_poster, poster, spotlight, minimal, bold_vibrant)
- Visual variant (0-3)
- Engagement actions (share, like, skip)
- Engagement score (share=2.0, like=1.0, skip=-1.0)
- A/B test group assignment (control or bold_variant)

```sql
CREATE TABLE card_template_variants (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP,
  user_ip VARCHAR(100),
  device_id VARCHAR(64),
  template_family VARCHAR(50),
  template_variant INTEGER,
  qa_log_id INTEGER,
  question_theme VARCHAR(100),
  was_shared BOOLEAN,
  was_liked BOOLEAN,
  was_skipped BOOLEAN,
  shares_count INTEGER,
  engagement_score FLOAT,
  ab_test_group VARCHAR(50)  -- 'control' or 'bold_variant'
);
```

### 2. **Bold Vibrant Template (buildBoldVibrantShareCard)**
New high-contrast template designed for maximum shareability:
- **Vibrant color gradients** by theme (reds for courage, teals for healing, purples for faith)
- **Bold typography** (800 weight, 50-92px)
- **High contrast accents** (yellow, cyan, white depending on theme)
- **Strong visual elements** (top/bottom accent bars, decorative circles)
- **Improved readability** on social media feeds
- **Shadow effects** for depth on dark backgrounds

### 3. **Feature Flags (app/core/config.py)**
```python
card_template_ab_testing_enabled: bool = True
card_template_bold_variant_enabled: bool = False
card_template_bold_variant_rollout_pct: int = 0  # Start at 0, gradually increase
card_template_track_engagement_enabled: bool = True
```

### 4. **A/B Test Manager (scripts/card_ab_test_manager.py)**
CLI tool for:
- Enabling/disabling bold variant at specified rollout percentage
- Viewing performance metrics
- Comparing control vs variant engagement rates
- Identifying winning template by theme
- Rolling out winners safely

### 5. **Analytics Functions (app/core/card_template_analytics.py)**

#### `log_card_template_impression()`
Records when a card is shown to a user.

```python
log_card_template_impression(
    db, 
    template_family='bold_vibrant',
    template_variant=2,
    user_ip='192.168.1.1',
    device_id='device_xyz',
    qa_log_id=123,
    question_theme='courage',
    ab_test_group='bold_variant'
)
```

#### `record_card_engagement()`
Records user engagement (share/like/skip) with a card.

```python
record_card_engagement(
    db,
    template_family='bold_vibrant',
    engagement_type='share',  # or 'like', 'skip'
    user_ip='192.168.1.1',
    device_id='device_xyz',
    weight=2.0  # share=2.0, like=1.0, skip=-1.0
)
```

#### `get_template_performance_metrics()`
Returns engagement metrics by template and A/B group:
```python
{
    'bold_vibrant': {
        'control': {
            'impressions': 1500,
            'shares': 120,
            'likes': 300,
            'skips': 450,
            'engagement_rate': 0.28,
            'avg_engagement_score': 0.45
        },
        'bold_variant': {
            'impressions': 1485,
            'shares': 180,
            'likes': 400,
            'skips': 380,
            'engagement_rate': 0.39,
            'avg_engagement_score': 0.68
        }
    }
}
```

#### `get_ab_test_results()`
Compares control vs variant with winner determination:
```python
{
    'bold_vibrant': {
        'control': {...},
        'bold_variant': {...},
        'winner': 'bold_variant',
        'lift_pct': 39.3  # 39.3% improvement
    }
}
```

## Usage Guide

### Phase 1: Enable A/B Testing (0% rollout - Observation Mode)

**Objective:** Set up infrastructure without changing user experience.

```bash
# Deploy new code with bold_vibrant template available
git push

# Enable tracking but keep bold variant at 0% rollout (data collection only)
python scripts/card_ab_test_manager.py --enable 0

# Verify infrastructure is working
python scripts/card_ab_test_manager.py --report 1
```

**Expected Output:**
- Card template variants table created ✅
- Tracking functions working ✅
- No change to user experience (0% see bold variant)

### Phase 2: Pilot Rollout (5-10% rollout)

**Objective:** Test bold variant with small percentage of users, detect issues.

```bash
# Roll out to 5% of users
python scripts/card_ab_test_manager.py --enable 5

# Monitor performance daily
python scripts/card_ab_test_manager.py --report 1
```

**Watch For:**
- Any rendering errors (check browser console)
- Extreme engagement differences (usually indicates a bug)
- Platform-specific issues (iOS/Android differences)

**Dashboard Output Example:**
```
🔬 A/B TEST COMPARISON:
─────────────────────────────
🏆 BOLD_VIBRANT
   Control:        24.8% engagement (2,340 impressions)
   Bold Variant:   31.2% engagement (2,320 impressions)
   Winner:         BOLD_VARIANT (+25.8%)

✅ POSTER
   Control:        22.4% engagement (1,880 impressions)
   Bold Variant:   19.8% engagement (1,920 impressions)
   Winner:         CONTROL (-11.6%)
```

### Phase 3: Gradual Rollout (10-50%)

**Objective:** Expand successful variant to larger user base.

```bash
# Increase rollout incrementally
python scripts/card_ab_test_manager.py --enable 20
# Wait 2-3 days...
python scripts/card_ab_test_manager.py --report 3

# If good, continue
python scripts/card_ab_test_manager.py --enable 50
```

**Success Criteria:**
- Bold variant maintains 20%+ engagement lift
- No error reports
- Consistent performance across themes
- Shares increasing (not just likes)

### Phase 4: Winner Declaration & Rollout (100%)

**Objective:** Make winning variant the default for all users.

```bash
# When winner is clear (confident at 50%+ rollout):
python scripts/card_ab_test_manager.py --rollout bold_vibrant bold_variant

# This updates getInsightShareFamily() to prefer bold_vibrant
# template selection logic in ask-mirror-talk.js
```

### Safe Rollback Plan

If issues arise at any phase:

```bash
# Immediately disable bold variant
python scripts/card_ab_test_manager.py --enable 0

# Investigate in dev environment
# Test in browser console:
window.__AMT_AB_TEST_BOLD_VARIANT = false
window.__AMT_BOLD_VARIANT_PCT = 0

# Deploy fix and re-enable at lower percentage
```

## Browser-Side Control

For testing/debugging in production, the frontend respects:

```javascript
// Enable/disable A/B testing
window.__AMT_AB_TEST_BOLD_VARIANT = true;  // Enable testing
window.__AMT_BOLD_VARIANT_PCT = 50;        // 50% of impressions

// Force a specific template family for testing
window.__AMT_TEST_FORCE_FAMILY = 'bold_vibrant';
```

**Browser Console Test:**
```javascript
// Check current card impression
console.log(window.__AMT_LAST_RENDER_DEBUG__);
// Output: { family: 'bold_vibrant', headline: '...' }

// Manually trigger rendering
window.__AMT_AB_TEST_BOLD_VARIANT = true;
window.__AMT_BOLD_VARIANT_PCT = 100;
// Next card share will use bold_vibrant
```

## Metrics Interpretation

### Engagement Rate
- **Formula:** (shares + likes) / total_impressions
- **Good target:** >20%
- **Excellent:** >30%

### Average Engagement Score
- **Formula:** (shares×2 + likes×1 + skips×-1) / impressions
- **Good:** >0.30
- **Excellent:** >0.50

### Lift Percentage
- **Formula:** ((variant_rate - control_rate) / control_rate) × 100
- **Statistically significant:** >10% at 500+ impressions
- **Meaningful improvement:** >20%

### Minimum Sample Size
- **Per group:** 500+ impressions before drawing conclusions
- **For theme-specific:** 100+ impressions per theme

## Theme-Specific Performance

Different themes may respond differently to bold_vibrant:

```
🎨 PERFORMANCE BY THEME:

COURAGE:
  • bold_vibrant      - 42.3% engagement (780 impressions) ← STRONG
  • aura_poster       - 18.9% engagement (410 impressions)

HEALING:
  • bold_vibrant      - 35.1% engagement (620 impressions) ← GOOD
  • aura_poster       - 26.4% engagement (580 impressions)

FAITH:
  • bold_vibrant      - 28.4% engagement (450 impressions) ← OKAY
  • editorial         - 24.7% engagement (420 impressions)
```

**Insight:** May selectively default bold_vibrant for high-performing themes.

## Safety Checklist

- [ ] Database migration executed (`migrate_add_card_template_variants.py`)
- [ ] Analytics functions tested with real data
- [ ] Browser console testing passes (window.__AMT_* flags work)
- [ ] Low initial rollout (0-5%) deployed
- [ ] Daily metric reviews for 3-5 days minimum
- [ ] No errors in browser console
- [ ] Engagement lift confirmed (>10%)
- [ ] Gradual rollout path planned (5% → 10% → 25% → 50% → 100%)
- [ ] Rollback procedure documented and tested
- [ ] Team notified of changes and success criteria

## Next Steps

1. **Deploy migrations** - Run `migrate_add_card_template_variants.py`
2. **Deploy code** - Merge card template A/B testing changes to production
3. **Enable tracking** - `python scripts/card_ab_test_manager.py --enable 0`
4. **Monitor 24hrs** - Verify tracking working: `--report 1`
5. **Pilot rollout** - `python scripts/card_ab_test_manager.py --enable 5`
6. **Daily reviews** - `--report 1` for minimum 3 days
7. **Gradual increase** - Follow Phase 3 schedule based on results
8. **Winner rollout** - Complete Phase 4 when >20% lift confirmed

## Questions?

- **Engagement not tracking?** Check CardTemplateVariant table has impressions/engagement records
- **A/B test not working?** Verify window.__AMT_AB_TEST_BOLD_VARIANT and window.__AMT_BOLD_VARIANT_PCT in browser
- **Bold variant not rendering?** Check buildBoldVibrantShareCard() for theme color/style bugs
- **Database query errors?** Verify migration ran successfully and table exists
