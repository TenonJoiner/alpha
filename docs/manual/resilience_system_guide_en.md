# Alpha Resilience System - User Guide

**Version**: 1.0
**Last Updated**: 2026-01-31

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Capabilities](#core-capabilities)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## Introduction

Alpha's **"Never Give Up" Resilience System** ensures that your tasks complete successfully even when encountering failures, network issues, or service outages. It implements intelligent retry strategies, automatic alternative exploration, failure pattern analysis, and creative problem-solving.

### Key Principle

> **When approaches fail, Alpha automatically switches strategies, explores multiple solution paths in parallel, analyzes failures to avoid repetition, devises creative workarounds, and persists with intelligent iteration until success or all options exhausted.**

---

## Core Capabilities

### 1. Intelligent Retry with Circuit Breaker

- Exponential backoff with jitter prevents overwhelming failing services
- Circuit breaker opens after repeated failures, fails fast instead of wasting time
- Automatic recovery detection (half-open state)

### 2. Alternative Strategy Exploration

- Automatically discovers alternative approaches when primary fails
- Ranks alternatives by historical success rate, cost, and speed
- Supports both sequential and parallel execution

### 3. Failure Pattern Analysis

- Detects 5 failure patterns: REPEATING, CASCADING, INTERMITTENT, PERMANENT, UNSTABLE_SERVICE
- Identifies root causes and generates actionable recommendations
- **NEW**: Persistent storage across restarts for cross-session learning

### 4. Strategy Blacklisting

- **NEW**: Automatically blacklists strategies that fail repeatedly
- Prevents wasting time on known-bad approaches
- Persistent blacklist across application restarts

### 5. Creative Problem Solving

- LLM-powered generation of novel workarounds
- Generates custom code when standard tools insufficient
- Safety validation before execution

### 6. Parallel Execution

- Runs multiple strategies concurrently (race condition)
- First success wins, others auto-canceled
- Reduces time-to-success by 30-50%

---

## Quick Start

### Basic Usage

```python
from alpha.core.resilience import ResilienceEngine, ResilienceConfig

# Create resilience engine
config = ResilienceConfig(
    max_attempts=5,
    enable_alternatives=True,
    enable_persistence=True  # Enable cross-restart learning
)

engine = ResilienceEngine(config)

# Execute with resilience
async def my_task():
    # Your code here
    return await fetch_data_from_api()

result = await engine.execute(
    my_task,
    operation_name="fetch_api_data"
)

if result.success:
    print(f"✅ Success: {result.value}")
else:
    print(f"❌ Failed: {result.error}")
    print(f"📊 Recommendations: {result.recommendations}")
```

### With Alternative Strategies

```python
from alpha.core.resilience import Strategy

# Define alternative strategies
strategies = [
    Strategy(
        name="primary_provider",
        func=fetch_from_provider_a,
        priority=1.0,
        description="Primary API provider"
    ),
    Strategy(
        name="backup_provider",
        func=fetch_from_provider_b,
        priority=0.8,
        description="Backup API provider"
    ),
    Strategy(
        name="cache_fallback",
        func=fetch_from_cache,
        priority=0.5,
        description="Cached data fallback"
    )
]

# Execute with alternatives (parallel mode)
result = await engine.execute_with_alternatives(
    strategies,
    operation_name="fetch_weather_data",
    parallel=True  # Try all at once, first success wins
)
```

---

## Configuration

### ResilienceConfig Options

```python
from alpha.core.resilience import ResilienceConfig

config = ResilienceConfig(
    # Retry configuration
    max_attempts=5,              # Maximum retry attempts per strategy
    base_delay=1.0,              # Initial retry delay (seconds)
    max_delay=60.0,              # Maximum retry delay (seconds)
    backoff_factor=2.0,          # Exponential backoff multiplier

    # Resource limits
    max_total_time=300.0,        # Total time budget (5 minutes)
    max_api_cost=1.0,            # API cost limit ($1)
    max_total_attempts=20,       # Total attempts across all strategies

    # Alternative exploration
    max_parallel_strategies=3,   # Max concurrent strategies
    strategy_timeout=30.0,       # Timeout per strategy (seconds)
    enable_alternatives=True,    # Enable automatic alternative discovery
    enable_creative_solving=True, # Enable LLM-powered creative solving

    # Creative solver
    enable_custom_code=True,     # Allow code generation
    creative_solver_provider="deepseek",  # LLM provider

    # Failure analysis
    pattern_detection_threshold=3,  # Failures needed to detect pattern
    enable_learning=True,        # Enable failure learning
    enable_persistence=True,     # **NEW**: Enable SQLite persistence

    # Progress tracking
    enable_progress_tracking=True,
    checkpoint_interval=60.0,    # Checkpoint frequency (seconds)

    # Escalation
    escalate_after_failures=10,  # Escalate after N failures
    user_intervention_threshold=15  # Request user help after N failures
)
```

### Enabling Persistent Failure Learning

**NEW in v1.0**: Enable cross-restart failure learning with SQLite persistence:

```python
from alpha.core.resilience import FailureAnalyzer

# Enable persistence (recommended for production)
analyzer = FailureAnalyzer(
    pattern_threshold=3,
    enable_persistence=True,
    db_path="data/failures.db"  # Database file path
)
```

**Benefits**:
- Failures remembered across application restarts
- Strategy blacklist persists
- 30-day automatic retention
- Analytics on failure trends

---

## Advanced Features

### 1. Failure Pattern Detection

Alpha detects 5 types of failure patterns:

| Pattern | Description | Auto-Action |
|---------|-------------|-------------|
| **REPEATING** | Same error multiple times | Try alternative approach |
| **CASCADING** | Different errors from same operation | Check dependencies |
| **INTERMITTENT** | Alternating success/failure | Implement circuit breaker |
| **PERMANENT** | Consistent failure | Rethink strategy |
| **UNSTABLE_SERVICE** | Multiple error types from same service | Use fallback provider |

**Example**:
```python
# Analyze failure patterns
analysis = analyzer.analyze_pattern()

print(f"Pattern: {analysis.pattern}")
print(f"Root Cause: {analysis.root_cause.description}")
print(f"Recommendations:")
for rec in analysis.recommendations:
    print(f"  - {rec}")
```

### 2. Strategy Blacklisting (NEW)

Automatically or manually blacklist failing strategies:

```python
# Check if strategy is blacklisted
if analyzer.is_strategy_blacklisted("provider_x", "fetch_data"):
    print("Strategy is blacklisted, skipping")

# Manually blacklist a strategy
analyzer.add_to_blacklist(
    strategy_name="failing_provider",
    operation="api_call",
    reason="Repeated timeout errors (5 failures in 10 minutes)"
)

# View all blacklisted strategies
blacklist = analyzer.get_blacklist()
for entry in blacklist:
    print(f"{entry['strategy_name']}: {entry['failure_count']} failures")

# Remove from blacklist (after issue fixed)
analyzer.remove_from_blacklist("provider_x", "api_call")
```

### 3. Failure Analytics (NEW)

Get insights into failure trends:

```python
analytics = analyzer.get_analytics()

print(f"Total failures: {analytics['total_failures']}")
print(f"Blacklisted strategies: {analytics['blacklisted_strategies']}")

print("\nMost common errors:")
for error in analytics['most_common_errors']:
    print(f"  {error['error_type']}: {error['count']} times")

print("\nProblematic operations:")
for op in analytics['problematic_operations']:
    print(f"  {op['operation']}: {op['failure_count']} failures")

print("\nDaily trends (last 7 days):")
for trend in analytics['daily_trends']:
    print(f"  {trend['date']}: {trend['count']} failures")
```

### 4. Automatic Cleanup

Configure automatic cleanup of old failures:

```python
# Cleanup failures older than 30 days
deleted_count = analyzer.cleanup_old_failures(days=30)
print(f"Deleted {deleted_count} old failure records")
```

**Recommendation**: Run cleanup weekly via cron job or scheduled task.

### 5. Parallel vs Sequential Execution

**Sequential** (default):
- Tries strategies one by one in priority order
- Lower resource usage
- Predictable cost

```python
result = await engine.execute_with_alternatives(
    strategies,
    parallel=False
)
```

**Parallel** (race mode):
- Tries multiple strategies concurrently
- First success wins, others canceled
- Faster time-to-success (30-50% reduction)
- Higher resource usage

```python
result = await engine.execute_with_alternatives(
    strategies,
    parallel=True
)
```

**When to use parallel**:
- Time-critical operations
- High-value tasks
- Strategies have similar cost
- Multiple low-latency alternatives available

---

## Best Practices

### 1. Enable Persistence in Production

```python
# ✅ RECOMMENDED for production
config = ResilienceConfig(enable_persistence=True)
```

**Benefits**:
- Learn from past failures across restarts
- Avoid repeating failed strategies
- Analytics for troubleshooting

### 2. Set Appropriate Resource Limits

```python
config = ResilienceConfig(
    max_total_time=300.0,  # 5 minutes for most tasks
    max_api_cost=1.0,      # $1 cost limit (adjust per task value)
    max_total_attempts=20  # Prevent infinite loops
)
```

### 3. Define Clear Operation Names

```python
# ✅ Good: Specific, meaningful names
await engine.execute(task, operation_name="fetch_user_profile_from_db")

# ❌ Bad: Generic names
await engine.execute(task, operation_name="fetch_data")
```

**Why**: Operation names used for failure grouping, analytics, and blacklisting.

### 4. Provide Context for Failures

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

**Why**: Context helps identify root causes and generate better recommendations.

### 5. Regular Maintenance

```python
# Weekly cleanup (e.g., via cron job)
analyzer.cleanup_old_failures(days=30)

# Monthly review of blacklist
blacklist = analyzer.get_blacklist()
# Review and remove entries if providers fixed
```

### 6. Monitor Analytics

```python
# Daily/weekly analytics review
analytics = analyzer.get_analytics()

if analytics['total_failures'] > threshold:
    alert_operations_team(analytics['problematic_operations'])
```

---

## Troubleshooting

### Problem: Failures Not Persisting

**Symptom**: Failures not remembered after restart

**Solution**:
```python
# Ensure persistence is enabled
analyzer = FailureAnalyzer(enable_persistence=True)

# Check database file exists
import os
assert os.path.exists("data/failures.db")
```

### Problem: Blacklist Not Working

**Symptom**: Blacklisted strategies still being tried

**Solution**:
```python
# Verify blacklist entry exists
blacklist = analyzer.get_blacklist()
print(blacklist)

# Check operation name matches exactly
# Operation names are case-sensitive
```

### Problem: Database Growing Too Large

**Symptom**: `failures.db` file > 100MB

**Solution**:
```python
# Reduce retention period
analyzer.cleanup_old_failures(days=14)  # Keep only 2 weeks

# Or clear all (caution: loses learning data)
analyzer.store.clear_all()
```

### Problem: Too Many Retries

**Symptom**: Tasks taking too long due to excessive retries

**Solution**:
```python
# Reduce max attempts
config = ResilienceConfig(
    max_attempts=3,  # Instead of default 5
    max_total_time=60.0,  # 1 minute timeout
    max_total_attempts=10  # Lower total limit
)
```

---

## API Reference

### ResilienceEngine

```python
ResilienceEngine(config: ResilienceConfig)
```

**Methods**:

- `async execute(func, *args, operation_name: str, context: dict = None, **kwargs) -> ResilienceResult`
  - Execute function with resilience

- `async execute_with_alternatives(strategies: List[Strategy], operation_name: str, parallel: bool = False) -> ResilienceResult`
  - Execute with alternative strategies

### FailureAnalyzer

```python
FailureAnalyzer(
    pattern_threshold: int = 3,
    enable_persistence: bool = False,
    db_path: str = "data/failures.db"
)
```

**Methods**:

- `record_failure(error: Exception, operation: str, context: dict = None) -> Failure`
- `analyze_pattern(failures: List[Failure] = None) -> FailureAnalysis`
- `is_strategy_blacklisted(strategy_name: str, operation: str) -> bool`
- `add_to_blacklist(strategy_name: str, operation: str, reason: str)`
- `remove_from_blacklist(strategy_name: str, operation: str)`
- `get_blacklist() -> List[Dict]`
- `get_analytics() -> Dict`
- `cleanup_old_failures(days: int = 30) -> int`

### FailureStore (NEW)

```python
FailureStore(db_path: str = "data/failures.db")
```

**Methods**:

- `save_failure(timestamp, error_type, error_message, operation, context=None) -> int`
- `get_failures(operation=None, error_type=None, since=None, limit=1000) -> List[Dict]`
- `cleanup_old_failures(days=30) -> int`
- `add_to_blacklist(strategy_name, operation, reason)`
- `is_blacklisted(strategy_name, operation) -> bool`
- `remove_from_blacklist(strategy_name, operation)`
- `get_blacklist() -> List[Dict]`
- `get_failure_analytics() -> Dict`

---

## Examples

### Example 1: Simple Resilient API Call

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
    print(f"User: {user['name']}")
```

### Example 2: Multi-Provider Fallback

```python
from alpha.core.resilience import Strategy

async def fetch_from_primary():
    return await primary_api.fetch()

async def fetch_from_secondary():
    return await secondary_api.fetch()

async def fetch_from_cache():
    return cache.get("data")

strategies = [
    Strategy("primary", fetch_from_primary, priority=1.0),
    Strategy("secondary", fetch_from_secondary, priority=0.8),
    Strategy("cache", fetch_from_cache, priority=0.3)
]

result = await engine.execute_with_alternatives(
    strategies,
    operation_name="fetch_critical_data",
    parallel=True  # Try all concurrently
)
```

### Example 3: Failure Analytics Dashboard

```python
def print_failure_dashboard(analyzer):
    analytics = analyzer.get_analytics()

    print("=" * 50)
    print("FAILURE ANALYTICS DASHBOARD")
    print("=" * 50)

    print(f"\n📊 Overall Stats:")
    print(f"  Total failures: {analytics['total_failures']}")
    print(f"  Blacklisted strategies: {analytics['blacklisted_strategies']}")

    print(f"\n🚫 Most Common Errors:")
    for i, error in enumerate(analytics['most_common_errors'][:5], 1):
        print(f"  {i}. {error['error_type']}: {error['count']} times")

    print(f"\n⚠️  Problematic Operations:")
    for i, op in enumerate(analytics['problematic_operations'][:5], 1):
        print(f"  {i}. {op['operation']}: {op['failure_count']} failures")

    print(f"\n📈 Last 7 Days Trend:")
    for trend in analytics['daily_trends']:
        bar = "█" * trend['count']
        print(f"  {trend['date']}: {bar} ({trend['count']})")

    print("\n" + "=" * 50)

# Run weekly
print_failure_dashboard(analyzer)
```

---

**For more information**:
- [Technical Architecture](../../docs/internal/resilience_system_design.md)
- [API Documentation](../../docs/internal/code_execution_api.md)
- [GitHub Issues](https://github.com/your-repo/alpha/issues)

---

**Version History**:
- v1.0 (2026-01-31): Added SQLite persistence, strategy blacklisting, analytics
- v0.9 (2026-01-30): Initial release with retry, alternatives, creative solving
