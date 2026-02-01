# REQ-6.2.5: Proactive Workflow Integration - Implementation Design

**Phase**: 6.2.5
**Priority**: High
**Status**: In Design → Implementation
**Created**: 2026-02-01
**Dependencies**: REQ-6.1 (Proactive Intelligence), REQ-6.2.1-6.2.4 (Workflow System)

---

## 1. Objective

Integrate Alpha's Proactive Intelligence system with the Workflow Orchestration system to enable:
1. **Automatic Pattern Detection**: Detect recurring task sequences worthy of workflow automation
2. **Proactive Suggestions**: Suggest workflow creation when patterns detected (≥3 occurrences/7 days)
3. **Auto-Generation**: Generate workflow definitions from task execution history
4. **Smart Execution**: Detect when to execute saved workflows proactively
5. **Optimization**: Analyze workflow execution data and recommend improvements

---

## 2. Architecture Design

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│               Proactive Workflow Integration                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  WorkflowPatternDetector                              │  │
│  │  (extends PatternLearner)                             │  │
│  │  - detect_workflow_patterns()                         │  │
│  │  - analyze_task_sequences()                           │  │
│  │  - calculate_pattern_confidence()                     │  │
│  └────────────────┬──────────────────────────────────────┘  │
│                   │                                          │
│  ┌────────────────┴──────────────────────────────────────┐  │
│  │  WorkflowSuggestionGenerator                          │  │
│  │  (extends TaskDetector)                               │  │
│  │  - generate_workflow_suggestions()                    │  │
│  │  - create_workflow_from_pattern()                     │  │
│  │  - detect_workflow_execution_opportunities()          │  │
│  └────────────────┬──────────────────────────────────────┘  │
│                   │                                          │
│  ┌────────────────┴──────────────────────────────────────┐  │
│  │  WorkflowOptimizer (NEW)                              │  │
│  │  - analyze_execution_history()                        │  │
│  │  - identify_bottlenecks()                             │  │
│  │  - recommend_improvements()                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
           │                     │                │
           ▼                     ▼                ▼
    ┌──────────┐         ┌─────────────┐  ┌──────────────┐
    │ Pattern  │         │ Workflow    │  │ Workflow     │
    │ Learner  │         │ Builder     │  │ Library      │
    └──────────┘         └─────────────┘  └──────────────┘
```

### 2.2 Data Models

```python
@dataclass
class WorkflowPattern:
    """Detected workflow pattern from task history."""
    pattern_id: str
    task_sequence: List[str]  # Normalized task descriptions
    frequency: int  # Number of times this sequence occurred
    confidence: float  # 0.0 to 1.0
    first_seen: datetime
    last_seen: datetime
    avg_interval: timedelta  # Average time between occurrences
    task_ids: List[str]  # Original task IDs
    suggested_workflow_name: str
    metadata: Dict[str, Any]

@dataclass
class WorkflowSuggestion:
    """Suggestion to create a workflow."""
    suggestion_id: str
    pattern_id: str
    suggested_name: str
    description: str
    confidence: float
    priority: int  # 1-5, higher = more important
    steps: List[Dict[str, Any]]  # Auto-generated workflow steps
    parameters: Dict[str, Any]  # Detected parameters
    triggers: List[str]  # Conditions for auto-execution
    created_at: datetime
    status: str  # "pending", "approved", "rejected", "auto_created"

@dataclass
class WorkflowOptimization:
    """Optimization recommendation for a workflow."""
    workflow_id: str
    optimization_type: str  # "remove_redundancy", "parallel_execution", "parameter_tuning"
    description: str
    potential_improvement: str  # e.g., "30% faster", "reduce errors"
    suggested_changes: Dict[str, Any]
    confidence: float
    created_at: datetime
```

---

## 3. Implementation Components

### Component 1: WorkflowPatternDetector

**Purpose**: Detect recurring task sequences from execution history

**Implementation**:
```python
class WorkflowPatternDetector:
    """
    Analyzes task execution history to detect workflow-worthy patterns.

    Detection Algorithm:
    1. Fetch recent task executions (last 30 days)
    2. Normalize task descriptions (remove dates, specific values)
    3. Find recurring sequences (using sliding window + LCS)
    4. Filter by frequency threshold (≥3 occurrences)
    5. Filter by temporal proximity (within 7 days)
    6. Calculate confidence score
    7. Generate suggested workflow name
    """

    def detect_workflow_patterns(
        self,
        lookback_days: int = 30,
        min_frequency: int = 3,
        min_sequence_length: int = 2,
        max_interval_days: int = 7
    ) -> List[WorkflowPattern]:
        """
        Detect workflow patterns from task history.

        Returns patterns sorted by (confidence, frequency).
        """
        pass

    def normalize_task_description(self, description: str) -> str:
        """
        Normalize task description for pattern matching.

        Examples:
        - "Deploy to staging on 2026-01-15" → "Deploy to staging"
        - "Backup files at 23:45" → "Backup files"
        - "Pull branch feature/auth" → "Pull branch"
        """
        pass

    def calculate_pattern_confidence(self, pattern: WorkflowPattern) -> float:
        """
        Calculate confidence score based on:
        - Frequency (higher = better)
        - Regularity (consistent intervals = better)
        - Sequence length (longer = more specific = better)
        - Task success rate (higher = better)
        """
        pass
```

**Files**:
- `alpha/workflow/pattern_detector.py` (NEW)
- `tests/workflow/test_pattern_detector.py` (NEW)

---

### Component 2: WorkflowSuggestionGenerator

**Purpose**: Generate workflow suggestions and auto-create workflows from patterns

**Implementation**:
```python
class WorkflowSuggestionGenerator:
    """
    Generates workflow suggestions from detected patterns.

    Features:
    - Create workflow suggestions from patterns
    - Auto-generate workflow definitions
    - Detect execution opportunities for existing workflows
    - Track suggestion approval/rejection
    """

    def generate_workflow_suggestions(
        self,
        patterns: List[WorkflowPattern],
        max_suggestions: int = 5
    ) -> List[WorkflowSuggestion]:
        """
        Generate workflow suggestions from patterns.

        Prioritization:
        - High frequency + high confidence → priority 5
        - Medium frequency + medium confidence → priority 3
        - Low frequency OR low confidence → priority 1
        """
        pass

    def create_workflow_from_pattern(
        self,
        pattern: WorkflowPattern
    ) -> Dict[str, Any]:
        """
        Auto-generate workflow definition from pattern.

        Steps:
        1. Extract task sequence
        2. Identify common parameters
        3. Generate step definitions
        4. Add error handling
        5. Create workflow schema
        """
        pass

    def detect_workflow_execution_opportunities(
        self,
        current_context: Dict[str, Any]
    ) -> List[WorkflowSuggestion]:
        """
        Detect when saved workflows should be executed.

        Checks:
        - Temporal patterns (e.g., daily at 9am)
        - Contextual triggers (e.g., after git push)
        - User behavior patterns
        """
        pass
```

**Files**:
- `alpha/workflow/suggestion_generator.py` (NEW)
- `tests/workflow/test_suggestion_generator.py` (NEW)

---

### Component 3: WorkflowOptimizer

**Purpose**: Analyze workflow execution history and recommend optimizations

**Implementation**:
```python
class WorkflowOptimizer:
    """
    Analyzes workflow execution data to find optimization opportunities.

    Optimization Types:
    1. Remove redundant steps
    2. Enable parallel execution
    3. Tune parameters
    4. Improve error handling
    5. Add caching
    """

    def analyze_workflow(
        self,
        workflow_id: str,
        min_executions: int = 5
    ) -> List[WorkflowOptimization]:
        """
        Analyze workflow execution history.

        Analysis:
        - Execution times per step
        - Error rates per step
        - Parameter value distribution
        - Step dependencies
        """
        pass

    def identify_bottlenecks(
        self,
        execution_history: List[Dict[str, Any]]
    ) -> List[Tuple[int, str, float]]:
        """
        Find slow steps in workflow.

        Returns: [(step_index, step_name, avg_duration_ms), ...]
        """
        pass

    def recommend_improvements(
        self,
        workflow: Dict[str, Any],
        execution_history: List[Dict[str, Any]]
    ) -> List[WorkflowOptimization]:
        """
        Generate optimization recommendations.

        Examples:
        - "Step 2 and 3 can run in parallel (30% faster)"
        - "Remove step 5: redundant with step 3"
        - "Add retry to step 4: fails 20% of the time"
        """
        pass
```

**Files**:
- `alpha/workflow/optimizer.py` (NEW)
- `tests/workflow/test_optimizer.py` (NEW)

---

### Component 4: CLI Integration

**New Commands**:
```bash
# View workflow suggestions
$ alpha workflow suggestions

  📋 Workflow Suggestions (based on your task history)

  [1] HIGH PRIORITY: "Daily Development Workflow"
      ├─ Detected pattern: 5 times in last 7 days
      ├─ Steps: git pull → run tests → check coverage
      └─ Confidence: 92%

      Create this workflow? (y/n/later): y
      ✅ Workflow "Daily Development Workflow" created

  [2] MEDIUM: "Weekly Backup Routine"
      ├─ Detected pattern: 3 times in last 14 days
      ├─ Steps: backup data → sync to cloud → verify integrity
      └─ Confidence: 78%

# Auto-approve high-confidence suggestions
$ alpha workflow suggestions --auto-approve --min-confidence 0.9

# View workflow optimizations
$ alpha workflow optimize <workflow_name>

  🔧 Optimization Recommendations for "Daily Development Workflow"

  [1] Enable Parallel Execution (Potential: 35% faster)
      ├─ Steps 1 and 2 have no dependencies
      └─ Can run simultaneously

  [2] Add Caching (Potential: 50% faster on reruns)
      └─ Test results can be cached for 1 hour

  Apply these optimizations? (y/n/selective): y

# View pattern statistics
$ alpha workflow patterns

  📊 Detected Task Patterns

  Pattern Type         Count  Avg Frequency  Suggested Workflows
  ──────────────────────────────────────────────────────────────
  Daily Routines         3        5x/week            2 created
  Weekly Tasks           2        3x/month           1 pending
  Project Workflows      4        10x/month          3 created
```

**Files**:
- `alpha/workflow/cli.py` (EXTEND)
- `tests/workflow/test_cli_proactive.py` (NEW)

---

## 4. Integration with AlphaEngine

### 4.1 Proactive Loop Extension

Extend the existing proactive loop to include workflow detection:

```python
class AlphaEngine:
    async def _run_proactive_loop(self):
        """
        Background loop for proactive intelligence.

        Extended with workflow detection:
        1. Pattern learning (existing)
        2. Task detection (existing)
        3. Workflow pattern detection (NEW)
        4. Workflow suggestions (NEW)
        5. Workflow optimization analysis (NEW)
        """
        while self.running:
            try:
                # Existing: Learn patterns
                await self.pattern_learner.analyze_recent_interactions()

                # Existing: Detect task opportunities
                suggestions = await self.task_detector.detect_opportunities()

                # NEW: Detect workflow patterns
                workflow_patterns = await self.workflow_pattern_detector.detect_workflow_patterns()

                # NEW: Generate workflow suggestions
                if workflow_patterns:
                    workflow_suggestions = await self.workflow_suggestion_generator.generate_workflow_suggestions(
                        patterns=workflow_patterns
                    )

                    # Auto-create high-confidence workflows
                    for suggestion in workflow_suggestions:
                        if suggestion.confidence >= 0.9 and self.config.proactive.auto_create_workflows:
                            await self._auto_create_workflow(suggestion)
                        else:
                            # Store for user review
                            await self.workflow_suggestion_generator.store_suggestion(suggestion)

                # NEW: Analyze existing workflows for optimization
                workflows = await self.workflow_library.list_workflows()
                for workflow in workflows:
                    optimizations = await self.workflow_optimizer.analyze_workflow(workflow.id)
                    if optimizations:
                        # Notify user of optimization opportunities
                        await self.notifier.notify_workflow_optimization(workflow, optimizations)

                await asyncio.sleep(self.config.proactive.check_interval)
            except Exception as e:
                logger.error(f"Proactive loop error: {e}")
                await asyncio.sleep(60)
```

### 4.2 Configuration Extension

```yaml
# config.yaml
proactive:
  enabled: true
  check_interval: 300  # seconds

  # Workflow integration (NEW)
  workflow_detection:
    enabled: true
    min_pattern_frequency: 3
    min_confidence: 0.7
    lookback_days: 30
    auto_create_workflows: false  # Safety: require user approval

  workflow_optimization:
    enabled: true
    min_executions: 5  # Require 5+ executions before suggesting optimizations
    analysis_interval: 86400  # Daily analysis
```

---

## 5. Implementation Plan

### Phase 1: Pattern Detection (Day 1, 4-5 hours)
- ✅ Design data models
- ✅ Implement WorkflowPatternDetector
- ✅ Add pattern normalization
- ✅ Add confidence scoring
- ✅ Unit tests (15+ tests)

### Phase 2: Suggestion Generation (Day 1-2, 4-5 hours)
- ✅ Implement WorkflowSuggestionGenerator
- ✅ Auto-generate workflow definitions
- ✅ Detect execution opportunities
- ✅ Unit tests (15+ tests)

### Phase 3: Workflow Optimization (Day 2, 3-4 hours)
- ✅ Implement WorkflowOptimizer
- ✅ Bottleneck detection
- ✅ Optimization recommendations
- ✅ Unit tests (10+ tests)

### Phase 4: Integration & CLI (Day 2, 3-4 hours)
- ✅ Extend AlphaEngine proactive loop
- ✅ Add CLI commands
- ✅ Configuration updates
- ✅ Integration tests (10+ tests)

### Phase 5: Testing & Documentation (Day 2-3, 3-4 hours)
- ✅ End-to-end integration tests
- ✅ Performance testing
- ✅ User documentation (EN + CN)
- ✅ Update global requirements list

**Total Estimated Effort**: 2-3 days, ~600 lines core code, 50+ tests

---

## 6. Success Criteria

### Functional
- ✅ Detects workflow patterns with ≥3 occurrences in 7 days
- ✅ Generates workflow suggestions with ≥70% confidence
- ✅ Auto-creates workflow definitions matching 90%+ of pattern tasks
- ✅ Provides actionable optimization recommendations
- ✅ CLI commands functional and user-friendly

### Quality
- ✅ 95%+ test coverage
- ✅ All tests passing
- ✅ No performance degradation (pattern detection <2s)
- ✅ Bilingual documentation complete

### User Experience
- ✅ Suggestions are relevant and accurate
- ✅ Auto-generated workflows work without modification
- ✅ Optimizations provide measurable improvements

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positive patterns | Medium | Require high confidence (≥0.7), user approval |
| Auto-generated workflows incorrect | High | Default auto_create=false, require review |
| Performance overhead | Medium | Optimize pattern detection, run in background |
| Integration complexity | Medium | Leverage existing proactive infrastructure |

---

**Document Version**: 1.0
**Status**: ✅ Design Complete - Ready for Implementation
**Created**: 2026-02-01
**Author**: Alpha Autonomous Development Agent
