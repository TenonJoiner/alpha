#!/bin/bash
# Alpha API 快速修复脚本

echo "==============================================="
echo "Alpha API 配置快速修复"
echo "==============================================="
echo ""

# 检查环境变量
echo "检查当前配置..."
echo ""

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✓ ANTHROPIC_API_KEY 已设置: ${ANTHROPIC_API_KEY:0:20}..."
else
    echo "✗ ANTHROPIC_API_KEY 未设置"
fi

if [ -n "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "✓ ANTHROPIC_AUTH_TOKEN 已设置: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
else
    echo "✗ ANTHROPIC_AUTH_TOKEN 未设置"
fi

if [ -n "$ANTHROPIC_BASE_URL" ]; then
    echo "✓ ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
else
    echo "○ ANTHROPIC_BASE_URL 未设置 (将使用默认官方API)"
fi

echo ""
echo "==============================================="
echo ""

# 检查是否至少有一个API密钥
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "❌ 错误：未设置任何API密钥"
    echo ""
    echo "请选择一个配置方式："
    echo ""
    echo "方案1 - 使用官方Anthropic API (推荐):"
    echo "  export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'"
    echo "  unset ANTHROPIC_BASE_URL"
    echo ""
    echo "方案2 - 使用moacode.org代理 + fallback:"
    echo "  export ANTHROPIC_AUTH_TOKEN='your-claude-code-token'"
    echo "  export ANTHROPIC_BASE_URL='https://moacode.org'"
    echo "  export ANTHROPIC_API_KEY='sk-ant-api03-standard-key'  # fallback"
    echo ""
    exit 1
fi

echo "建议的配置："
echo ""

# 根据当前配置给出建议
if [ -n "$ANTHROPIC_BASE_URL" ] && [ "$ANTHROPIC_BASE_URL" != "https://api.anthropic.com" ]; then
    echo "您正在使用代理: $ANTHROPIC_BASE_URL"
    echo ""
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "⚠️  建议：设置 ANTHROPIC_API_KEY 作为fallback"
        echo ""
        echo "  export ANTHROPIC_API_KEY='sk-ant-api03-your-standard-key'"
        echo ""
        echo "这样当代理失败时，会自动切换到官方API"
    else
        echo "✓ 已配置fallback API密钥"
        echo "  代理失败时会自动切换到官方API"
    fi
else
    echo "✓ 配置正确，使用官方Anthropic API"
fi

echo ""
echo "==============================================="
echo ""
echo "运行测试脚本验证配置："
echo "  python test_fallback.py"
echo ""
echo "或直接启动Alpha："
echo "  ./start.sh"
echo ""
