#!/usr/bin/env python3
"""
Test the incomplete answer detection function.
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.qa.service import _is_incomplete_answer


def test_incomplete_answer_detection():
    """Test various cases of complete and incomplete answers."""
    
    test_cases = [
        # (answer_text, expected_is_incomplete, description)
        ("", True, "Empty answer"),
        ("Too short", True, "Too short answer"),
        (
            "This is a complete answer that ends properly with multiple sentences. "
            "It has enough content and ends with proper punctuation. "
            "Everything looks good here.",
            False,
            "Complete answer with proper ending"
        ),
        (
            "That's such a poignant question, especially in a world where hustle is often glorified. "
            "When we think about rest in a culture that pushes us to constantly chase our goals, it "
            "can feel like an elusive concept—almost like trying to catch smoke with your bare "
            "hands. From the podcast discussions, it's clear that true rest isn",
            True,
            "Incomplete answer ending with 'rest isn'"
        ),
        (
            "This is a good answer that has substance and",
            True,
            "Answer ending with 'and'"
        ),
        (
            "The answer is that",
            True,
            "Answer ending with 'that'"
        ),
        (
            "You need to understand the",
            True,
            "Answer ending with 'the'"
        ),
        (
            "This answer doesn't end with punctuation",
            True,
            "No ending punctuation"
        ),
        (
            "This is a complete answer! It has proper punctuation and enough content. "
            "The key insight is to be present and intentional. "
            "This means taking time to truly disconnect and rest.",
            False,
            "Complete answer with exclamation"
        ),
        (
            "What is truly important? It's about finding balance in your life. "
            "Rest isn't just the absence of work; it's the presence of peace. "
            "Take time to discover what that means for you.",
            False,
            "Complete answer with question in the middle"
        ),
        (
            "This answer has good content but ends with a preposition to",
            True,
            "Ending with preposition 'to'"
        ),
        (
            "The best approach is to take small steps. Start with five minutes a day. "
            "Notice how it feels to simply be without doing anything productive. "
            "That's where real rest begins.",
            False,
            "Complete practical answer"
        ),
    ]
    
    print("Testing incomplete answer detection")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for answer, expected_incomplete, description in test_cases:
        result = _is_incomplete_answer(answer)
        status = "✓ PASS" if result == expected_incomplete else "✗ FAIL"
        
        if result == expected_incomplete:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status}: {description}")
        print(f"  Expected incomplete: {expected_incomplete}, Got: {result}")
        if answer:
            preview = answer[:100] + "..." if len(answer) > 100 else answer
            print(f"  Text: {preview}")
            if len(answer) > 0:
                print(f"  Ends with: '...{answer[-30:]}'")
    
    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    return failed == 0


if __name__ == "__main__":
    success = test_incomplete_answer_detection()
    sys.exit(0 if success else 1)
