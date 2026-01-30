"""
Test Query Classifier

Validates the query classification logic.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alpha.skills.query_classifier import QueryClassifier


def test_query_classifier():
    """Test query classifier with various inputs."""
    classifier = QueryClassifier()

    # Test cases: (query, expected_type, expected_needs_skill_matching)
    test_cases = [
        # Simple queries
        ("exot", "simple", False),
        ("hi", "simple", False),
        ("你好", "simple", False),
        ("test", "simple", False),

        # Questions (no skills needed)
        ("what is python", "question", False),
        ("为什么简单的问题响应时间也比较长", "question", False),
        ("how do I learn python?", "question", False),
        ("tell me about machine learning", "question", False),

        # Commands
        ("help", "command", False),
        ("status", "command", False),
        ("skills", "command", False),

        # Tasks (needs skills)
        ("create a pdf document", "task", True),
        ("generate a report", "task", True),
        ("帮我创建一个PDF", "task", True),
        ("analyze this data", "task", True),
        ("convert json to csv", "task", True),
        ("build a react component", "task", True),
        ("fix the bug in auth.py", "task", True),
        ("read the excel file data.xlsx", "task", True),

        # Edge cases
        ("", "simple", False),
        ("   ", "simple", False),
        ("This is a longer query that doesn't have clear task indicators", "task", True),  # Long = task by default
    ]

    print("=" * 80)
    print("Query Classifier Test Results")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for query, expected_type, expected_needs_skill in test_cases:
        result = classifier.classify(query)

        type_match = result['type'] == expected_type
        skill_match = result['needs_skill_matching'] == expected_needs_skill

        status = "✓ PASS" if (type_match and skill_match) else "✗ FAIL"

        if type_match and skill_match:
            passed += 1
        else:
            failed += 1

        # Format output
        query_display = query if query else "(empty)"
        print(f"{status:8} | Query: {query_display[:50]:50}")
        print(f"         | Expected: {expected_type:10} needs_skill={expected_needs_skill}")
        print(f"         | Got:      {result['type']:10} needs_skill={result['needs_skill_matching']} "
              f"(confidence={result['confidence']:.2f})")

        if not (type_match and skill_match):
            print(f"         | ❌ Mismatch!")

        print()

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = test_query_classifier()
    sys.exit(0 if success else 1)
