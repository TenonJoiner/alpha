# Vector Memory CLI Integration Plan

## Date: 2026-01-30

## Executive Summary

Integration plan for Vector Memory System with Alpha CLI interface to enable intelligent context retrieval, personalized responses, and long-term memory capabilities.

## Current Status

**Vector Memory Implementation**: ✅ Complete (1733 lines, 4 modules, 32 tests)

**Components Implemented**:
- ✅ VectorStore (ChromaDB integration)
- ✅ EmbeddingService (OpenAI/Anthropic/Local)
- ✅ KnowledgeBase (knowledge management)
- ✅ ContextRetriever (context-aware responses)

**CLI Integration**: ❌ Not Started

**Dependencies**:
- ChromaDB: ✅ Installed
- sentence-transformers: ⏳ Installing

---

## Integration Architecture

### 1. CLI Enhancement Points

```
alpha/interface/cli.py (Current Flow):
┌─────────────────────────────────────┐
│  User Input                         │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Conversation History (in-memory)   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  LLM Service (generate response)    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Tool/Skill Execution               │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Memory Manager (SQLite storage)    │
└─────────────────────────────────────┘
```

**Enhanced Flow with Vector Memory**:
```
┌─────────────────────────────────────┐
│  User Input                         │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Context Retriever                  │
│  - Retrieve relevant conversations  │
│  - Get related knowledge            │
│  - Build enriched context           │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Conversation History + Context     │
│  (in-memory + semantic retrieval)   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  LLM Service (context-aware)        │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Tool/Skill Execution               │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Dual Storage:                      │
│  - Memory Manager (SQLite)          │
│  - Vector Store (ChromaDB)          │
└─────────────────────────────────────┘
```

### 2. CLI Modification Points

**File**: `alpha/interface/cli.py`

**Changes Required**:

1. **Import Vector Memory Components**:
```python
from alpha.vector_memory import (
    VectorStore,
    EmbeddingService,
    KnowledgeBase,
    ContextRetriever
)
```

2. **Initialize in CLI.__init__()**:
```python
def __init__(self, engine, llm_service, tool_registry, skill_executor=None):
    # ... existing code ...

    # Initialize Vector Memory (optional - disable if embeddings unavailable)
    self.vector_memory_enabled = self._initialize_vector_memory()
```

3. **Add Vector Memory Initialization Method**:
```python
def _initialize_vector_memory(self) -> bool:
    """Initialize vector memory system."""
    try:
        # Load config
        config = self._load_vector_memory_config()

        # Initialize embedding service
        self.embedding_service = EmbeddingService(
            provider=config.get('provider', 'local'),
            model=config.get('model')
        )

        # Initialize vector store
        vector_store_dir = config.get('persist_directory', 'data/vector_memory')
        self.vector_store = VectorStore(
            persist_directory=vector_store_dir,
            embedding_function=self.embedding_service.get_embedding_function()
        )

        # Initialize knowledge base
        self.knowledge_base = KnowledgeBase(
            vector_store=self.vector_store,
            embedding_service=self.embedding_service
        )

        # Initialize context retriever
        self.context_retriever = ContextRetriever(
            vector_store=self.vector_store,
            embedding_service=self.embedding_service,
            max_context_tokens=config.get('max_context_tokens', 4000)
        )

        logger.info("Vector Memory initialized successfully")
        return True

    except Exception as e:
        logger.warning(f"Vector Memory initialization failed: {e}")
        logger.info("Continuing without semantic search capabilities")
        return False
```

4. **Enhance _process_user_input() Method**:
```python
async def _process_user_input(self, user_input: str):
    # ... existing code ...

    # Add to conversation history (existing)
    user_msg = Message(role="user", content=user_input)
    self.conversation_history.append(user_msg)

    # NEW: Add to vector memory for semantic search
    if self.vector_memory_enabled:
        await self._add_to_vector_memory(user_input, role="user")

    # NEW: Retrieve relevant context
    if self.vector_memory_enabled:
        relevant_context = await self._retrieve_relevant_context(user_input)
        if relevant_context:
            # Inject context into conversation
            self._inject_context_into_conversation(relevant_context)

    # ... continue with existing LLM generation ...
```

5. **Add Helper Methods**:
```python
async def _add_to_vector_memory(self, content: str, role: str):
    """Add message to vector memory."""
    try:
        self.context_retriever.add_conversation(
            role=role,
            content=content,
            metadata={'session_id': self.session_id}
        )
    except Exception as e:
        logger.error(f"Failed to add to vector memory: {e}")

async def _retrieve_relevant_context(self, query: str, n_results: int = 3) -> Optional[str]:
    """Retrieve relevant context for query."""
    try:
        context = self.context_retriever.build_context(
            query=query,
            n_conversations=n_results,
            n_knowledge=2
        )
        return context
    except Exception as e:
        logger.error(f"Failed to retrieve context: {e}")
        return None

def _inject_context_into_conversation(self, context: str):
    """Inject retrieved context into conversation history."""
    context_msg = Message(
        role="system",
        content=f"Relevant context from previous conversations:\n{context}"
    )
    # Insert before last user message
    self.conversation_history.insert(-1, context_msg)
```

### 3. Configuration

**File**: `config.yaml`

**New Section**:
```yaml
vector_memory:
  enabled: true
  provider: "local"  # openai, anthropic, local
  model: null  # Model name (provider-specific)
  persist_directory: "data/vector_memory"
  max_context_tokens: 4000

  # Context retrieval settings
  retrieval:
    max_conversations: 5
    max_knowledge_entries: 3
    time_window_days: 30

  # Conversation cleanup
  cleanup:
    enabled: true
    older_than_days: 90
```

---

## Implementation Phases

### Phase 1: Basic Integration (Priority: High)
**Estimated Time**: 2 hours

**Tasks**:
1. ✅ Create integration design document (this file)
2. ⏳ Wait for sentence-transformers installation
3. ⏳ Test Vector Memory modules independently
4. ⏳ Add Vector Memory initialization to CLI
5. ⏳ Implement conversation storage to vector memory
6. ⏳ Test basic storage and retrieval

**Success Criteria**:
- Vector Memory initializes without errors
- Conversations are stored in ChromaDB
- No regression in existing CLI functionality

---

### Phase 2: Context Retrieval (Priority: High)
**Estimated Time**: 2 hours

**Tasks**:
1. Implement context retrieval in _process_user_input()
2. Add context injection into conversation history
3. Test semantic search accuracy
4. Optimize retrieval parameters (n_results, time_window)

**Success Criteria**:
- Relevant past conversations are retrieved
- LLM receives enriched context
- Response quality improves with context

---

### Phase 3: Knowledge Base Integration (Priority: Medium)
**Estimated Time**: 3 hours

**Tasks**:
1. Add CLI commands for knowledge management
   - `kb add <text>` - Add knowledge entry
   - `kb search <query>` - Search knowledge base
   - `kb list` - List all knowledge entries
   - `kb delete <id>` - Delete entry
2. Integrate knowledge retrieval with context building
3. Test knowledge-aware responses

**Success Criteria**:
- Users can manage knowledge base via CLI
- Knowledge entries enhance LLM responses
- All knowledge commands work correctly

---

### Phase 4: User Preferences (Priority: Medium)
**Estimated Time**: 2 hours

**Tasks**:
1. Implement preference storage
2. Add CLI commands:
   - `pref set <key> <value>` - Set preference
   - `pref get <key>` - Get preference
   - `pref list` - List all preferences
3. Use preferences to personalize responses

**Success Criteria**:
- Preferences are stored and retrieved correctly
- LLM adapts to user preferences
- Preferences persist across sessions

---

### Phase 5: Advanced Features (Priority: Low)
**Estimated Time**: 3 hours

**Tasks**:
1. Conversation cleanup (auto-delete old entries)
2. Export/import knowledge base
3. Statistics and analytics
4. Performance optimization

---

## Testing Strategy

### Unit Tests
- Test Vector Memory initialization
- Test conversation storage
- Test context retrieval
- Test knowledge management operations

### Integration Tests
- Test end-to-end conversation flow with context
- Test multi-session persistence
- Test context relevance and quality
- Test error handling and fallbacks

### Performance Tests
- Measure context retrieval latency
- Test with large conversation history (1000+ messages)
- Verify memory usage stays within limits

---

## Fallback Mechanisms

**Graceful Degradation**:
1. If sentence-transformers not available → Disable local embeddings, suggest OpenAI
2. If OpenAI/Anthropic API fails → Fall back to local or disable
3. If ChromaDB initialization fails → Disable vector memory, continue with basic memory
4. If context retrieval fails → Continue without context (log warning)

**User Experience**:
- Never block CLI startup due to Vector Memory failures
- Show clear status messages about Vector Memory availability
- Provide helpful suggestions when features are unavailable

---

## Configuration Validation

**Startup Checks**:
```python
def _validate_vector_memory_config(self, config: Dict) -> bool:
    """Validate vector memory configuration."""
    # Check provider
    valid_providers = ['openai', 'anthropic', 'local']
    if config.get('provider') not in valid_providers:
        logger.warning(f"Invalid provider: {config.get('provider')}")
        return False

    # Check API keys if needed
    if config.get('provider') == 'openai':
        if not os.getenv('OPENAI_API_KEY'):
            logger.warning("OpenAI provider requires OPENAI_API_KEY")
            return False

    # Check persist directory
    persist_dir = Path(config.get('persist_directory', 'data/vector_memory'))
    try:
        persist_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Cannot create vector memory directory: {e}")
        return False

    return True
```

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| sentence-transformers installation fails | High | Low | Use OpenAI embeddings as fallback |
| ChromaDB compatibility issues | Medium | Low | Test with different Python versions |
| Performance degradation with large history | Medium | Medium | Implement pagination, cleanup old entries |
| Embedding API costs | Low | Medium | Default to local embeddings, monitor usage |

---

## Success Metrics

**Phase 1 Success**:
- [ ] Vector Memory initializes in <2 seconds
- [ ] Conversations stored successfully (100% success rate)
- [ ] No CLI startup failures

**Phase 2 Success**:
- [ ] Context retrieval in <500ms
- [ ] Retrieval precision >80% (relevant results)
- [ ] User reports improved response quality

**Overall Success**:
- [ ] All 32 Vector Memory tests passing
- [ ] End-to-end integration tests passing
- [ ] No performance regression in CLI
- [ ] Documentation updated

---

## Next Steps

1. ⏳ Wait for sentence-transformers installation completion
2. ✅ Run all 32 Vector Memory tests
3. ✅ Implement Phase 1: Basic Integration
4. ✅ Test Phase 1 integration
5. ✅ Proceed to Phase 2: Context Retrieval

---

**Document Version**: 1.0
**Author**: Alpha Development Team
**Status**: Planning → Implementation
