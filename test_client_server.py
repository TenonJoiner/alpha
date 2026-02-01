#!/usr/bin/env python3
"""
Test script for Client-Server architecture

This script tests the basic functionality without starting the full server.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from alpha.api.chat_handler import ChatHandler
from alpha.core.engine import AlphaEngine
from alpha.utils.config import load_config
from alpha.llm.service import LLMService
from alpha.tools.registry import create_default_registry
from alpha.skills.executor import SkillExecutor


async def test_chat_handler():
    """Test ChatHandler functionality."""
    print("=" * 60)
    print("Testing Alpha Client-Server Architecture")
    print("=" * 60)
    print()

    # Load config
    print("1. Loading configuration...")
    config = load_config('config.yaml')
    print(f"   ✓ Config loaded: {config.name}")
    print()

    # Create engine
    print("2. Creating AlphaEngine...")
    engine = AlphaEngine(config)
    await engine.startup()
    print("   ✓ Engine started")
    print()

    # Create LLM service
    print("3. Creating LLM service...")
    llm_service = LLMService.from_config(config.llm)
    print("   ✓ LLM service created")
    print()

    # Create tool registry
    print("4. Creating tool registry...")
    tool_registry = create_default_registry(llm_service, config)
    print("   ✓ Tool registry created")
    print()

    # Create chat handler
    print("5. Creating ChatHandler...")
    chat_handler = ChatHandler(
        engine=engine,
        llm_service=llm_service,
        tool_registry=tool_registry,
        skill_executor=None,
        auto_skill_manager=None
    )
    print("   ✓ ChatHandler created")
    print()

    # Test message processing
    print("6. Testing message processing...")
    test_message = "Hello, Alpha! This is a test."
    print(f"   User: {test_message}")
    print("   Alpha: ", end="", flush=True)

    response_chunks = []
    async for chunk in chat_handler.process_message(test_message, stream=True):
        if chunk['type'] == 'text':
            response_chunks.append(chunk['content'])
            print(chunk['content'], end="", flush=True)
        elif chunk['type'] == 'status':
            print(f"\n   [{chunk['content']}]", flush=True)
        elif chunk['type'] == 'done':
            print()
            break

    print()
    print("   ✓ Message processed successfully")
    print()

    # Get stats
    print("7. Getting chat statistics...")
    stats = chat_handler.get_stats()
    print(f"   Messages: {stats['messages_count']}")
    print(f"   User: {stats['user_messages']}, Assistant: {stats['assistant_messages']}")
    print()

    # Cleanup
    print("8. Shutting down...")
    await engine.shutdown()
    print("   ✓ Engine stopped")
    print()

    print("=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Start server: bin/alpha start")
    print("  2. Connect client: bin/alpha chat")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(test_chat_handler())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
