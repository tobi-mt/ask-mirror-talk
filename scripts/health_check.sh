#!/bin/bash

# Quick Health Check Script for Ask Mirror Talk API
# Tests deployment, API endpoints, and response quality

set -e  # Exit on error

API_URL="https://ask-mirror-talk-production.up.railway.app"

echo "========================================"
echo "Ask Mirror Talk - Health Check"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq not found. Install with: brew install jq${NC}"
    echo "Continuing without JSON formatting..."
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

echo "Testing API URL: $API_URL"
echo ""

# Test 1: Health Check
echo "1️⃣  Health Check..."
echo "-----------------------------------"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Status: OK (HTTP $HTTP_CODE)${NC}"
    if [ "$JQ_AVAILABLE" = true ]; then
        echo "$BODY" | jq '.'
    else
        echo "$BODY"
    fi
else
    echo -e "${RED}❌ Status: Failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
fi
echo ""

# Test 2: Status Check
echo "2️⃣  Status Check..."
echo "-----------------------------------"
STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/status")
HTTP_CODE=$(echo "$STATUS_RESPONSE" | tail -n1)
BODY=$(echo "$STATUS_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Status: OK (HTTP $HTTP_CODE)${NC}"
    if [ "$JQ_AVAILABLE" = true ]; then
        echo "$BODY" | jq '.'
        EPISODE_COUNT=$(echo "$BODY" | jq -r '.episodes')
        CHUNK_COUNT=$(echo "$BODY" | jq -r '.chunks')
        echo ""
        echo "Episodes loaded: $EPISODE_COUNT"
        echo "Chunks available: $CHUNK_COUNT"
        
        if [ "$EPISODE_COUNT" -lt 3 ]; then
            echo -e "${YELLOW}⚠️  Warning: Only $EPISODE_COUNT episodes loaded. Consider running full ingestion.${NC}"
        fi
    else
        echo "$BODY"
    fi
else
    echo -e "${RED}❌ Status: Failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
fi
echo ""

# Test 3: Simple Question
echo "3️⃣  Test Question..."
echo "-----------------------------------"
echo "Question: 'What is alignment?'"
echo ""

QUESTION_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is alignment?"}')
HTTP_CODE=$(echo "$QUESTION_RESPONSE" | tail -n1)
BODY=$(echo "$QUESTION_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Response: OK (HTTP $HTTP_CODE)${NC}"
    echo ""
    
    if [ "$JQ_AVAILABLE" = true ]; then
        # Extract and display answer
        ANSWER=$(echo "$BODY" | jq -r '.answer')
        CITATIONS_COUNT=$(echo "$BODY" | jq '.citations | length')
        
        echo "Answer (first 300 chars):"
        echo "-----------------------------------"
        echo "$ANSWER" | head -c 300
        echo "..."
        echo ""
        echo "Citations: $CITATIONS_COUNT episodes referenced"
        echo ""
        
        # Check for quality indicators
        echo "Quality Checks:"
        echo "-----------------------------------"
        
        # Check 1: Answer length
        ANSWER_LENGTH=${#ANSWER}
        if [ $ANSWER_LENGTH -gt 200 ]; then
            echo -e "${GREEN}✅ Answer length: $ANSWER_LENGTH chars (substantial response)${NC}"
        else
            echo -e "${YELLOW}⚠️  Answer length: $ANSWER_LENGTH chars (might be too short)${NC}"
        fi
        
        # Check 2: Has citations
        if [ $CITATIONS_COUNT -gt 0 ]; then
            echo -e "${GREEN}✅ Citations: $CITATIONS_COUNT episodes referenced${NC}"
        else
            echo -e "${RED}❌ No citations found${NC}"
        fi
        
        # Check 3: Check for incomplete sentences
        if echo "$ANSWER" | grep -q "^And " || echo "$ANSWER" | grep -q "^So, I don't"; then
            echo -e "${RED}❌ Warning: Possible incomplete sentences detected${NC}"
        else
            echo -e "${GREEN}✅ No obvious incomplete sentences${NC}"
        fi
        
        # Check 4: Timestamp format in citations
        echo ""
        echo "Citation Details:"
        echo "-----------------------------------"
        echo "$BODY" | jq -r '.citations[] | "Episode: \(.episode_title)\nTimestamp: \(.timestamp)\nURL: \(.episode_url)\n"' | head -20
        
        # Check if timestamps are in correct format
        FIRST_URL=$(echo "$BODY" | jq -r '.citations[0].episode_url // empty')
        if [[ $FIRST_URL == *"#t="* ]]; then
            echo -e "${GREEN}✅ Timestamps: Using correct #t=seconds format${NC}"
        elif [ ! -z "$FIRST_URL" ]; then
            echo -e "${YELLOW}⚠️  Timestamps: May not have correct format${NC}"
        fi
        
        # Check for duplicate episodes in citations
        UNIQUE_EPISODES=$(echo "$BODY" | jq -r '[.citations[].episode_id] | unique | length')
        TOTAL_CITATIONS=$CITATIONS_COUNT
        if [ "$UNIQUE_EPISODES" = "$TOTAL_CITATIONS" ]; then
            echo -e "${GREEN}✅ Deduplication: All citations are from unique episodes${NC}"
        else
            echo -e "${YELLOW}⚠️  Deduplication: Some episodes may be duplicated ($UNIQUE_EPISODES unique out of $TOTAL_CITATIONS)${NC}"
        fi
        
    else
        echo "$BODY"
    fi
else
    echo -e "${RED}❌ Response: Failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
fi
echo ""

# Test 4: CORS Check (if curl supports it)
echo "4️⃣  CORS Check..."
echo "-----------------------------------"
CORS_RESPONSE=$(curl -s -H "Origin: https://mirrortalkpodcast.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS "$API_URL/ask" -i | grep -i "access-control-allow-origin" || echo "")

if [ ! -z "$CORS_RESPONSE" ]; then
    echo -e "${GREEN}✅ CORS headers present${NC}"
    echo "$CORS_RESPONSE"
else
    echo -e "${YELLOW}⚠️  Could not verify CORS headers (may need to test in browser)${NC}"
fi
echo ""

# Summary
echo "========================================"
echo "Summary"
echo "========================================"
echo ""
echo "Next Steps:"
echo "1. If all tests passed ✅ - API is ready for production"
echo "2. If episodes < 10 - Consider running full ingestion"
echo "3. Test WordPress widget on live site"
echo "4. Verify in multiple browsers (Chrome, Safari, Firefox)"
echo "5. Clear browser cache and test again"
echo ""
echo "For detailed logs, run: railway logs --tail"
echo "For WordPress testing, see: WORDPRESS_UPDATE_GUIDE.md"
echo ""
