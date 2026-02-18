#!/usr/bin/env python3
"""
Generate Weekly Engagement Report

Analyzes:
- Query volume
- Episode diversity
- MMR performance
- User engagement trends

Run: python scripts/weekly_engagement_report.py
"""

from datetime import datetime, timedelta


def generate_weekly_report():
    """Generate comprehensive weekly engagement report"""
    
    print("=" * 80)
    print("📊 WEEKLY ENGAGEMENT REPORT - Ask Mirror Talk")
    print("=" * 80)
    
    week_start = datetime.now() - timedelta(days=7)
    week_end = datetime.now()
    
    print(f"Period: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
    print()
    
    print("=" * 80)
    print("1. QUERY VOLUME")
    print("=" * 80)
    print("  Instructions:")
    print("  - Run: railway logs --since 7d | grep 'POST /ask' | wc -l")
    print("  - Enter total queries: _______")
    print("  - Compare to previous week")
    print("  - Trend: ⬆️ Increasing / ➡️ Stable / ⬇️ Decreasing")
    print()
    
    print("=" * 80)
    print("2. EPISODE DIVERSITY")
    print("=" * 80)
    print("  Instructions:")
    print("  - Run: railway logs --since 7d | grep 'MMR: Selected' | grep -oE 'Episode [0-9]+' | sort | uniq | wc -l")
    print("  - Unique episodes cited: _______")
    print("  - Target: >100 episodes (for 471 total)")
    print("  - Percentage of catalog: _______% (= unique/471 * 100)")
    print()
    
    print("=" * 80)
    print("3. EPISODE DISTRIBUTION")
    print("=" * 80)
    print("  Instructions:")
    print("  - Run: railway logs --since 7d | grep 'MMR: Selected' | grep -oE 'Episode [0-9]+' | sort | uniq -c | sort -rn | head -10")
    print("  - List top 10 episodes:")
    print("    1. Episode ___ : ___ times")
    print("    2. Episode ___ : ___ times")
    print("    ...")
    print("  - Check: No episode should appear >30% of total queries")
    print()
    
    print("=" * 80)
    print("4. MMR PERFORMANCE")
    print("=" * 80)
    print("  Instructions:")
    print("  - Run: railway logs --since 7d | grep 'MMR: Final selection'")
    print("  - Review candidate pool sizes (should be ~30)")
    print("  - Check for any warnings or errors")
    print("  - Average diversity rate: _______% (unique episodes per query)")
    print()
    
    print("=" * 80)
    print("5. USER FEEDBACK")
    print("=" * 80)
    print("  Check:")
    print("  - [ ] Comments on website")
    print("  - [ ] Support emails")
    print("  - [ ] Social media mentions")
    print("  - [ ] Contact form submissions")
    print()
    print("  Sentiment:")
    print("  - Positive: _____ mentions")
    print("  - Neutral: _____ mentions")
    print("  - Negative: _____ mentions")
    print()
    print("  Common themes:")
    print("  - More episode variety: _____")
    print("  - Finding new episodes: _____")
    print("  - Citations not relevant: _____")
    print()
    
    print("=" * 80)
    print("6. RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("  Based on metrics above:")
    print()
    print("  ✅ Keep Current Settings If:")
    print("     - Unique episodes > 100/week")
    print("     - No episode dominates (>30%)")
    print("     - User feedback is positive")
    print("     - No relevance complaints")
    print()
    print("  ⚙️ Tune DIVERSITY_LAMBDA If:")
    print("     - Too repetitive → Decrease to 0.6")
    print("     - Too random → Increase to 0.8")
    print("     - Relevance complaints → Increase to 0.8-0.9")
    print()
    print("  🔍 Investigate If:")
    print("     - Query volume drops significantly")
    print("     - One episode dominates (>50%)")
    print("     - Errors in logs")
    print("     - Negative user feedback")
    print()
    
    print("=" * 80)
    print("✅ Report Template Complete")
    print()
    print("💡 Save this report and compare week-over-week trends")
    print("   Run: python scripts/weekly_engagement_report.py > reports/week_$(date +%Y%m%d).txt")
    print()


if __name__ == "__main__":
    generate_weekly_report()
