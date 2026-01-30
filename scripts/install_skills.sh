#!/bin/bash
# 快速安装热门技能脚本

echo "=================================================="
echo "  Alpha AI - 安装热门技能"
echo "=================================================="
echo ""

echo "📦 可用的热门技能包："
echo ""
echo "1. Vercel Labs (官方推荐) - 4个技能"
echo "   - vercel-composition-patterns   : React组件模式"
echo "   - vercel-react-best-practices   : React/Next.js最佳实践"
echo "   - vercel-react-native-skills    : React Native技能"
echo "   - web-design-guidelines         : Web设计指南"
echo ""
echo "2. Anthropic (Claude官方)"
echo ""

read -p "选择要安装的技能包 (1=Vercel, 2=Anthropic, 3=两者都安装, 0=取消): " choice

case $choice in
    1)
        echo ""
        echo "正在安装 Vercel Labs 技能..."
        npx skills add vercel-labs/agent-skills --all -y
        ;;
    2)
        echo ""
        echo "正在安装 Anthropic 技能..."
        npx skills add anthropics/skills --all -y
        ;;
    3)
        echo ""
        echo "正在安装所有技能..."
        npx skills add vercel-labs/agent-skills --all -y
        npx skills add anthropics/skills --all -y
        ;;
    0)
        echo "取消安装"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "✅ 技能安装完成！"
echo "=================================================="
echo ""
echo "📂 技能已安装到: skills/"
echo ""
echo "下一步："
echo "  1. 运行 'npx skills list' 查看已安装技能"
echo "  2. 运行 './start.sh' 启动 Alpha"
echo "  3. 在 CLI 中输入 'skills' 查看技能状态"
echo ""
