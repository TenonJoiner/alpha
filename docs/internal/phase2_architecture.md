# Alpha AI Assistant - Phase 2 Architecture Design
# Phase 2: Autonomous Operation Core - Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Draft

## 1. Architecture Overview

Phase 2 extends Alpha's foundation with autonomous operation capabilities, enhancing it from a reactive assistant to a proactive, self-managing agent.

### 1.1 Design Principles

- **Modularity**: Each component is independent and replaceable
- **Extensibility**: Easy to add new schedulers, triggers, and analyzers
- **Reliability**: Fault-tolerant with automatic recovery
- **Performance**: Efficient resource usage for 24/7 operation
- **Observability**: Comprehensive logging and metrics

### 1.2 New Components

```
alpha/
├── scheduler/          # Task scheduling system (NEW)
│   ├── scheduler.py    # Main scheduler
│   ├── cron.py         # Cron expression parser
│   ├── triggers.py     # Event-based triggers
│   └── storage.py      # Schedule persistence
├── vector_memory/      # Vector-based memory (NEW)
│   ├── store.py        # Vector store interface
│   ├── chroma.py       # ChromaDB integration
│   └── embeddings.py   # Embedding generation
├── monitoring/         # Self-monitoring system (NEW)
│   ├── metrics.py      # Metrics collection
│   ├── analyzer.py     # Self-analysis
│   └── reporter.py     # Report generation
└── daemon/             # Daemon mode support (NEW)
    ├── service.py      # Service management
    ├── health.py       # Health monitoring
    └── config.py       # Configuration management
```

## 2. Component Details

### 2.1 Task Scheduler (`scheduler/`)

#### 2.1.1 Scheduler Architecture

```
┌─────────────────────────────────────────┐
│         TaskScheduler                   │
├─────────────────────────────────────────┤
│ - schedule_task(task, schedule)         │
│ - cancel_schedule(schedule_id)          │
│ - list_schedules()                      │
│ - check_due_tasks()                     │
└─────────────────────────────────────────┘
            │
            ├──> CronSchedule (time-based)
            ├──> IntervalSchedule (recurring)
            ├──> EventTrigger (event-based)
            └──> ConditionTrigger (condition-based)
                         │
                         ├──> ScheduleStorage
                         └──> TaskExecutor
```

#### 2.1.2 Key Classes

**TaskScheduler**
```python
class TaskScheduler:
    def __init__(self, task_manager, storage):
        self.task_manager = task_manager
        self.storage = storage
        self.schedules: Dict[str, Schedule] = {}

    async def schedule_task(
        self,
        task_spec: TaskSpec,
        schedule: ScheduleConfig
    ) -> str:
        """Schedule a task with given configuration."""

    async def check_due_tasks(self) -> List[Task]:
        """Check and execute due tasks."""

    async def cancel_schedule(self, schedule_id: str):
        """Cancel a scheduled task."""
```

**Schedule Types**
```python
class ScheduleType(Enum):
    CRON = "cron"           # Cron expression
    INTERVAL = "interval"   # Fixed interval
    ONE_TIME = "one_time"   # Single execution
    EVENT = "event"         # Event-triggered
    CONDITION = "condition" # Condition-based

@dataclass
class Schedule:
    id: str
    task_spec: TaskSpec
    schedule_type: ScheduleType
    config: Dict[str, Any]
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    created_at: datetime
    metadata: Dict[str, Any]
```

#### 2.1.3 Cron Support

```python
class CronSchedule:
    """Parse and evaluate cron expressions."""

    def __init__(self, expression: str):
        self.expression = expression
        self.parts = self._parse(expression)

    def next_run_time(self, after: datetime) -> datetime:
        """Calculate next run time after given datetime."""

    def matches(self, dt: datetime) -> bool:
        """Check if datetime matches cron expression."""
```

**Supported Format**: `minute hour day month weekday`
- Examples:
  - `0 9 * * *` - Daily at 9:00 AM
  - `*/15 * * * *` - Every 15 minutes
  - `0 0 * * 0` - Weekly on Sunday at midnight

#### 2.1.4 Storage Schema

**Database Tables**:

```sql
-- Schedules table
CREATE TABLE schedules (
    id TEXT PRIMARY KEY,
    task_name TEXT NOT NULL,
    task_description TEXT,
    task_params TEXT,  -- JSON
    schedule_type TEXT NOT NULL,
    schedule_config TEXT,  -- JSON
    enabled INTEGER DEFAULT 1,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    run_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    metadata TEXT  -- JSON
);

-- Schedule execution history
CREATE TABLE schedule_runs (
    id TEXT PRIMARY KEY,
    schedule_id TEXT,
    task_id TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,
    result TEXT,
    error TEXT,
    FOREIGN KEY(schedule_id) REFERENCES schedules(id)
);
```

### 2.2 Event & Trigger System (`scheduler/triggers.py`)

#### 2.2.1 Trigger Architecture

```
┌─────────────────────────────────────────┐
│         TriggerManager                  │
├─────────────────────────────────────────┤
│ - register_trigger(trigger)             │
│ - check_triggers()                      │
│ - fire_trigger(trigger_id, event)       │
└─────────────────────────────────────────┘
            │
            ├──> TimeTrigger
            ├──> FileTrigger
            ├──> SystemTrigger
            ├──> ConditionTrigger
            └──> CustomTrigger
```

#### 2.2.2 Trigger Types

**Base Trigger**
```python
class Trigger(ABC):
    def __init__(self, trigger_id: str, config: Dict):
        self.trigger_id = trigger_id
        self.config = config
        self.enabled = True

    @abstractmethod
    async def check(self) -> bool:
        """Check if trigger condition is met."""

    @abstractmethod
    async def execute(self, task_manager):
        """Execute associated tasks when triggered."""
```

**File System Trigger**
```python
class FileTrigger(Trigger):
    """Trigger based on file system events."""

    def __init__(self, path: str, event_type: str):
        self.path = path
        self.event_type = event_type  # created, modified, deleted

    async def check(self) -> bool:
        # Monitor file system using watchdog
        pass
```

**Condition Trigger**
```python
class ConditionTrigger(Trigger):
    """Trigger based on custom conditions."""

    def __init__(self, condition: str, check_interval: int):
        self.condition = condition  # Python expression
        self.check_interval = check_interval

    async def check(self) -> bool:
        # Evaluate condition in safe context
        pass
```

### 2.3 Vector Memory System (`vector_memory/`)

#### 2.3.1 Vector Store Architecture

```
┌─────────────────────────────────────────┐
│         VectorMemory                    │
├─────────────────────────────────────────┤
│ - add(text, metadata)                   │
│ - search(query, limit, filter)          │
│ - delete(ids)                           │
│ - get_stats()                           │
└─────────────────────────────────────────┘
            │
            ├──> EmbeddingService
            │    └──> OpenAI / Anthropic / Local
            └──> VectorStore
                 └──> ChromaDB / FAISS / Pinecone
```

#### 2.3.2 Key Classes

**VectorMemory**
```python
class VectorMemory:
    def __init__(self, store: VectorStore, embedding_service: EmbeddingService):
        self.store = store
        self.embedding_service = embedding_service

    async def add(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Add text to vector memory."""
        embedding = await self.embedding_service.embed(text)
        return await self.store.add(embedding, text, metadata)

    async def search(
        self,
        query: str,
        limit: int = 10,
        filter: Optional[Dict] = None
    ) -> List[SearchResult]:
        """Semantic search in vector memory."""
        query_embedding = await self.embedding_service.embed(query)
        return await self.store.search(query_embedding, limit, filter)
```

**ChromaDB Integration**
```python
class ChromaVectorStore(VectorStore):
    def __init__(self, collection_name: str, persist_directory: str):
        import chromadb
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    async def add(
        self,
        embedding: List[float],
        text: str,
        metadata: Dict
    ) -> str:
        doc_id = str(uuid.uuid4())
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return doc_id

    async def search(
        self,
        query_embedding: List[float],
        limit: int,
        filter: Optional[Dict] = None
    ) -> List[SearchResult]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=filter
        )
        return self._parse_results(results)
```

#### 2.3.3 Memory Types

**Conversation Memory**
```python
@dataclass
class ConversationEntry:
    message_id: str
    timestamp: datetime
    role: str  # user, assistant, system
    content: str
    metadata: Dict[str, Any]
```

**Knowledge Memory**
```python
@dataclass
class KnowledgeEntry:
    knowledge_id: str
    title: str
    content: str
    category: str
    tags: List[str]
    source: str
    created_at: datetime
    accessed_count: int
```

**Task Memory**
```python
@dataclass
class TaskMemoryEntry:
    task_id: str
    task_name: str
    description: str
    execution_summary: str
    tools_used: List[str]
    outcome: str
    timestamp: datetime
```

### 2.4 Monitoring System (`monitoring/`)

#### 2.4.1 Metrics Architecture

```
┌─────────────────────────────────────────┐
│         MetricsCollector                │
├─────────────────────────────────────────┤
│ - record_metric(name, value, tags)      │
│ - increment_counter(name, tags)         │
│ - record_duration(name, duration)       │
│ - get_metrics(filter)                   │
└─────────────────────────────────────────┘
            │
            ├──> TaskMetrics
            ├──> LLMMetrics
            ├──> ToolMetrics
            └──> SystemMetrics
```

#### 2.4.2 Key Metrics

**Task Metrics**
- Total tasks executed
- Success/failure rates
- Average execution time
- Tasks by priority
- Tasks by type

**LLM Metrics**
- Total API calls
- Token usage (input/output)
- API costs
- Response times
- Error rates

**Tool Metrics**
- Tool usage frequency
- Success rates by tool
- Execution times
- Resource consumption

**System Metrics**
- CPU usage
- Memory usage
- Disk I/O
- Network usage
- Uptime

#### 2.4.3 Self-Analysis

```python
class SelfAnalyzer:
    def __init__(self, metrics_collector, log_parser):
        self.metrics = metrics_collector
        self.log_parser = log_parser

    async def analyze_performance(
        self,
        time_range: Tuple[datetime, datetime]
    ) -> AnalysisReport:
        """Analyze performance over time range."""

    async def detect_anomalies(self) -> List[Anomaly]:
        """Detect performance anomalies."""

    async def suggest_improvements(self) -> List[Suggestion]:
        """Suggest performance improvements."""
```

**Analysis Types**:
1. **Performance Analysis**: Identify slow operations
2. **Error Analysis**: Pattern detection in failures
3. **Resource Analysis**: Optimize resource usage
4. **Cost Analysis**: Track and optimize API costs

#### 2.4.4 Reporting

```python
class ReportGenerator:
    async def generate_daily_report(self, date: datetime) -> Report:
        """Generate daily activity report."""

    async def generate_performance_report(
        self,
        time_range: Tuple[datetime, datetime]
    ) -> Report:
        """Generate performance analysis report."""
```

### 2.5 Daemon Mode (`daemon/`)

#### 2.5.1 Service Management

```python
class DaemonService:
    def __init__(self, engine: AlphaEngine):
        self.engine = engine
        self.running = False

    async def start(self):
        """Start daemon service."""
        self._setup_signal_handlers()
        self.running = True
        await self.engine.start()
        await self._main_loop()

    async def stop(self):
        """Graceful shutdown."""
        self.running = False
        await self.engine.stop()

    def _setup_signal_handlers(self):
        """Setup SIGTERM, SIGHUP handlers."""
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGHUP, self._handle_sighup)
```

#### 2.5.2 Health Monitoring

```python
class HealthMonitor:
    async def check_health(self) -> HealthStatus:
        """Comprehensive health check."""

    async def check_component_health(
        self,
        component: str
    ) -> ComponentHealth:
        """Check specific component health."""

    async def recover_from_failure(self, component: str):
        """Attempt automatic recovery."""
```

**Health Checks**:
- LLM API connectivity
- Database accessibility
- Disk space availability
- Memory usage
- Task queue health
- Background jobs status

## 3. Data Flow

### 3.1 Scheduled Task Execution

```
1. TaskScheduler checks due tasks (every minute)
2. For each due schedule:
   a. Create Task from TaskSpec
   b. TaskManager executes task
   c. Update schedule last_run, next_run
   d. Record execution in history
3. Metrics recorded throughout
4. Results stored in vector memory
```

### 3.2 Event-Triggered Execution

```
1. TriggerManager monitors triggers (continuous)
2. When trigger fires:
   a. Evaluate trigger conditions
   b. Create task(s) based on trigger config
   c. Execute via TaskManager
   d. Log trigger event
3. Update trigger state
```

### 3.3 Context Retrieval

```
1. User query received
2. VectorMemory.search(query) to find relevant context
3. Retrieved context added to LLM prompt
4. LLM generates response with context
5. Interaction stored in vector memory
```

## 4. Integration with Existing Components

### 4.1 Core Engine Integration

```python
class AlphaEngine:
    def __init__(self, config):
        # Existing components
        self.event_bus = EventBus()
        self.task_manager = TaskManager(self.event_bus)
        self.memory_manager = MemoryManager()

        # NEW Phase 2 components
        self.scheduler = TaskScheduler(self.task_manager, schedule_storage)
        self.vector_memory = VectorMemory(chroma_store, embedding_service)
        self.trigger_manager = TriggerManager(self.task_manager)
        self.metrics_collector = MetricsCollector()
        self.health_monitor = HealthMonitor(self)

    async def run(self):
        # Main loop now includes:
        # - Scheduled task checking
        # - Trigger evaluation
        # - Metrics collection
        # - Health monitoring
        pass
```

### 4.2 Memory Manager Enhancement

```python
class MemoryManager:
    def __init__(self):
        # Existing
        self.conversation_db = ConversationDB()
        self.task_db = TaskDB()

        # NEW
        self.vector_memory = VectorMemory(...)

    async def store_conversation(self, message):
        # Store in SQLite
        await self.conversation_db.add(message)

        # Also store in vector memory for semantic search
        await self.vector_memory.add(
            text=message.content,
            metadata={
                "type": "conversation",
                "role": message.role,
                "timestamp": message.timestamp
            }
        )
```

## 5. Configuration

### 5.1 Configuration Schema

```yaml
# alpha/config.yaml

scheduler:
  enabled: true
  check_interval: 60  # seconds
  max_concurrent_scheduled: 5
  persistence: true

vector_memory:
  enabled: true
  provider: chromadb  # chromadb, faiss, pinecone
  persist_directory: ./data/vector_store
  collection_name: alpha_memory
  embedding_provider: openai  # openai, anthropic, local

triggers:
  enabled: true
  check_interval: 10  # seconds
  max_triggers: 100

monitoring:
  enabled: true
  metrics_retention_days: 30
  daily_reports: true
  performance_analysis_interval: 3600  # seconds

daemon:
  enabled: false
  pid_file: ./data/alpha.pid
  log_file: ./logs/alpha.log
  health_check_interval: 300  # seconds
```

## 6. API Design

### 6.1 Scheduler API

```python
# Schedule a task
schedule_id = await scheduler.schedule_task(
    task_spec=TaskSpec(
        name="daily_summary",
        description="Generate daily summary",
        executor="summarize_day"
    ),
    schedule=ScheduleConfig(
        type=ScheduleType.CRON,
        cron="0 20 * * *"  # 8 PM daily
    )
)

# List schedules
schedules = await scheduler.list_schedules(enabled=True)

# Cancel schedule
await scheduler.cancel_schedule(schedule_id)
```

### 6.2 Vector Memory API

```python
# Add to memory
await vector_memory.add(
    text="User prefers concise responses",
    metadata={"type": "preference", "user_id": "user123"}
)

# Search memory
results = await vector_memory.search(
    query="How does user like responses?",
    limit=5,
    filter={"type": "preference"}
)
```

### 6.3 Trigger API

```python
# Register trigger
trigger_id = await trigger_manager.register_trigger(
    FileTrigger(
        path="/data/inbox",
        event_type="created",
        task_spec=TaskSpec(
            name="process_new_file",
            executor="file_processor"
        )
    )
)

# Enable/disable trigger
await trigger_manager.set_enabled(trigger_id, False)
```

## 7. Performance Considerations

### 7.1 Optimization Strategies

1. **Lazy Loading**: Load vector embeddings only when needed
2. **Caching**: Cache frequently accessed vector search results
3. **Batch Processing**: Batch multiple embeddings for efficiency
4. **Connection Pooling**: Reuse database connections
5. **Async I/O**: Non-blocking operations throughout

### 7.2 Resource Limits

```python
# Configuration
MAX_CONCURRENT_TASKS = 10
MAX_VECTOR_MEMORY_SIZE = 100_000  # documents
MAX_SCHEDULE_CHECKS_PER_MINUTE = 60
METRICS_BUFFER_SIZE = 1000
```

## 8. Testing Strategy

### 8.1 Unit Tests

- Test each component in isolation
- Mock external dependencies (ChromaDB, LLM APIs)
- Test edge cases and error conditions

### 8.2 Integration Tests

- Test component interactions
- Test with real ChromaDB instance
- Test scheduler with various cron expressions
- Test trigger firing and task execution

### 8.3 Performance Tests

- Benchmark vector search performance
- Test scheduler accuracy
- Measure resource usage under load
- Test long-running daemon stability

## 9. Migration Path

### 9.1 From Phase 1 to Phase 2

1. **Database Migration**: Add new tables for schedules
2. **Configuration Update**: Add Phase 2 config sections
3. **Dependencies Installation**: Install ChromaDB, APScheduler
4. **Data Migration**: Optionally migrate existing conversations to vector memory
5. **Gradual Rollout**: Enable features incrementally

### 9.2 Backward Compatibility

- Existing TaskManager API remains unchanged
- Phase 2 features are additive, not breaking
- Old tasks continue to work without modification

## 10. Security Considerations

### 10.1 Scheduled Task Security

- Validate task specifications before scheduling
- Limit privileges for scheduled tasks
- Audit log for all scheduled operations

### 10.2 Vector Memory Security

- Sanitize inputs before embedding
- Implement access controls for sensitive memories
- Option to exclude sensitive data from vector storage

### 10.3 Trigger Security

- Validate trigger conditions in sandboxed environment
- Rate limit trigger firing
- Prevent recursive trigger loops

## Summary

Phase 2 architecture builds upon Phase 1 foundation by adding:

1. **TaskScheduler**: Cron-based and event-based task scheduling
2. **VectorMemory**: Semantic search with ChromaDB
3. **TriggerManager**: Event-driven task execution
4. **MetricsCollector & Analyzer**: Self-monitoring and improvement
5. **DaemonService**: 24/7 operation support

These components work together to transform Alpha into a truly autonomous assistant capable of proactive operation and continuous self-improvement.

---

**Next Steps**: Review architecture, implement components in order: Scheduler → Vector Memory → Triggers → Monitoring → Daemon
