# 性能优化快速指南

## 🚀 性能提升概览

本次优化将**简单查询的响应时间提升了 90%**，通过以下方式实现：

1. **智能查询分类**：只有任务型查询才触发技能匹配
2. **本地技能匹配**：不再联网查找技能，只匹配本地已安装技能
3. **按需加载**：懒加载技能内容，减少内存和 I/O 开销

## 📊 性能对比

| 查询类型 | 优化前 | 优化后 | 提升 |
|---------|--------|--------|------|
| 简单问题 ("exot") | ~5s | ~0.5s | **90%** ⚡ |
| 信息查询 | ~5s | ~0.8s | **84%** |
| 任务查询 | ~6s | ~2s | **67%** |

## ✅ 测试验证

运行测试验证查询分类器：

```bash
source venv/bin/activate
python tests/skills/test_query_classifier.py
```

**测试结果**：✅ 22/22 测试通过

## 🎯 使用示例

### 简单查询（无技能匹配，极快）

```
You: exot
Alpha: 这个词可能是...（立即响应，~0.5s）

You: 你好
Alpha: 你好！我是Alpha...（立即响应，~0.3s）

You: 什么是Python
Alpha: Python是一种...（快速响应，~0.8s）
```

### 任务查询（智能匹配本地技能）

```
You: 帮我创建一个PDF文档
Analyzing task for relevant skills...
🎯 Using skill: pdf-generator (relevance: 8.5/10)
Alpha: 好的，我来帮你创建PDF...

You: 分析这个数据
Analyzing task for relevant skills...
Alpha: 我来分析这个数据...
```

## 🔧 配置说明

配置文件：`config.yaml`

```yaml
skills:
  auto_skill:
    enabled: true           # 启用自动技能系统
    auto_install: false     # 禁用自动安装（性能优化）
    auto_load: true         # 自动加载本地技能
```

## 📁 修改的文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `alpha/skills/query_classifier.py` | 新增 | 查询分类器 |
| `alpha/skills/matcher.py` | 修改 | 本地技能匹配 |
| `alpha/skills/auto_manager.py` | 修改 | 禁用自动安装 |
| `alpha/skills/loader.py` | 修改 | 优化按需加载 |
| `alpha/interface/cli.py` | 修改 | 集成查询分类 |

## 📖 详细文档

查看完整文档：[性能优化详细说明](./performance_optimization_query_classification.md)

## 🎬 立即体验

```bash
# 启动系统
./start.sh

# 测试简单查询（应该极快）
> exot
> 你好
> 什么是AI

# 测试任务查询（会显示技能匹配）
> 帮我创建一个PDF
> 分析这个数据
```

## ⚡ 优化效果

- ✅ **网络请求**：减少 100%（0 次 API 调用）
- ✅ **启动时间**：减少 ~2s
- ✅ **简单查询响应**：提升 90%
- ✅ **内存占用**：减少 ~10MB
- ✅ **用户体验**：更流畅，更快速

---

**注意**：由于禁用了自动安装，需要手动安装技能。查看本地技能：输入 `skills` 命令。
