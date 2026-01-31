# Alpha 韧性系统 - 用户指南

**版本**: 1.0
**最后更新**: 2026-01-31

---

## 目录

1. [简介](#简介)
2. [核心能力](#核心能力)
3. [快速开始](#快速开始)
4. [配置选项](#配置选项)
5. [高级特性](#高级特性)
6. [最佳实践](#最佳实践)
7. [故障排查](#故障排查)

---

## 简介

Alpha的**"永不放弃"韧性系统**确保您的任务即使在遇到故障、网络问题或服务中断时也能成功完成。它实现了智能重试策略、自动替代方案探索、失败模式分析和创造性问题解决。

### 核心原则

> **当方法失败时，Alpha自动切换策略、并行探索多个解决方案路径、分析失败以避免重复、设计创造性变通方案，并通过智能迭代持续尝试直到成功或所有选项耗尽。**

---

## 核心能力

### 1. 智能重试与熔断器

- 指数退避加抖动，避免压垮失败的服务
- 重复失败后熔断器打开，快速失败而不浪费时间
- 自动恢复检测（半开状态）

### 2. 替代策略探索

- 主要方法失败时自动发现替代方案
- 根据历史成功率、成本和速度对替代方案排序
- 支持顺序和并行执行

### 3. 失败模式分析

- 检测5种失败模式：重复、级联、间歇、永久、不稳定服务
- 识别根本原因并生成可操作建议
- **新功能**: 跨重启持久化存储，实现跨会话学习

### 4. 策略黑名单

- **新功能**: 自动将重复失败的策略列入黑名单
- 避免在已知失败的方法上浪费时间
- 黑名单在应用重启后持久化

### 5. 创造性问题解决

- LLM驱动的新颖变通方案生成
- 当标准工具不足时生成自定义代码
- 执行前安全验证

### 6. 并行执行

- 同时运行多个策略（竞速模式）
- 第一个成功的获胜，其他自动取消
- 成功时间减少30-50%

---

## 快速开始

### 基础用法

```python
from alpha.core.resilience import ResilienceEngine, ResilienceConfig

# 创建韧性引擎
config = ResilienceConfig(
    max_attempts=5,
    enable_alternatives=True,
    enable_persistence=True  # 启用跨重启学习
)

engine = ResilienceEngine(config)

# 使用韧性执行
async def my_task():
    # 您的代码
    return await fetch_data_from_api()

result = await engine.execute(
    my_task,
    operation_name="fetch_api_data"
)

if result.success:
    print(f"✅ 成功: {result.value}")
else:
    print(f"❌ 失败: {result.error}")
    print(f"📊 建议: {result.recommendations}")
```

### 使用替代策略

```python
from alpha.core.resilience import Strategy

# 定义替代策略
strategies = [
    Strategy(
        name="primary_provider",
        func=fetch_from_provider_a,
        priority=1.0,
        description="主要API提供商"
    ),
    Strategy(
        name="backup_provider",
        func=fetch_from_provider_b,
        priority=0.8,
        description="备份API提供商"
    ),
    Strategy(
        name="cache_fallback",
        func=fetch_from_cache,
        priority=0.5,
        description="缓存数据回退"
    )
]

# 使用替代方案执行（并行模式）
result = await engine.execute_with_alternatives(
    strategies,
    operation_name="fetch_weather_data",
    parallel=True  # 同时尝试所有，第一个成功的获胜
)
```

---

## 配置选项

### ResilienceConfig 配置项

```python
from alpha.core.resilience import ResilienceConfig

config = ResilienceConfig(
    # 重试配置
    max_attempts=5,              # 每个策略的最大重试次数
    base_delay=1.0,              # 初始重试延迟（秒）
    max_delay=60.0,              # 最大重试延迟（秒）
    backoff_factor=2.0,          # 指数退避乘数

    # 资源限制
    max_total_time=300.0,        # 总时间预算（5分钟）
    max_api_cost=1.0,            # API成本限制（$1）
    max_total_attempts=20,       # 所有策略的总尝试次数

    # 替代方案探索
    max_parallel_strategies=3,   # 最大并发策略数
    strategy_timeout=30.0,       # 每个策略的超时（秒）
    enable_alternatives=True,    # 启用自动替代发现
    enable_creative_solving=True, # 启用LLM驱动的创造性解决

    # 失败分析
    pattern_detection_threshold=3,  # 检测模式所需的失败次数
    enable_learning=True,        # 启用失败学习
    enable_persistence=True,     # **新**: 启用SQLite持久化

    # 进度跟踪
    enable_progress_tracking=True,
    checkpoint_interval=60.0,    # 检查点频率（秒）
)
```

### 启用持久化失败学习

**v1.0新功能**: 使用SQLite持久化启用跨重启失败学习：

```python
from alpha.core.resilience import FailureAnalyzer

# 启用持久化（生产环境推荐）
analyzer = FailureAnalyzer(
    pattern_threshold=3,
    enable_persistence=True,
    db_path="data/failures.db"  # 数据库文件路径
)
```

**优势**:
- 应用重启后记住失败
- 策略黑名单持久化
- 30天自动保留
- 失败趋势分析

---

## 高级特性

### 1. 失败模式检测

Alpha检测5种失败模式：

| 模式 | 描述 | 自动操作 |
|------|------|---------|
| **REPEATING** | 相同错误多次出现 | 尝试替代方法 |
| **CASCADING** | 同一操作的不同错误 | 检查依赖项 |
| **INTERMITTENT** | 成功和失败交替 | 实现熔断器 |
| **PERMANENT** | 持续失败 | 重新思考策略 |
| **UNSTABLE_SERVICE** | 同一服务的多种错误类型 | 使用回退提供商 |

### 2. 策略黑名单（新功能）

自动或手动将失败策略列入黑名单：

```python
# 检查策略是否在黑名单中
if analyzer.is_strategy_blacklisted("provider_x", "fetch_data"):
    print("策略在黑名单中，跳过")

# 手动将策略列入黑名单
analyzer.add_to_blacklist(
    strategy_name="failing_provider",
    operation="api_call",
    reason="重复超时错误（10分钟内5次失败）"
)

# 查看所有黑名单策略
blacklist = analyzer.get_blacklist()
for entry in blacklist:
    print(f"{entry['strategy_name']}: {entry['failure_count']} 次失败")

# 从黑名单中移除（问题修复后）
analyzer.remove_from_blacklist("provider_x", "api_call")
```

### 3. 失败分析（新功能）

获取失败趋势洞察：

```python
analytics = analyzer.get_analytics()

print(f"总失败次数: {analytics['total_failures']}")
print(f"黑名单策略: {analytics['blacklisted_strategies']}")

print("\n最常见错误:")
for error in analytics['most_common_errors']:
    print(f"  {error['error_type']}: {error['count']} 次")

print("\n问题操作:")
for op in analytics['problematic_operations']:
    print(f"  {op['operation']}: {op['failure_count']} 次失败")
```

### 4. 自动清理

配置自动清理旧失败记录：

```python
# 清理30天前的失败记录
deleted_count = analyzer.cleanup_old_failures(days=30)
print(f"删除了 {deleted_count} 条旧失败记录")
```

**建议**: 通过cron任务或计划任务每周运行清理。

### 5. 并行 vs 顺序执行

**顺序**（默认）:
- 按优先级顺序逐个尝试策略
- 较低的资源使用
- 可预测的成本

```python
result = await engine.execute_with_alternatives(
    strategies,
    parallel=False
)
```

**并行**（竞速模式）:
- 同时尝试多个策略
- 第一个成功的获胜，其他取消
- 更快的成功时间（减少30-50%）
- 较高的资源使用

```python
result = await engine.execute_with_alternatives(
    strategies,
    parallel=True
)
```

**何时使用并行**:
- 时间关键的操作
- 高价值任务
- 策略成本相似
- 有多个低延迟替代方案可用

---

## 最佳实践

### 1. 生产环境启用持久化

```python
# ✅ 生产环境推荐
config = ResilienceConfig(enable_persistence=True)
```

**优势**:
- 跨重启从过去的失败中学习
- 避免重复失败的策略
- 用于故障排查的分析

### 2. 设置适当的资源限制

```python
config = ResilienceConfig(
    max_total_time=300.0,  # 大多数任务5分钟
    max_api_cost=1.0,      # $1成本限制（根据任务价值调整）
    max_total_attempts=20  # 防止无限循环
)
```

### 3. 定义清晰的操作名称

```python
# ✅ 好: 具体、有意义的名称
await engine.execute(task, operation_name="fetch_user_profile_from_db")

# ❌ 不好: 通用名称
await engine.execute(task, operation_name="fetch_data")
```

**原因**: 操作名称用于失败分组、分析和黑名单。

### 4. 为失败提供上下文

```python
await engine.execute(
    task,
    operation_name="api_call",
    context={
        "endpoint": "/users/123",
        "method": "GET",
        "provider": "service_a"
    }
)
```

**原因**: 上下文有助于识别根本原因并生成更好的建议。

### 5. 定期维护

```python
# 每周清理（例如，通过cron任务）
analyzer.cleanup_old_failures(days=30)

# 每月审查黑名单
blacklist = analyzer.get_blacklist()
# 如果提供商已修复，审查并删除条目
```

---

## 故障排查

### 问题: 失败未持久化

**症状**: 重启后失败未被记住

**解决方案**:
```python
# 确保启用了持久化
analyzer = FailureAnalyzer(enable_persistence=True)

# 检查数据库文件是否存在
import os
assert os.path.exists("data/failures.db")
```

### 问题: 黑名单不起作用

**症状**: 黑名单中的策略仍在尝试

**解决方案**:
```python
# 验证黑名单条目存在
blacklist = analyzer.get_blacklist()
print(blacklist)

# 检查操作名称完全匹配
# 操作名称区分大小写
```

### 问题: 数据库增长过大

**症状**: `failures.db` 文件 > 100MB

**解决方案**:
```python
# 减少保留期
analyzer.cleanup_old_failures(days=14)  # 只保留2周

# 或清除所有（注意：丢失学习数据）
analyzer.store.clear_all()
```

---

## 示例

### 示例1: 简单的韧性API调用

```python
from alpha.core.resilience import ResilienceEngine, ResilienceConfig
import httpx

config = ResilienceConfig(max_attempts=5)
engine = ResilienceEngine(config)

async def fetch_user_data(user_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()

result = await engine.execute(
    fetch_user_data,
    user_id=123,
    operation_name="fetch_user_data"
)

if result.success:
    user = result.value
    print(f"用户: {user['name']}")
```

### 示例2: 多提供商回退

```python
from alpha.core.resilience import Strategy

strategies = [
    Strategy("primary", fetch_from_primary, priority=1.0),
    Strategy("secondary", fetch_from_secondary, priority=0.8),
    Strategy("cache", fetch_from_cache, priority=0.3)
]

result = await engine.execute_with_alternatives(
    strategies,
    operation_name="fetch_critical_data",
    parallel=True  # 同时尝试所有
)
```

### 示例3: 失败分析仪表板

```python
def print_failure_dashboard(analyzer):
    analytics = analyzer.get_analytics()

    print("=" * 50)
    print("失败分析仪表板")
    print("=" * 50)

    print(f"\n📊 总体统计:")
    print(f"  总失败次数: {analytics['total_failures']}")
    print(f"  黑名单策略: {analytics['blacklisted_strategies']}")

    print(f"\n🚫 最常见错误:")
    for i, error in enumerate(analytics['most_common_errors'][:5], 1):
        print(f"  {i}. {error['error_type']}: {error['count']} 次")

    print(f"\n⚠️  问题操作:")
    for i, op in enumerate(analytics['problematic_operations'][:5], 1):
        print(f"  {i}. {op['operation']}: {op['failure_count']} 次失败")

    print("\n" + "=" * 50)

# 每周运行
print_failure_dashboard(analyzer)
```

---

**更多信息**:
- [技术架构](../../docs/internal/resilience_system_design.md)
- [API文档](../../docs/internal/code_execution_api.md)

---

**版本历史**:
- v1.0 (2026-01-31): 添加SQLite持久化、策略黑名单、分析功能
- v0.9 (2026-01-30): 初始发布，包含重试、替代方案、创造性解决
