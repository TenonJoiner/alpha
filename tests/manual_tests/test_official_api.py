#!/usr/bin/env python3
"""
测试官方Anthropic API连接

使用标准API密钥测试，而非Claude Code专用凭证
"""

import asyncio
import os
from alpha.llm.claude_code_client import ClaudeCodeClient


async def test_official_api():
    """测试官方Anthropic API端点"""

    # 检查环境变量
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")

    if not api_key:
        print("❌ 错误：未设置API密钥")
        print("请设置 ANTHROPIC_API_KEY 环境变量")
        return

    print(f"API密钥: {api_key[:20]}...")
    print("目标: 官方Anthropic API (https://api.anthropic.com)")
    print("=" * 60)

    # 使用官方API端点
    client = ClaudeCodeClient(
        api_key=api_key,
        base_url="https://api.anthropic.com"
    )

    try:
        print("\n🚀 测试非流式请求...")
        response = await client.create_message(
            model="claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": "用中文说你好"}],
            max_tokens=100
        )
        print("✅ 成功！")
        print(f"响应: {response['content'][0]['text']}\n")

        print("🚀 测试流式请求...")
        print("响应: ", end="", flush=True)
        async for text in client.stream_message(
            model="claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": "从1数到5"}],
            max_tokens=50
        ):
            print(text, end="", flush=True)
        print("\n")

        print("=" * 60)
        print("✅ 所有测试通过！")
        print("\n建议：")
        print("1. 取消设置 ANTHROPIC_BASE_URL 环境变量")
        print("2. 或将其设置为: export ANTHROPIC_BASE_URL=https://api.anthropic.com")
        print("3. 确保使用标准API密钥，而非Claude Code专用凭证")

    except Exception as e:
        print(f"❌ 错误: {e}")
        print(f"\n错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()

        print("\n可能的解决方案：")
        print("1. 检查API密钥是否有效（访问 https://console.anthropic.com/）")
        print("2. 确认API密钥不是Claude Code专用凭证")
        print("3. 检查网络连接是否正常")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_official_api())
