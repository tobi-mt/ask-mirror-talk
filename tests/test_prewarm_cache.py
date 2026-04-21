#!/usr/bin/env python3
"""Test cache pre-warming with a small subset of questions."""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.prewarm_cache import prewarm_cache

# Test with just 2 questions to speed up testing
TEST_QUESTIONS = [
    "What does courage look like in everyday life?",
    "How do I stop comparing myself to others?",
]

async def test_prewarm():
    """Test pre-warming with a small subset."""
    print("\n🧪 Testing cache pre-warming with 2 sample questions...\n")
    await prewarm_cache(TEST_QUESTIONS, force=False)

if __name__ == "__main__":
    asyncio.run(test_prewarm())
