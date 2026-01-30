#!/usr/bin/env python3
"""
快速测试Alpha的API fallback机制
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from alpha.llm.service import LLMService, Message, AnthropicProvider


async def test_fallback():
    """测试fallback机制"""

    print("=" * 60)
    print("Alpha API Fallback 测试")
    print("=" * 60)

    # 检查环境变量
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

    print(f"\n当前配置:")
    print(f"  ANTHROPIC_AUTH_TOKEN: {'✓ 已设置' if auth_token else '✗ 未设置'}")
    print(f"  ANTHROPIC_API_KEY: {'✓ 已设置' if api_key else '✗ 未设置'}")
    print(f"  ANTHROPIC_BASE_URL: {base_url}")

    # 使用的API密钥
    using_key = api_key or auth_token
    if not using_key:
        print("\n❌ 错误：未设置API密钥")
        print("请设置 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN")
        return

    print(f"\n使用API密钥: {using_key[:20]}...")

    # 创建provider
    provider = AnthropicProvider(
        api_key=using_key,
        model="claude-sonnet-4-5-20250929",
        base_url=base_url
    )

    # 测试消息
    messages = [
        Message(role="user", content="用中文说你好")
    ]

    print("\n" + "=" * 60)
    print("开始测试...")
    print("=" * 60)

    try:
        print("\n🚀 测试流式响应...")
        print("Alpha: ", end="", flush=True)

        response_text = ""
        async for chunk in provider.stream_complete(messages):
            print(chunk, end="", flush=True)
            response_text += chunk

        print("\n")

        if response_text:
            print("=" * 60)
            print("✅ 测试成功！")
            print("=" * 60)

            # 显示使用的endpoint
            if "Falling back" in str(provider):
                print("\n提示：使用了fallback到官方API")
            else:
                print(f"\n提示：成功连接到 {base_url}")

            print("\n您可以使用以下方式之一配置Alpha：")
            print("\n方案1 - 仅使用官方API (推荐):")
            print("  export ANTHROPIC_API_KEY='sk-ant-api03-...'")
            print("  unset ANTHROPIC_BASE_URL")
            print("\n方案2 - 使用proxy + fallback:")
            print("  export ANTHROPIC_AUTH_TOKEN='your-claude-code-token'")
            print("  export ANTHROPIC_BASE_URL='https://moacode.org'")
            print("  export ANTHROPIC_API_KEY='sk-ant-api03-...'  # fallback密钥")

    except Exception as e:
        print("\n")
        print("=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        print(f"\n错误: {e}")

        print("\n可能的原因：")
        print("1. API密钥无效或已过期")
        print("2. 网络连接问题")
        print("3. 模型名称不正确")
        print("4. 两个endpoint都失败了")

        print("\n建议：")
        print("1. 检查API密钥是否有效（访问 https://console.anthropic.com/）")
        print("2. 如果使用代理，确保fallback API密钥已设置")
        print("3. 查看详细日志：tail -f logs/alpha.log")

        import traceback
        print("\n详细错误信息：")
        traceback.print_exc()


if __name__ == "__main__":
    # 创建logs目录
    Path("logs").mkdir(exist_ok=True)

    # 配置日志
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/fallback_test.log')
        ]
    )

    asyncio.run(test_fallback())
