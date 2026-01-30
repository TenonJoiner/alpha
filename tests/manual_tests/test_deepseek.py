#!/usr/bin/env python3
"""
测试DeepSeek API集成

测试Alpha对DeepSeek API的支持，包括非流式和流式响应。
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from alpha.llm.service import DeepSeekProvider, Message


async def test_deepseek():
    """测试DeepSeek API"""

    print("=" * 60)
    print("DeepSeek API 集成测试")
    print("=" * 60)

    # 检查API密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not api_key:
        print("\n❌ 错误：未设置 DEEPSEEK_API_KEY")
        print("\n请按以下步骤操作：")
        print("1. 访问 https://platform.deepseek.com/api_keys")
        print("2. 创建API密钥")
        print("3. 设置环境变量:")
        print("   export DEEPSEEK_API_KEY='your-api-key-here'")
        return

    print(f"\n✓ API密钥已设置: {api_key[:20]}...")
    print("✓ Base URL: https://api.deepseek.com")

    # 创建provider
    provider = DeepSeekProvider(
        api_key=api_key,
        model="deepseek-chat",
        max_tokens=4096,
        temperature=0.7
    )

    print("\n" + "=" * 60)
    print("测试开始...")
    print("=" * 60)

    # 测试消息
    messages = [
        Message(role="user", content="用中文简单介绍一下DeepSeek")
    ]

    try:
        # 测试1: 非流式响应
        print("\n[测试 1/2] 非流式响应")
        print("-" * 60)

        response = await provider.complete(messages, max_tokens=200)

        print(f"✓ 请求成功")
        print(f"✓ 模型: {response.model}")
        print(f"✓ Token使用: {response.tokens_used}")
        print(f"✓ 结束原因: {response.finish_reason}")
        print(f"\n响应内容:\n{response.content}")

        # 测试2: 流式响应
        print("\n" + "=" * 60)
        print("[测试 2/2] 流式响应")
        print("-" * 60)

        stream_messages = [
            Message(role="user", content="从1数到5，每个数字单独一行")
        ]

        print("\n流式输出:")
        print("-" * 60)

        response_text = ""
        async for chunk in provider.stream_complete(stream_messages, max_tokens=50):
            print(chunk, end="", flush=True)
            response_text += chunk

        print()
        print("-" * 60)
        print(f"✓ 流式响应成功，共接收 {len(response_text)} 字符")

        # 总结
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

        print("\nDeepSeek API集成成功！")
        print("\n可用的DeepSeek模型:")
        print("  - deepseek-chat: 通用对话模型")
        print("  - deepseek-reasoner: 高级推理模型 (DeepSeek-R1)")
        print("  - deepseek-coder: 代码生成专用模型")

        print("\n在Alpha中使用DeepSeek:")
        print("1. 在config.yaml中设置 default_provider: 'deepseek'")
        print("2. 或在代码中指定: llm_service.complete(messages, provider='deepseek')")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        print(f"\n错误: {e}")

        print("\n可能的原因:")
        print("1. API密钥无效或已过期")
        print("2. 网络连接问题")
        print("3. API服务暂时不可用")
        print("4. 配额已用完")

        print("\n建议:")
        print("1. 检查API密钥是否正确")
        print("2. 访问 https://platform.deepseek.com 检查账户状态")
        print("3. 查看详细日志")

        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()


async def test_all_models():
    """测试所有DeepSeek模型"""

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("跳过多模型测试（未设置API密钥）")
        return

    models = ["deepseek-chat", "deepseek-coder"]

    print("\n" + "=" * 60)
    print("测试所有可用模型")
    print("=" * 60)

    for model in models:
        print(f"\n测试模型: {model}")
        print("-" * 60)

        try:
            provider = DeepSeekProvider(
                api_key=api_key,
                model=model,
                max_tokens=100,
                temperature=0.7
            )

            messages = [Message(role="user", content="Hi")]
            response = await provider.complete(messages, max_tokens=50)

            print(f"✓ {model}: {response.content[:100]}...")

        except Exception as e:
            print(f"✗ {model} 失败: {e}")


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
            logging.FileHandler('logs/deepseek_test.log')
        ]
    )

    print("\n" + "=" * 60)
    print("Alpha - DeepSeek API 测试")
    print("=" * 60)

    # 运行主测试
    asyncio.run(test_deepseek())

    # 如果设置了API密钥，运行扩展测试
    if os.environ.get("DEEPSEEK_API_KEY"):
        asyncio.run(test_all_models())
