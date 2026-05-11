#!/usr/bin/env python3
"""
Test OpenAI compatibility layer for max_tokens vs max_completion_tokens.
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.openai_compat import uses_max_completion_tokens, is_reasoning_chat_model


def test_model_detection():
    """Test that models are correctly identified for parameter compatibility."""
    
    test_cases = [
        # (model_name, should_use_max_completion_tokens, is_reasoning_model)
        ("gpt-4o", True, False),
        ("gpt-4o-mini", True, False),
        ("gpt-4.1", True, False),
        ("gpt-4-2024-11-20", True, False),
        ("gpt-4-turbo-2024-04-09", True, False),
        ("gpt-5", True, True),
        ("gpt-5-mini", True, True),
        ("o1", True, True),
        ("o1-preview", True, True),
        ("gpt-4-turbo", False, False),
        ("gpt-4", False, False),
        ("gpt-3.5-turbo", False, False),
    ]
    
    print("Testing OpenAI model parameter compatibility")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for model, expected_max_completion, expected_reasoning in test_cases:
        uses_max_comp = uses_max_completion_tokens(model)
        is_reasoning = is_reasoning_chat_model(model)
        
        max_comp_ok = uses_max_comp == expected_max_completion
        reasoning_ok = is_reasoning == expected_reasoning
        
        if max_comp_ok and reasoning_ok:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"\n{status}: {model}")
        if not max_comp_ok:
            print(f"  max_completion_tokens: Expected {expected_max_completion}, Got {uses_max_comp}")
        if not reasoning_ok:
            print(f"  is_reasoning: Expected {expected_reasoning}, Got {is_reasoning}")
        
        # Show which parameter should be used
        if uses_max_comp:
            print(f"  → Uses: max_completion_tokens")
        else:
            print(f"  → Uses: max_tokens")
    
    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    return failed == 0


if __name__ == "__main__":
    success = test_model_detection()
    sys.exit(0 if success else 1)
