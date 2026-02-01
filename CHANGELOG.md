[English](#english) | [简体中文](#中文)

---

# <a name="english"></a>English

# Alpha v1.0.0 - Production Release 🎉

## Release Date
2026-02-02

## 🎯 Major Milestone

**Alpha v1.0.0** marks the completion of all 128 core requirements (100%), transforming Alpha from a prototype into a production-ready **Personal Super AI Assistant**.

## 📊 Completion Summary

| Category | Requirements | Status |
|----------|--------------|--------|
| Phase 1: Foundation | 24 | ✅ 100% |
| Phase 2: Autonomous Operation | 29 | ✅ 100% |
| Phase 3: Resilience System | 12 | ✅ 100% |
| Phase 4: Advanced Capabilities | 8 | ✅ 100% |
| Phase 5: Self-Improvement | 22 | ✅ 100% |
| Phase 6: Integration & UX | 12 | ✅ 100% |
| Phase 7: Enhanced Resilience | 5 | ✅ 100% |
| Phase 8: Task Mastery | 5 | ✅ 100% |
| Phase 9: Multimodal | 6 | ✅ 100% |
| Phase 10: Personalization | 5 | ✅ 100% |
| **Total** | **128** | **✅ 100%** |

## 🚀 Key Features

### Complete Feature Set
- ✅ **Autonomous 24/7 Operation** - Runtime engine, scheduling, daemon mode
- ✅ **Multi-Model Intelligence** - DeepSeek, OpenAI, Anthropic with auto-routing
- ✅ **Never Give Up Resilience** - Circuit breakers, retry policies, self-healing
- ✅ **Advanced Tools** - 50+ skills, browser automation, code execution
- ✅ **Self-Improvement** - Continuous learning and optimization loops
- ✅ **Proactive Intelligence** - Pattern learning, task prediction, workflow automation
- ✅ **Task Mastery** - Intelligent decomposition, progress tracking
- ✅ **Multimodal** - Image understanding with Claude Vision
- ✅ **Personalization** - Adaptive communication, preference learning
- ✅ **Vector Memory** - Semantic search, conversation history

### Technical Achievements
- **Production Code**: 50,000+ lines
- **Test Coverage**: 1,091/1,093 tests passing (99.8%)
- **Documentation**: 100+ pages (EN + CN)
- **Components**: 120+ modules

## 📚 Documentation

Complete documentation available:
- `README.md` - Installation and quickstart
- `docs/` - User guides and API documentation
- `docs/internal/global_requirements_list.md` - Complete requirements tracking

## 🔮 Future Roadmap

Post-v1.0.0 possibilities:
- Knowledge Graph System
- Voice Processing
- Multi-User Support
- Web Dashboard UI

---

[English](#english) | [简体中文](#中文)

---

# <a name="english"></a>English

# Alpha Auto-Skill System - v0.5.0

## Update Date
2026-01-29

## Major Changes

### 1. Automatic Skill Discovery and Execution

**New Feature:**
Alpha now automatically finds, downloads, installs, and executes relevant agent skills based on user queries.

**Core Capabilities:**

**智能技能匹配 (Intelligent Matching)**:
- Analyzes user requests to identify keywords and intent
- Searches skills.sh marketplace with 50+ available skills
- Ranks skills by relevance score and popularity
- Automatically selects the best matching skill

**自动下载安装 (Auto-Installation)**:
- Checks if skill is already installed
- Uses `npx skills` to install missing skills automatically
- Handles installation errors and timeouts gracefully
- Tracks installed skills and usage statistics

**动态加载执行 (Dynamic Loading)**:
- Reads SKILL.md files and parses YAML frontmatter
- Loads skill instructions as LLM context
- LLM responds following skill-specific guidelines
- Supports all skills from skills.sh marketplace

**System Architecture:**

```
User Query
    ↓
SkillMatcher (finds relevant skills)
    ↓
SkillDownloader (auto-installs if needed)
    ↓
SkillLoader (loads SKILL.md content)
    ↓
AutoSkillManager (coordinates workflow)
    ↓
LLM (responds with skill context)
```

**Components:**

1. **SkillMatcher** (`alpha/skills/matcher.py`)
   - Keyword extraction
   - Relevance scoring (0-10 scale)
   - Popularity-based ranking

2. **SkillDownloader** (`alpha/skills/downloader.py`)
   - Installation check
   - Automatic `npx skills` execution
   - Error handling

3. **SkillLoader** (`alpha/skills/loader.py`)
   - SKILL.md parsing
   - YAML frontmatter extraction
   - Context formatting

4. **AutoSkillManager** (`alpha/skills/auto_manager.py`)
   - End-to-end orchestration
   - Usage statistics
   - Skill suggestions

**Configuration:**
```yaml
skills:
  auto_skill:
    enabled: true           # Enable auto-skill
    auto_install: true      # Auto-install missing skills
    auto_load: true         # Auto-load skill context
    min_score: 3.0          # Minimum relevance score
    max_matches: 3          # Max skills to consider
```

**Usage Examples:**

Example 1: React Development
```
User: "Help me build a performant React component"
System:
  1. Matches: vercel-react-best-practices (score: 7.0, 67K installs)
  2. Already installed ✓
  3. Loads React optimization guidelines
  4. LLM responds with React best practices
```

Example 2: PDF Generation
```
User: "Create a PDF invoice"
System:
  1. Matches: pdf (score: 15.5, 5.2K installs)
  2. Already installed ✓
  3. Loads PDF creation instructions
  4. LLM provides PDF generation steps
```

Example 3: SEO Audit
```
User: "Audit my website for SEO"
System:
  1. Matches: seo-audit (score: 5.5, 7.4K installs)
  2. Already installed ✓
  3. Loads SEO audit checklist
  4. LLM performs comprehensive SEO analysis
```

**Relevance Scoring:**
- Exact name match: +10 points
- Keyword match: +5 points per keyword
- Popularity bonus:
  - >50K installs: +2 points
  - >20K installs: +1 point
  - >5K installs: +0.5 points

**Testing:**
```bash
python tests/test_auto_skill.py
```

Results:
- ✅ Skill matching: 100% pass
- ✅ Auto-installation: 100% pass
- ✅ Skill loading: 100% pass
- ✅ End-to-end workflow: 100% pass

**Benefits:**

1. **Zero Configuration**
   - No manual skill installation required
   - Automatic skill discovery
   - Intelligent best-match selection

2. **Dynamic Extension**
   - Add new skills anytime
   - No system restart needed
   - Instant availability

3. **Context-Aware**
   - Loads domain-specific instructions
   - LLM gains specialized knowledge
   - More professional responses

4. **Performance Optimized**
   - Skills cached after first use
   - Only installs when needed
   - Lightweight integration

**Documentation:**
- Full guide: `docs/AUTO_SKILL_SYSTEM.md`
- Test suite: `tests/test_auto_skill.py`
- Configuration: `config.yaml`

---

# Alpha Agent Skills Integration - v0.4.0

## Update Date
2026-01-29

## Major Changes

### 1. Integrated Skills.sh Marketplace

**New Feature:**
Alpha now supports external agent skills from the skills.sh marketplace.

**Skills Installed (20 total):**

**Frontend Development (8 skills):**
- ✅ **vercel-react-best-practices** (67K installs) - React/Next.js performance optimization
- ✅ **web-design-guidelines** (52K installs) - Web interface design compliance
- ✅ **vercel-composition-patterns** (7.6K installs) - React component patterns
- ✅ **vercel-react-native-skills** (6K installs) - React Native best practices
- ✅ **frontend-design** (26K installs) - Frontend design guidelines
- ✅ **ui-ux-pro-max** (6.7K installs) - Advanced UI/UX design
- ✅ **remotion-best-practices** (48K installs) - Programmatic video with React
- ✅ **agent-browser** (14K installs) - Browser automation for agents

**Document Processing (4 skills):**
- ✅ **pdf** (5.2K installs) - PDF document creation and manipulation
- ✅ **docx** - Word document processing
- ✅ **pptx** - PowerPoint presentation creation
- ✅ **xlsx** - Excel spreadsheet processing

**Marketing & Content (2 skills):**
- ✅ **seo-audit** (7.4K installs) - SEO analysis and optimization
- ✅ **copywriting** (5.6K installs) - Marketing copy creation

**Database & Auth (2 skills):**
- ✅ **supabase-postgres-best-practices** (7K installs) - Database optimization
- ✅ **better-auth-best-practices** (5.1K installs) - Authentication patterns

**Tools & Utilities (4 skills):**
- ✅ **find-skills** (40K installs) - Discover and install skills
- ✅ **skill-creator** (15K installs) - Create custom skills
- ✅ **brainstorming** (4.9K installs) - Creative problem solving
- ✅ **audit-website** (7.2K installs) - Website quality audit

**Installation Method:**
- Command: `npx skills add <owner/repo>`
- Installed to: `.agents/skills/`
- Format: SKILL.md (YAML frontmatter + Markdown)
- Compatible with Claude Code and other agents

**Configuration:**
```yaml
skills:
  sources:
    - name: "Skills.sh"
      url: "https://skills.sh/api/skills"
      type: "api"
  downloaded_dir: ".agents/skills"
```

**Usage:**
```bash
# List installed skills
npx skills list

# Search for skills
npx skills find [query]

# Add new skills
npx skills add <owner/repo>

# Update skills
npx skills update
```

**Documentation:**
- Skill list: `docs/INSTALLED_SKILLS.md`
- Configuration: `config.yaml`
- Marketplace: https://skills.sh/

---

# Alpha Builtin Skills - v0.3.1

## Update Date
2026-01-29

## Major Changes

### 1. Preinstalled Builtin Skills

**New Feature:**
3 commonly used skills are now preinstalled and ready to use immediately.

**Builtin Skills:**
- ✅ **text-processing** - Advanced text processing and transformation
  - 20+ operations: uppercase, lowercase, reverse, split, replace, extract emails/URLs/numbers, etc.
  - No dependencies, pure Python
  - Optimized for performance

- ✅ **json-processor** - JSON parsing, formatting, and transformation
  - 8 operations: parse, stringify, format, minify, validate, extract, merge, filter
  - Handle complex JSON with path-based extraction
  - Validation with detailed error messages

- ✅ **data-analyzer** - Statistical analysis and data aggregation
  - 17 operations: mean, median, mode, min, max, variance, stdev, percentile, etc.
  - Data operations: group_by, aggregate, sort, filter
  - Complete statistical summary

**Automatic Loading:**
- Skills are automatically preinstalled at startup
- No configuration required
- Shows loading progress: "Loading builtin skills... ✓ Loaded 3 builtin skills"
- Instant availability, no download needed

**Skill Registry:**
- Builtin skills registry at `alpha/skills/builtin/registry.json`
- SkillMarketplace automatically includes builtin skills
- Builtin skills have priority over remote skills

**Visual Feedback:**
- Added loading spinner for skill/tool execution
- Status display shows "Executing skill: {name}..." during execution
- Improved user experience with visual feedback

**Documentation:**
- ✅ `docs/BUILTIN_SKILLS.md` - Complete reference for all builtin skills
- Detailed operation descriptions and usage examples
- Troubleshooting guide

**Testing:**
- ✅ `tests/test_builtin_skills.py` - Comprehensive builtin skills test
- All 3 skills tested and verified
- 100% test pass rate

### 2. Preinstallation Mechanism

**Implementation:**
- New `preinstall_builtin_skills()` function in `alpha/skills/__init__.py`
- Automatically discovers and installs all builtin skills
- Integrated into CLI startup process
- No user interaction required

**Files Modified:**
- `alpha/skills/__init__.py` - Added preinstall function
- `alpha/skills/marketplace.py` - Added builtin skills support
- `alpha/interface/cli.py` - Integrated preinstallation

### 3. Enhanced User Experience

**Visual Improvements:**
- Loading progress indicator
- Success message with skill count
- Execution status spinner (from Status import)
- Clear visual feedback during operations

## Files Created

### Builtin Skills
- `alpha/skills/builtin/text-processing/skill.yaml` - Metadata
- `alpha/skills/builtin/text-processing/skill.py` - Implementation (150 lines)
- `alpha/skills/builtin/json-processor/skill.yaml` - Metadata
- `alpha/skills/builtin/json-processor/skill.py` - Implementation (180 lines)
- `alpha/skills/builtin/data-analyzer/skill.yaml` - Metadata
- `alpha/skills/builtin/data-analyzer/skill.py` - Implementation (250 lines)
- `alpha/skills/builtin/registry.json` - Builtin skills registry

### Documentation
- `docs/BUILTIN_SKILLS.md` - Complete builtin skills reference

### Testing
- `tests/test_builtin_skills.py` - Builtin skills test suite

## Testing

Run builtin skills tests:

```bash
source venv/bin/activate
python tests/test_builtin_skills.py
```

Expected output:
```
================================================================================
✓ ALL TESTS PASSED
================================================================================
Successfully preinstalled and tested 3 builtin skills
```

## Usage Examples

### Text Processing
```
You: Convert "hello world" to uppercase

Alpha: SKILL: text-processing
PARAMS:
  operation: "uppercase"
  text: "hello world"

Result: "HELLO WORLD"
```

### JSON Processing
```
You: Parse this JSON: {"name": "Alpha"}

Alpha: SKILL: json-processor
PARAMS:
  operation: "parse"
  json_str: '{"name": "Alpha"}'

Result: {name: "Alpha"}
```

### Data Analysis
```
You: Calculate average of [1, 2, 3, 4, 5]

Alpha: SKILL: data-analyzer
PARAMS:
  operation: "mean"
  data: [1, 2, 3, 4, 5]

Result: 3.0
```

## Benefits

1. **Instant Availability** - Skills ready immediately, no installation
2. **Offline Ready** - No internet required for builtin skills
3. **Fast Performance** - Optimized, no external dependencies
4. **Reliable** - Tested and maintained by Alpha team
5. **Common Use Cases** - Cover most text, JSON, and data operations

## Breaking Changes

None - fully backward compatible with v0.3.0

## Upgrade Instructions

No action required. Builtin skills will be automatically loaded on next start.

---

# Alpha Agent Skill System - v0.3.0

## Update Date
2026-01-29

## Major Changes

### 1. Agent Skill System - Dynamic Capability Expansion

**New Feature:**
Complete Agent Skill system implementation enabling dynamic discovery, installation, and execution of skills.

**Key Components:**
- ✅ **AgentSkill Base Class** - Abstract base for creating skills
- ✅ **SkillRegistry** - Manage installed skills and lifecycle
- ✅ **SkillMarketplace** - Discover and download skills from repositories
- ✅ **SkillInstaller** - Install skills and manage dependencies
- ✅ **SkillExecutor** - Execute skills with auto-install support

**Features:**
- 🔍 **Auto-Discovery** - Automatically find skills in marketplace
- 📦 **Auto-Installation** - Install skills on-demand when needed
- ♻️ **Reusable** - Skills can be used across different tasks
- 📚 **Versioned** - Support for skill versioning
- 🏪 **Marketplace** - Search and browse available skills
- 🧪 **Fully Tested** - Comprehensive test suite with 100% pass rate

**CLI Integration:**
- New `skills` command - List installed skills
- New `search skill <query>` command - Search for available skills
- Support for `SKILL:` directive in LLM responses
- Skills auto-install when referenced in conversations

**Example Usage:**
```
You: Convert "hello world" to uppercase

Alpha: I'll use the text-processing skill for this.

SKILL: text-processing
PARAMS:
  operation: "uppercase"
  text: "hello world"

Result: "HELLO WORLD"
```

**Example Skill Created:**
- ✅ `examples/skills/example-skill/` - Demonstrates skill structure
- Features text transformation capabilities
- Includes comprehensive documentation

**Documentation:**
- ✅ `docs/AGENT_SKILLS.md` - Complete technical documentation
- ✅ `docs/AGENT_SKILLS_QUICKSTART.md` - Quick start guide
- ✅ API reference and best practices
- ✅ Troubleshooting guide

**Testing:**
- ✅ `tests/test_agent_skills.py` - Comprehensive test suite
- All tests passing (20+ test cases)
- Tests cover: metadata, registry, installer, marketplace, executor

### 2. Enhanced System Prompt

**Updates:**
- Added Skills vs Tools distinction
- Explained auto-discovery and auto-install behavior
- Added SKILL: directive documentation
- Clarified when to use skills vs tools

### 3. Parser Enhancement

**Changes:**
- Extended `_parse_tool_calls()` to support SKILL: directive
- Extended `_extract_user_message()` to filter SKILL: lines
- Backward compatible with existing tool calls
- Support for mixed tool/skill calls in single response

### 4. CLI Enhancements

**New Features:**
- Skills system integration
- New commands for skill management
- Enhanced help text with skill information
- Skill execution with auto-install

## Architecture

### Skills vs Tools

| Feature | Tools | Skills |
|---------|-------|--------|
| Built-in | ✅ Yes | ❌ No |
| Dynamic Install | ❌ No | ✅ Yes |
| Versioning | ❌ No | ✅ Yes |
| Dependencies | ❌ No | ✅ Yes |
| Marketplace | ❌ No | ✅ Yes |
| Community Contributed | ❌ No | ✅ Yes |

### Skill Structure

```
skill-name/
├── skill.yaml        # Metadata (required)
├── skill.py          # Implementation (required)
├── README.md         # Documentation (optional)
└── requirements.txt  # Dependencies (optional)
```

## Breaking Changes

None - fully backward compatible with v0.2.0

## Upgrade Instructions

### From v0.2.0

No changes required. The skill system is automatically available and optional.

To enable auto-install (enabled by default):
```python
# In run_cli()
skill_executor = SkillExecutor(
    registry=skill_registry,
    marketplace=skill_marketplace,
    installer=skill_installer,
    auto_install=True  # Default
)
```

## Known Limitations

1. **Sandboxing** - Skills currently run without isolation (planned for v0.4.0)
2. **Permission System** - No fine-grained permissions yet (planned for v0.4.0)
3. **Marketplace UI** - CLI-only, no web interface (planned for v0.5.0)
4. **Repository Support** - Currently GitHub only (GitLab support planned)

## Future Roadmap

### v0.4.0 (Planned)
- 🔐 Sandboxed skill execution
- 🎯 Permission system for skills
- 📊 Skill usage analytics
- 🔗 Skill dependencies on other skills

### v0.5.0 (Planned)
- 🌐 Web-based skill marketplace
- 🏪 Skill ratings and reviews
- 📦 Skill packaging and distribution
- 🔄 Auto-update for skills

## Files Modified/Created

### New Files
- `alpha/skills/__init__.py` - Skill module initialization
- `alpha/skills/base.py` - Base classes and data structures
- `alpha/skills/registry.py` - Skill registry implementation
- `alpha/skills/marketplace.py` - Marketplace implementation
- `alpha/skills/installer.py` - Installer implementation
- `alpha/skills/executor.py` - Executor implementation
- `examples/skills/example-skill/` - Example skill
- `tests/test_agent_skills.py` - Test suite
- `docs/AGENT_SKILLS.md` - Technical documentation
- `docs/AGENT_SKILLS_QUICKSTART.md` - Quick start guide

### Modified Files
- `alpha/interface/cli.py` - Integrated skill system
  - Added skill_executor parameter
  - Enhanced system prompt with SKILL: support
  - Added skills and search skill commands
  - Extended parser for SKILL: directive
  - Modified execution flow for skills

## Testing

Run the skill system tests:

```bash
source venv/bin/activate
python tests/test_agent_skills.py
```

Expected output:
```
================================================================================
✓ ALL TESTS PASSED
================================================================================
```

## Contributors

- Alpha Development Team

---

# Alpha Enhancement - v0.2.0

## Update Date
2026-01-29

## Major Changes

### 1. Enhanced Tool Call Parser - Multi-Format Support

**Problem Fixed:**
- Users were seeing internal tool call details (TOOL: and PARAMS: lines) in responses
- LLM used multi-line YAML format that wasn't recognized by the parser

**Solution:**
- ✅ Enhanced `_parse_tool_calls()` to support both JSON and YAML formats
- ✅ Enhanced `_extract_user_message()` to filter multi-line PARAMS blocks
- ✅ Updated system prompt to clarify tool call lines are invisible to users

**Supported Formats:**
```python
# Single-line JSON (original)
PARAMS: {"url": "https://example.com", "method": "GET"}

# Multi-line YAML (new)
PARAMS:
  url: "https://example.com"
  method: "GET"

# Complex nested YAML (new)
PARAMS:
  headers:
    Content-Type: "application/json"
  json:
    query: "test"
```

**User Experience:**
- Before: Users saw raw `TOOL:` and `PARAMS:` lines
- After: Complete technical detail hiding, pure natural language interaction

### 2. Universal Tool Design Philosophy

**Removed:**
- Specialized WeatherTool (decided against dedicated tools for each scenario)

**Philosophy:**
- ✅ Use generic tools (HTTP, Search) to handle all scenarios
- ✅ LLM autonomously combines tools to solve problems
- ✅ No code changes needed for new use cases

**Tool Usage Guide:**
- Created `docs/TOOL_USAGE_GUIDE.md` with examples:
  - Weather queries: `HTTP + wttr.in API`
  - Stock market: `Search for latest data`
  - News: `Search with time filters`
  - Currency rates: `HTTP + exchange rate APIs`

### 3. System Prompt Enhancements

**Added:**
- Tool usage strategies (weather, real-time data, APIs)
- Format flexibility explanation (JSON/YAML)
- Critical reminder: tool calls are invisible to users

### 4. Testing Improvements

**New Tests:**
- ✅ `tests/test_parser.py` - Parser unit tests (4 scenarios)
- ✅ `tests/test_weather_http.py` - Weather API integration test
- ✅ All 25 comprehensive tests pass (100%)

**Test Coverage:**
- Single-line JSON parsing
- Multi-line YAML parsing
- Mixed format parsing
- Complex nested structure parsing

### 5. Documentation

**New Documents:**
- `docs/TOOL_USAGE_GUIDE.md` - Complete tool usage guide
- `docs/PARSER_ENHANCEMENT.md` - Parser enhancement details

## Bug Fixes

- Fixed `KeyError: 'city'` in system prompt formatting
- Fixed tool call visibility issue in CLI output
- Fixed `StopIteration` error in streaming response (Rich library bug in Python 3.12)
- Improved search tool timeout handling and error messages
- Added network connectivity fallback strategies

## Breaking Changes

None - fully backward compatible

---

# Alpha Configuration Update - v0.1.1

## Update Content

This update adds enhanced support for the Anthropic API, providing more flexible configuration options.

## Major Changes

### 1. Changed Default Provider to Anthropic

- ✅ Use `anthropic` as the default LLM provider
- ✅ Upgraded default model to `claude-3-5-sonnet-20241022`
- ✅ Increased maximum tokens to 8192

### 2. Added Environment Variable Support

**ANTHROPIC_AUTH_TOKEN** (Recommended)
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

**ANTHROPIC_API_KEY** (Compatible)
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

**ANTHROPIC_BASE_URL** (Optional)
```bash
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### 3. Environment Variable Fallback Mechanism

Configuration files now support environment variable fallback syntax:

```yaml
api_key: "${ANTHROPIC_AUTH_TOKEN:-${ANTHROPIC_API_KEY}}"
```

Resolution order:
1. Prioritize `ANTHROPIC_AUTH_TOKEN`
2. If not set, fallback to `ANTHROPIC_API_KEY`
3. If neither is set, return empty string

### 4. Base URL Support

AnthropicProvider now supports custom API endpoints:

```python
client = AsyncAnthropic(
    api_key=api_key,
    base_url=base_url  # If configured
)
```

This allows using:
- Self-hosted Anthropic-compatible API
- Enterprise internal proxy
- Testing environment endpoints

## Code Changes

### Modified Files

1. **config.example.yaml** & **config.yaml**
   - Changed default provider to anthropic
   - Added base_url configuration
   - Updated api_key with fallback syntax
   - Upgraded model and token limits

2. **alpha/utils/config.py**
   - Enhanced `_replace_env_vars()` function
   - Support for `${VAR1:-${VAR2}}` syntax
   - Support for `${VAR:-default}` syntax

3. **alpha/llm/service.py**
   - AnthropicProvider supports base_url parameter
   - Pass base_url in complete() and stream_complete()
   - from_config() method passes base_url to provider

### New Files

1. **docs/anthropic_config.md** - Complete Anthropic configuration guide
2. **tests/test_config.py** - Configuration loading tests
3. **start.sh** - Quick start script

## Usage Examples

### Quick Start

```bash
# Set API key
export ANTHROPIC_AUTH_TOKEN="sk-ant-..."

# Start Alpha
./start.sh
```

### Using Custom Endpoint

```bash
export ANTHROPIC_AUTH_TOKEN="your-token"
export ANTHROPIC_BASE_URL="https://api.your-company.com"
./start.sh
```

### Switching Back to OpenAI

Edit config.yaml:
```yaml
llm:
  default_provider: "openai"
```

Then set:
```bash
export OPENAI_API_KEY="sk-..."
./start.sh
```

## Testing

Run configuration tests:

```bash
source venv/bin/activate
PYTHONPATH=. python tests/test_config.py
```

Test coverage:
- ✅ Configuration file loading
- ✅ ANTHROPIC_AUTH_TOKEN parsing
- ✅ Fallback to ANTHROPIC_API_KEY
- ✅ Base URL configuration
- ✅ Model and parameter validation

## Backward Compatibility

This update is fully backward compatible:
- ✅ Still supports `ANTHROPIC_API_KEY`
- ✅ OpenAI configuration unaffected
- ✅ Existing configuration files remain valid

If `ANTHROPIC_API_KEY` is already set, no changes are needed - the system will use it automatically.

## Upgrade Steps

### Upgrading from v0.1.0

1. Update configuration file:
```bash
cp config.yaml config.yaml.bak
cp config.example.yaml config.yaml
# Adjust configuration as needed
```

2. Set environment variables:
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

3. Test configuration:
```bash
PYTHONPATH=. python tests/test_config.py
```

4. Start Alpha:
```bash
./start.sh
```

## Documentation Updates

- ✅ README.md - Updated installation instructions
- ✅ docs/quickstart.md - Updated configuration steps
- ✅ docs/anthropic_config.md - New complete configuration guide
- ✅ Updated code comments

## Next Steps

Recommended future features:
- [ ] Support more environment variables (timeout, retry, etc.)
- [ ] Add configuration validation command
- [ ] Support configuration hot reload
- [ ] Add multi-profile support

---

**Version**: v0.1.1
**Release Date**: 2026-01-29
**Change Type**: Feature Enhancement
**Backward Compatible**: Yes

---

# <a name="中文"></a>简体中文

# Alpha Configuration Update - v0.1.1

## 更新内容

本次更新增加了对Anthropic API的增强支持,提供更灵活的配置方式。

## 主要变更

### 1. 默认Provider改为Anthropic

- ✅ 默认使用 `anthropic` 作为LLM provider
- ✅ 默认模型升级为 `claude-3-5-sonnet-20241022`
- ✅ 最大token数提升至 8192

### 2. 新增环境变量支持

**ANTHROPIC_AUTH_TOKEN** (推荐)
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

**ANTHROPIC_API_KEY** (兼容)
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

**ANTHROPIC_BASE_URL** (可选)
```bash
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### 3. 环境变量Fallback机制

配置文件现在支持环境变量fallback语法:

```yaml
api_key: "${ANTHROPIC_AUTH_TOKEN:-${ANTHROPIC_API_KEY}}"
```

解析顺序:
1. 优先使用 `ANTHROPIC_AUTH_TOKEN`
2. 如果未设置,fallback到 `ANTHROPIC_API_KEY`
3. 如果都未设置,返回空字符串

### 4. Base URL支持

AnthropicProvider现在支持自定义API端点:

```python
client = AsyncAnthropic(
    api_key=api_key,
    base_url=base_url  # 如果设置的话
)
```

这允许使用:
- 自建Anthropic兼容API
- 企业内部代理
- 测试环境端点

## 代码变更

### 修改的文件

1. **config.example.yaml** & **config.yaml**
   - 默认provider改为anthropic
   - 添加base_url配置
   - 更新api_key为fallback语法
   - 升级模型和token限制

2. **alpha/utils/config.py**
   - 增强`_replace_env_vars()`函数
   - 支持`${VAR1:-${VAR2}}`语法
   - 支持`${VAR:-default}`语法

3. **alpha/llm/service.py**
   - AnthropicProvider支持base_url参数
   - 在complete()和stream_complete()中传递base_url
   - from_config()方法传递base_url到provider

### 新增文件

1. **docs/anthropic_config.md** - Anthropic配置完整指南
2. **tests/test_config.py** - 配置加载测试
3. **start.sh** - 快速启动脚本

## 使用示例

### 快速开始

```bash
# 设置API密钥
export ANTHROPIC_AUTH_TOKEN="sk-ant-..."

# 启动Alpha
./start.sh
```

### 使用自定义端点

```bash
export ANTHROPIC_AUTH_TOKEN="your-token"
export ANTHROPIC_BASE_URL="https://api.your-company.com"
./start.sh
```

### 切换回OpenAI

编辑config.yaml:
```yaml
llm:
  default_provider: "openai"
```

然后设置:
```bash
export OPENAI_API_KEY="sk-..."
./start.sh
```

## 测试

运行配置测试:

```bash
source venv/bin/activate
PYTHONPATH=. python tests/test_config.py
```

测试覆盖:
- ✅ 配置文件加载
- ✅ ANTHROPIC_AUTH_TOKEN解析
- ✅ Fallback到ANTHROPIC_API_KEY
- ✅ Base URL设置
- ✅ 模型和参数验证

## 向后兼容

本次更新完全向后兼容:
- ✅ 仍然支持 `ANTHROPIC_API_KEY`
- ✅ OpenAI配置不受影响
- ✅ 现有配置文件仍然有效

如果已经设置了`ANTHROPIC_API_KEY`,无需修改,系统会自动使用。

## 升级步骤

### 从v0.1.0升级

1. 更新配置文件:
```bash
cp config.yaml config.yaml.bak
cp config.example.yaml config.yaml
# 根据需要调整配置
```

2. 设置环境变量:
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key"
```

3. 测试配置:
```bash
PYTHONPATH=. python tests/test_config.py
```

4. 启动Alpha:
```bash
./start.sh
```

## 文档更新

- ✅ README.md - 更新安装说明
- ✅ docs/quickstart.md - 更新配置步骤
- ✅ docs/anthropic_config.md - 新增完整配置指南
- ✅ 代码注释更新

## 下一步

建议后续功能:
- [ ] 支持更多环境变量(超时、重试等)
- [ ] 添加配置验证命令
- [ ] 支持配置文件热加载
- [ ] 添加多profile支持

---

**版本**: v0.1.1
**发布日期**: 2026-01-29
**变更类型**: Feature Enhancement
**向后兼容**: Yes
