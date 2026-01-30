## Alpha Agent Benchmark Testing Framework

Industry-standard benchmark testing framework for evaluating Alpha's capabilities across different task complexity levels.

### Overview

This benchmark framework implements comprehensive evaluation inspired by leading AI agent benchmarks:
- **AgentBench**: Multi-environment agent evaluation
- **GAIA**: Complexity-stratified general assistant benchmarking
- **τ-Bench**: Real-world task evaluation
- **SWE-bench**: Software engineering task benchmarking

### Quick Start

```bash
# Run all benchmarks
python -m tests.benchmarks.run_benchmarks

# Run specific complexity level
python -m tests.benchmarks.run_benchmarks --level level_1_simple

# Run specific category
python -m tests.benchmarks.run_benchmarks --category file_system

# Run in parallel (faster)
python -m tests.benchmarks.run_benchmarks --parallel --max-tasks 10

# Generate specific format
python -m tests.benchmarks.run_benchmarks --format markdown
```

### Complexity Levels

#### Level 1 - Simple Tasks
- **Steps**: 1-2 steps
- **Tools**: 1-2 tool uses
- **Reasoning**: Minimal
- **Target Success**: ≥95%
- **Target Time**: ≤1 second
- **Examples**: File operations, simple calculations, basic queries

#### Level 2 - Medium Tasks
- **Steps**: 3-5 steps
- **Tools**: 3-5 tool uses
- **Reasoning**: Moderate
- **Target Success**: ≥85%
- **Target Time**: ≤10 seconds
- **Examples**: Multi-file operations, data processing pipelines, API integrations

#### Level 3 - Complex Tasks
- **Steps**: 6-10 steps
- **Tools**: 6-10 tool uses
- **Reasoning**: Advanced
- **Target Success**: ≥70%
- **Target Time**: ≤60 seconds
- **Examples**: Code generation with tests, complex data analysis, multi-API orchestration

#### Level 4 - Expert Tasks
- **Steps**: 10+ steps
- **Tools**: 10+ tool uses
- **Reasoning**: Deep, adaptive replanning
- **Target Success**: ≥50%
- **Target Time**: ≤300 seconds
- **Examples**: End-to-end feature development, complex debugging, system integration

### Task Categories

1. **File & System Management**: File operations, directory management, shell commands
2. **Data Processing & Analysis**: JSON/CSV processing, calculations, transformations
3. **Web & API Interactions**: HTTP requests, API integrations, error handling
4. **Information Retrieval**: Web search, data extraction, summarization
5. **Code Generation & Execution**: Script writing, code execution, debugging
6. **Task Scheduling & Automation**: Cron jobs, workflows, dependencies
7. **Agent Skills Integration**: Skill discovery, installation, execution
8. **Multi-Model Selection**: Automatic model routing based on task complexity

### Evaluation Dimensions

The framework evaluates Alpha across multiple dimensions:

1. **Task Completion Success Rate**: Percentage of successfully completed tasks
2. **Reasoning & Planning Capability**: Quality of multi-step reasoning
3. **Tool Use Proficiency**: Accuracy in tool selection and usage
4. **Cost-Performance Optimization**: API costs vs. quality trade-offs
5. **Response Latency**: Time from task input to completion
6. **Error Recovery & Resilience**: Ability to handle failures ("never give up")
7. **Multi-Step Task Consistency**: Context maintenance across long tasks

### Performance Metrics

**Overall Benchmark Score** (0-100): Weighted composite score
- Success Rate: 35%
- Performance (Time): 25%
- Cost Efficiency: 15%
- Tool Usage: 15%
- Resilience: 10%

### Report Formats

#### Console Output
Formatted summary printed to terminal with key metrics and insights.

#### JSON Report
Machine-readable structured data saved to `tests/benchmarks/reports/benchmark_report.json`:
```json
{
  "overall_score": {"composite_score": 85.3, ...},
  "complexity_breakdown": {...},
  "category_breakdown": {...},
  "detailed_results": [...]
}
```

#### Markdown Report
Human-readable report saved to `tests/benchmarks/reports/benchmark_report.md`:
- Executive summary
- Dimension scores
- Complexity/category breakdowns
- Detailed task results
- Analysis and recommendations

### Creating Custom Scenarios

```python
from tests.benchmarks import TaskBuilder, TaskComplexity, TaskCategory

task = TaskBuilder()
    .with_name("Custom Task")
    .with_description("Description of what to do")
    .with_complexity(TaskComplexity.LEVEL_2_MEDIUM)
    .with_category(TaskCategory.FILE_SYSTEM)
    .with_input({"key": "value"})
    .with_expected_output("Expected result")
    .build()
```

### Integration with CI/CD

```bash
# Run benchmarks and fail if score < 60
python -m tests.benchmarks.run_benchmarks || exit 1

# Generate report for artifacts
python -m tests.benchmarks.run_benchmarks --format json
```

### Best Practices

1. **Run regularly**: Execute benchmarks after major changes
2. **Track trends**: Compare scores across versions
3. **Focus improvements**: Use weaknesses/recommendations to guide development
4. **Set thresholds**: Define minimum acceptable scores for CI/CD
5. **Category testing**: Test specific categories during focused development

### Troubleshooting

**ImportError: No module named 'alpha'**
```bash
# Make sure you're in the project root
cd /path/to/agents-889b8e6452
python -m tests.benchmarks.run_benchmarks
```

**Tasks timing out**
```bash
# Increase timeout multiplier in code or run fewer parallel tasks
python -m tests.benchmarks.run_benchmarks --max-tasks 3
```

**Low scores**
- Review detailed task results in the report
- Check execution logs for errors
- Focus on categories with lowest performance
- Implement recommendations from the analysis

### Architecture

```
tests/benchmarks/
├── __init__.py           # Package exports
├── framework.py          # Core framework & evaluation dimensions
├── tasks.py              # Task definitions & results
├── metrics.py            # Performance metrics & scoring
├── reporter.py           # Report generation (JSON/MD/Console)
├── runner.py             # Automated test execution
├── run_benchmarks.py     # Main CLI entry point
├── scenarios/            # Test scenario definitions
│   └── __init__.py       # All complexity level scenarios
└── reports/              # Generated reports (git-ignored)
    ├── benchmark_report.json
    └── benchmark_report.md
```

### Contributing

To add new benchmark scenarios:

1. Edit `tests/benchmarks/scenarios/__init__.py`
2. Add tasks to appropriate complexity level function
3. Use TaskBuilder for consistent task creation
4. Include validation functions for expected outputs
5. Run benchmarks to verify new scenarios work

### References

- [AgentBench Paper](https://arxiv.org/abs/2308.03688)
- [GAIA Benchmark](https://arxiv.org/abs/2311.12983)
- [τ-Bench](https://sierra.ai/blog/benchmarking-ai-agents)
- [SWE-bench](https://www.swebench.com/)
