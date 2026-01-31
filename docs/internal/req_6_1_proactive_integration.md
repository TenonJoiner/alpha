# REQ-6.1: Proactive Intelligence Integration
## Requirement ID: REQ-6.1
## Priority: HIGH
## Status: 📋 Planned
## Phase: 6.1 - Proactive Intelligence Integration
## Created: 2026-01-31

---

## Background

**Critical Gap Identified**: The Proactive Intelligence System (Phase 5.2) has been fully implemented and tested (32/32 tests passing), but is **NOT integrated** into the core AlphaEngine or CLI interface. This prevents Alpha from fulfilling its core positioning as a "proactive, autonomous super assistant."

### Already Implemented (Phase 5.2):
- ✅ PatternLearner - Learn from user behavior
- ✅ TaskDetector - Detect proactive task opportunities
- ✅ Predictor - Predict user needs and timing
- ✅ Notifier - Intelligent notification system
- ✅ 32 comprehensive tests (100% pass rate)

### Not Done:
- ❌ Integration into AlphaEngine lifecycle
- ❌ CLI event hooks for pattern learning
- ❌ Background proactive task detection loop
- ❌ User-facing proactive suggestions
- ❌ Safe task auto-execution

---

## Objective

Integrate the existing Proactive Intelligence System into Alpha's core runtime, enabling:
1. Continuous pattern learning from user interactions
2. Background detection of proactive task opportunities
3. Intelligent, timely notifications to users
4. Optional auto-execution of safe, high-confidence tasks

---

## Detailed Requirements

### REQ-6.1.1: AlphaEngine Integration
**Description**: Add proactive components to AlphaEngine initialization and lifecycle

**Acceptance Criteria**:
- PatternLearner, TaskDetector, and Notifier initialized in `AlphaEngine.__init__()`
- Components started during `startup()` phase
- Graceful shutdown in `shutdown()` method
- Proper error handling and logging

**Implementation**:
```python
# alpha/core/engine.py modifications
from alpha.proactive import PatternLearner, TaskDetector, Notifier, Predictor

class AlphaEngine:
    def __init__(self, config: Config):
        # ... existing code ...

        # Proactive Intelligence
        proactive_db = config.memory.database.replace('.db', '_proactive.db')
        self.pattern_learner = PatternLearner(
            database_path=proactive_db,
            min_pattern_frequency=3,
            min_confidence=0.6
        )
        self.task_detector = TaskDetector(
            pattern_learner=self.pattern_learner,
            database_path=proactive_db
        )
        self.notifier = Notifier()

    async def startup(self):
        # ... existing initialization ...

        # Initialize proactive components
        self.pattern_learner.initialize()
        logger.info("Pattern learner initialized")

        # Start background proactive loop
        self.proactive_task = asyncio.create_task(self._proactive_loop())
        logger.info("Proactive intelligence started")
```

### REQ-6.1.2: CLI Event Hooks
**Description**: Capture user interactions in CLI for pattern learning

**Acceptance Criteria**:
- Record user queries and responses
- Track successful task completions
- Log user preferences when detected
- Minimal performance impact (< 10ms overhead)

**Implementation**:
```python
# alpha/interface/cli.py modifications

async def _handle_query(self, query: str):
    # Record query for pattern learning
    await self.engine.pattern_learner.record_user_request(
        request_type="query",
        description=query,
        timestamp=datetime.now()
    )

    # ... existing query handling ...

    # If successful, record completion
    if task_successful:
        await self.engine.pattern_learner.record_task_completion(
            task_id=task_id,
            success=True
        )
```

### REQ-6.1.3: Background Proactive Loop
**Description**: Continuously detect and suggest proactive tasks

**Acceptance Criteria**:
- Runs in background without blocking main loop
- Checks for task opportunities every 60 seconds (configurable)
- Generates suggestions with confidence scores
- Respects user notification preferences

**Implementation**:
```python
async def _proactive_loop(self):
    """Background loop for proactive task detection."""
    while self.running:
        try:
            # Detect task opportunities
            suggestions = await self.task_detector.detect_tasks(
                current_context=self._get_current_context(),
                max_suggestions=5
            )

            # Filter high-confidence suggestions
            for suggestion in suggestions:
                if suggestion.confidence >= 0.8:
                    await self.notifier.notify(
                        title="Proactive Task Suggestion",
                        message=f"{suggestion.justification}",
                        priority="normal",
                        actions=["execute", "dismiss", "snooze"]
                    )

        except Exception as e:
            logger.error(f"Proactive loop error: {e}", exc_info=True)

        await asyncio.sleep(60)  # Check every minute
```

### REQ-6.1.4: Safe Task Auto-Execution
**Description**: Automatically execute high-confidence, safe tasks

**Acceptance Criteria**:
- Only execute tasks marked as "safe" (read-only operations)
- Requires confidence >= 0.9
- User can configure auto-execution threshold
- All auto-executions logged for transparency

**Safe Task Categories**:
- Information retrieval (web search, weather, news)
- Read-only data queries
- Scheduled reminders
- Status checks

**Implementation**:
```python
async def _execute_safe_task(self, suggestion):
    """Auto-execute a safe proactive task."""
    # Safety checks
    if not suggestion.is_safe:
        return False
    if suggestion.confidence < 0.9:
        return False
    if not self.config.proactive.auto_execute:
        return False

    logger.info(f"Auto-executing safe task: {suggestion.task_description}")

    # Execute and log
    result = await self._execute_task(suggestion.task_params)

    await self.memory_manager.add_system_event(
        "proactive_execution",
        {
            "suggestion_id": suggestion.suggestion_id,
            "confidence": suggestion.confidence,
            "result": "success" if result else "failed"
        }
    )
```

### REQ-6.1.5: Configuration
**Description**: Add configuration options for proactive behavior

**Config File** (`config.yaml`):
```yaml
proactive:
  enabled: true
  auto_execute: false  # Require user approval by default
  confidence_threshold: 0.8
  notification_channels:
    - cli
    # Future: email, webhook
  check_interval: 60  # seconds
  pattern_learning:
    enabled: true
    min_frequency: 3
    min_confidence: 0.6
```

### REQ-6.1.6: User Commands
**Description**: Add CLI commands for managing proactive features

**New Commands**:
- `proactive status` - Show proactive intelligence statistics
- `proactive suggestions` - View pending suggestions
- `proactive history` - View past proactive executions
- `proactive enable/disable` - Toggle proactive features
- `preferences` - View and edit learned preferences

---

## Testing Strategy

### Unit Tests
- ✅ Already exist (32 tests for proactive modules)
- New: Integration tests for engine modifications

### Integration Tests (New)
1. Test pattern learning from CLI interactions
2. Test background proactive loop startup/shutdown
3. Test suggestion generation and notification
4. Test safe task auto-execution
5. Test configuration loading

### Manual Testing Scenarios
1. Use Alpha for 1 week, verify patterns learned
2. Test proactive suggestions at appropriate times
3. Verify auto-execution works for safe tasks
4. Test notification delivery

---

## Implementation Plan

### Phase 1: Engine Integration (Day 1)
- [ ] Modify AlphaEngine to initialize proactive components
- [ ] Add background proactive loop
- [ ] Implement graceful startup/shutdown
- [ ] Write integration tests

### Phase 2: CLI Hooks (Day 1-2)
- [ ] Add event hooks for query/response logging
- [ ] Implement user preference detection
- [ ] Add proactive commands to CLI
- [ ] Test pattern learning from real interactions

### Phase 3: Notification & Auto-Execution (Day 2)
- [ ] Implement safe task auto-execution logic
- [ ] Add notification delivery (CLI output)
- [ ] Implement suggestion approval workflow
- [ ] Add configuration options

### Phase 4: Testing & Validation (Day 2-3)
- [ ] Run integration tests
- [ ] Manual testing with real scenarios
- [ ] Performance testing (overhead < 10ms)
- [ ] Documentation updates

---

## Success Criteria

1. **Functional**:
   - Pattern learning works from CLI interactions
   - Proactive suggestions generated in background
   - Safe tasks auto-execute when conditions met
   - All 32 existing tests still pass
   - At least 10 new integration tests passing

2. **Performance**:
   - Pattern learning overhead < 10ms per interaction
   - Background loop uses < 5% CPU
   - No noticeable CLI responsiveness degradation

3. **User Experience**:
   - Proactive suggestions are relevant (user acceptance > 50%)
   - Auto-executed tasks are correct (no false positives)
   - Easy to enable/disable/configure

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance degradation | High | Medium | Optimize pattern detection, use caching |
| False positive suggestions | Medium | Medium | High confidence threshold, user feedback loop |
| Database conflicts | Medium | Low | Separate proactive database |
| Notification spam | High | Medium | Rate limiting, smart batching |

---

## Dependencies

- Existing: Memory Manager, Event Bus, Task Manager
- New: Configuration module enhancement
- External: None

---

## Estimated Effort

- **Development**: 2-3 days
- **Testing**: 1 day
- **Documentation**: 0.5 days
- **Total**: 3-4 days

---

## Documentation Requirements

### Internal Docs
- [ ] Update architecture.md with proactive system
- [ ] Add proactive_integration.md technical guide
- [ ] Update global_requirements_list.md

### User Docs
- [ ] Add proactive_intelligence_guide.md (EN/CN)
- [ ] Update README with proactive features
- [ ] Add FAQ section for proactive behavior

---

## Version & Tracking

- **Target Version**: v0.11.0
- **Milestone**: Phase 6.1 - Proactive Intelligence Integration
- **Created By**: Autonomous Development Agent
- **Date**: 2026-01-31
- **Status**: Ready for Implementation Approval
