#!/usr/bin/env python3
"""Test cache pre-warming with a small subset of questions."""

import sys
import asyncio
import os
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.prewarm_cache import prewarm_cache

# Test with just 2 questions to speed up testing
TEST_QUESTIONS = [
    "What does courage look like in everyday life?",
    "How do I stop comparing myself to others?",
]

def test_prewarm():
    """Test pre-warming with a small subset."""
    if os.getenv("AMT_RUN_PREWARM_INTEGRATION") != "1":
        pytest.skip("Set AMT_RUN_PREWARM_INTEGRATION=1 to run live cache prewarm integration test.")
    print("\n🧪 Testing cache pre-warming with 2 sample questions...\n")
    asyncio.run(prewarm_cache(TEST_QUESTIONS, force=False))

if __name__ == "__main__":
    asyncio.run(prewarm_cache(TEST_QUESTIONS, force=False))
