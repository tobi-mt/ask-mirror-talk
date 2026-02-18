#!/bin/bash
# Daily Railway Log Analysis
# Run: bash scripts/analyze_daily_logs.sh

echo "📊 Daily Ask Mirror Talk - Engagement Report"
echo "==========================================="
echo "Date: $(date)"
echo ""

# Total queries today
TOTAL_QUERIES=$(railway logs --since 24h 2>/dev/null | grep "POST /ask" | wc -l | tr -d ' ')
echo "Total Queries (24h): $TOTAL_QUERIES"
echo ""

# Episode diversity
echo "Top 10 Most Cited Episodes (24h):"
echo "-----------------------------------------"
railway logs --since 24h 2>/dev/null | grep "MMR: Selected" | grep -oE "Episode [0-9]+" | sort | uniq -c | sort -rn | head -10
echo ""

# Unique episodes
UNIQUE_EPISODES=$(railway logs --since 24h 2>/dev/null | grep "MMR: Selected" | grep -oE "Episode [0-9]+" | sort | uniq | wc -l | tr -d ' ')
echo "Unique Episodes Cited (24h): $UNIQUE_EPISODES"
echo ""

# Average candidates used
echo "MMR Candidate Pool (Recent):"
echo "-----------------------------------------"
railway logs --since 24h 2>/dev/null | grep "MMR: Final selection" | tail -5
echo ""

# Error rate
ERRORS=$(railway logs --since 24h 2>/dev/null | grep "ERROR" | wc -l | tr -d ' ')
echo "Errors (24h): $ERRORS"
echo ""

# Health check
echo "API Health Check:"
echo "-----------------------------------------"
HEALTH=$(curl -s https://ask-mirror-talk-production.up.railway.app/health 2>/dev/null)
echo "$HEALTH"
echo ""

echo "==========================================="
echo "✅ Analysis Complete"
echo ""
echo "💡 Quick Interpretation:"
if [ "$TOTAL_QUERIES" -gt 0 ]; then
  echo "  - API is receiving queries ✅"
else
  echo "  - No queries in last 24h ⚠️"
fi

if [ "$UNIQUE_EPISODES" -gt 10 ]; then
  echo "  - Good episode diversity ✅"
else
  echo "  - Low diversity, check MMR ⚠️"
fi

if [ "$ERRORS" -eq 0 ]; then
  echo "  - No errors ✅"
else
  echo "  - $ERRORS errors found ⚠️"
fi
echo ""
