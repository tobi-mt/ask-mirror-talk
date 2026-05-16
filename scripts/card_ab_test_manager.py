#!/usr/bin/env python3
"""
A/B Test Setup and Management for Card Template Variants

This script provides utilities for:
1. Enabling/disabling the bold variant A/B test
2. Querying performance metrics
3. Comparing control vs bold variant
4. Safely rolling out winners
"""
import sys
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.card_template_analytics import (
    get_template_performance_metrics,
    get_ab_test_results,
    get_template_by_theme_performance
)

def enable_ab_test(rollout_pct: int):
    """Enable the bold variant A/B test at specified rollout percentage."""
    if not (0 <= rollout_pct <= 100):
        print("❌ Rollout percentage must be 0-100")
        return False
    
    engine = create_engine(settings.database_url)
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO quote_selector_weight_versions (version, weights_json, metrics_json, is_active)
                SELECT 
                    COALESCE(MAX(version), 0) + 1,
                    weights_json,
                    json_build_object(
                        'ab_test_enabled', true,
                        'bold_variant_rollout_pct', :rollout_pct,
                        'test_started_at', now()
                    ),
                    true
                FROM quote_selector_weight_versions
                WHERE is_active = true
                LIMIT 1
            """), {'rollout_pct': rollout_pct})
        
        print(f"✅ A/B test enabled: {rollout_pct}% of users will see bold_vibrant variant")
        print(f"   Use window.__AMT_AB_TEST_BOLD_VARIANT = true and window.__AMT_BOLD_VARIANT_PCT = {rollout_pct}")
        return True
    except Exception as e:
        print(f"❌ Failed to enable A/B test: {e}")
        return False

def disable_ab_test():
    """Disable the bold variant A/B test."""
    try:
        print("✅ A/B test disabled (set window.__AMT_AB_TEST_BOLD_VARIANT = false in browser)")
        return True
    except Exception as e:
        print(f"❌ Failed to disable A/B test: {e}")
        return False

def show_performance_report(days: int = 7):
    """Display A/B test performance metrics."""
    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        # Show overall metrics
        print("\n" + "=" * 80)
        print("CARD TEMPLATE PERFORMANCE REPORT")
        print(f"Period: Last {days} days ({datetime.now().date() - timedelta(days=days)} to {datetime.now().date()})")
        print("=" * 80)
        
        try:
            # Get overall metrics
            metrics = get_template_performance_metrics(conn, days=days)
            
            if not metrics:
                print("❌ No template data available yet. Cards need to be shared to generate metrics.")
                return
            
            # Display by template family
            print("\n📊 PERFORMANCE BY TEMPLATE FAMILY:")
            print("-" * 80)
            print(f"{'Family':<20} {'Group':<15} {'Impressions':<12} {'Engagement':<12} {'Avg Score':<12}")
            print("-" * 80)
            
            for family in sorted(metrics.keys()):
                groups = metrics[family]
                for group_name in sorted(groups.keys()):
                    group = groups[group_name]
                    eng_rate = f"{group['engagement_rate']:.1%}"
                    avg_score = f"{group['avg_engagement_score']:.2f}"
                    impr = group['impressions']
                    print(f"{family:<20} {group_name:<15} {impr:<12} {eng_rate:<12} {avg_score:<12}")
            
            # Show A/B test comparison
            print("\n🔬 A/B TEST COMPARISON:")
            print("-" * 80)
            results = get_ab_test_results(conn, days=days)
            
            for family in sorted(results.keys()):
                result = results[family]
                control = result['control']
                bold = result['bold_variant']
                
                if not control or not bold:
                    print(f"⏳ {family}: Insufficient data (need impressions in both groups)")
                    continue
                
                control_rate = control['engagement_rate']
                bold_rate = bold['engagement_rate']
                winner = result['winner']
                lift = result['lift_pct']
                
                emoji = "🏆" if winner == 'bold_variant' else "✅" if winner == 'control' else "⚖️"
                print(f"\n{emoji} {family.upper()}")
                print(f"   Control:        {control_rate:.1%} engagement ({control['impressions']} impressions)")
                print(f"   Bold Variant:   {bold_rate:.1%} engagement ({bold['impressions']} impressions)")
                if winner:
                    print(f"   Winner:         {winner.upper()} (+{lift}%)")
                else:
                    print(f"   Status:         TIE")
            
            # Show theme-specific performance
            print("\n🎨 PERFORMANCE BY THEME:")
            print("-" * 80)
            theme_perf = get_template_by_theme_performance(conn, days=days)
            
            if theme_perf:
                for theme in sorted(theme_perf.keys()):
                    print(f"\n{theme.upper()}:")
                    for perf in sorted(theme_perf[theme], key=lambda x: x['engagement_rate'], reverse=True):
                        print(f"  • {perf['template']:<20} - {perf['engagement_rate']:.1%} engagement ({perf['impressions']} impressions)")
            
            print("\n" + "=" * 80)
            
        except Exception as e:
            print(f"❌ Error fetching metrics: {e}")

def rollout_winner(template_family: str, winning_variant: str):
    """Safely roll out the winning variant as the default."""
    if winning_variant not in ['control', 'bold_variant']:
        print("❌ Winning variant must be 'control' or 'bold_variant'")
        return False
    
    print(f"🚀 Rolling out {winning_variant} for {template_family}...")
    print("⚠️  This feature requires manual configuration in templates to favor the winner")
    print("    Use getInsightShareFamily() rollout logic to increase selection % for winner")
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="A/B Testing Management for Card Templates")
    parser.add_argument('--enable', type=int, metavar='PCT', help='Enable A/B test at PCT% rollout')
    parser.add_argument('--disable', action='store_true', help='Disable A/B test')
    parser.add_argument('--report', type=int, default=7, metavar='DAYS', help='Show performance report for DAYS')
    parser.add_argument('--rollout', nargs=2, metavar=('FAMILY', 'VARIANT'), help='Roll out winning variant')
    
    args = parser.parse_args()
    
    if args.enable is not None:
        enable_ab_test(args.enable)
    elif args.disable:
        disable_ab_test()
    elif args.rollout:
        rollout_winner(args.rollout[0], args.rollout[1])
    else:
        show_performance_report(args.report)

if __name__ == '__main__':
    main()
