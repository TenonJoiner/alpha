#!/usr/bin/env python3
"""
Test script for DeepSeek multi-model support and automatic model selection.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alpha.utils.config import load_config
from alpha.llm.service import LLMService, Message
from alpha.llm.model_selector import TaskAnalyzer


async def test_model_selection():
    """Test automatic model selection with different task types."""

    print("=" * 60)
    print("Testing DeepSeek Multi-Model Support")
    print("=" * 60)
    print()

    # Load configuration
    try:
        config = load_config("config.yaml")
        print(f"✓ Configuration loaded successfully")
        print(f"  Default provider: {config.llm.default_provider}")

        # Check DeepSeek configuration
        if 'deepseek' in config.llm.providers:
            deepseek_config = config.llm.providers['deepseek']
            print(f"  DeepSeek default model: {deepseek_config.default_model}")
            print(f"  Auto-select enabled: {deepseek_config.auto_select_model}")
            if deepseek_config.models:
                print(f"  Available models: {', '.join(deepseek_config.models.keys())}")
        print()
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return

    # Create LLM service
    try:
        llm_service = LLMService.from_config(config.llm)
        print(f"✓ LLM service initialized")
        print()
    except Exception as e:
        print(f"✗ Failed to initialize LLM service: {e}")
        return

    # Test cases with different task characteristics
    test_cases = [
        {
            "name": "Simple Question",
            "messages": [
                Message(role="user", content="What is the capital of France?")
            ],
            "expected_difficulty": "simple",
            "expected_model": "deepseek-chat"
        },
        {
            "name": "Coding Task",
            "messages": [
                Message(role="user", content="Write a Python function to calculate fibonacci numbers")
            ],
            "expected_difficulty": "medium",
            "expected_model": "deepseek-coder"
        },
        {
            "name": "Complex Reasoning",
            "messages": [
                Message(role="user", content="""
                Explain the trade-offs between different distributed system consensus algorithms
                like Paxos, Raft, and Byzantine fault tolerance protocols. Compare their performance
                characteristics and use cases.
                """)
            ],
            "expected_difficulty": "expert",
            "expected_model": "deepseek-reasoner"
        },
        {
            "name": "Code Refactoring",
            "messages": [
                Message(role="user", content="""
                Refactor this code to improve performance and maintainability:
                def process_data(data):
                    result = []
                    for item in data:
                        if item > 0:
                            result.append(item * 2)
                    return result
                """)
            ],
            "expected_difficulty": "medium",
            "expected_model": "deepseek-coder"
        },
        {
            "name": "Algorithm Design",
            "messages": [
                Message(role="user", content="""
                Design an efficient algorithm to find the longest increasing subsequence
                in an array. Analyze the time and space complexity.
                """)
            ],
            "expected_difficulty": "complex",
            "expected_model": "deepseek-reasoner"
        }
    ]

    # Run tests
    print("=" * 60)
    print("Testing Task Analysis and Model Selection")
    print("=" * 60)
    print()

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 60)

        # Analyze task
        message_dicts = [{"role": msg.role, "content": msg.content} for msg in test_case["messages"]]
        characteristics = TaskAnalyzer.analyze(message_dicts)

        print(f"  User Query: {test_case['messages'][0].content[:60]}...")
        print(f"  Detected Difficulty: {characteristics.difficulty.value}")
        print(f"  Is Coding Task: {characteristics.is_coding}")
        print(f"  Requires Reasoning: {characteristics.requires_reasoning}")
        print(f"  Estimated Tokens: {characteristics.estimated_tokens}")

        # Check if model selector would work correctly
        deepseek_provider = llm_service.providers.get('deepseek')
        if deepseek_provider and deepseek_provider.model_selector:
            selected_model = deepseek_provider._select_model(test_case["messages"])
            print(f"  Selected Model: {selected_model}")

            # Verify selection
            status = "✓" if selected_model == test_case.get("expected_model") else "⚠"
            print(f"  {status} Expected: {test_case.get('expected_model')}")
        else:
            print(f"  ⚠ Model selector not available")

        print()

    print("=" * 60)
    print("Test Configuration Summary")
    print("=" * 60)
    print()

    if 'deepseek' in config.llm.providers:
        deepseek_config = config.llm.providers['deepseek']
        if deepseek_config.models:
            for model_name, model_config in deepseek_config.models.items():
                print(f"Model: {model_name}")
                print(f"  Max Tokens: {model_config.max_tokens}")
                print(f"  Temperature: {model_config.temperature}")
                print(f"  Difficulty Range: {', '.join(model_config.difficulty_range)}")
                print()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_model_selection())
